import os
import xml.etree.ElementTree as ET
from gutenbergpy.textget import get_text_by_id
import sqlite3


# Étape 1 : Extraire les métadonnées du fichier RDF
def extract_rdf_data(rdf_file, folder_name):
    """Extrait les informations du fichier RDF en utilisant le nom du dossier comme ID."""
    try:
        tree = ET.parse(rdf_file)
        root = tree.getroot()

        # Espace de noms RDF
        namespaces = {
            'dcterms': 'http://purl.org/dc/terms/',
            'pgterms': 'http://www.gutenberg.org/2009/pgterms/',
        }

        # Utiliser le nom du dossier comme ID du livre
        book_id = int(folder_name)  # Le nom du dossier est l'ID du livre

        # Titre du livre
        title = root.find(".//dcterms:title", namespaces)
        title_text = title.text if title is not None else "Titre inconnu"

        # Auteur
        author = root.find(".//pgterms:agent/pgterms:name", namespaces)
        author_name = author.text if author is not None else "Auteur inconnu"

        return book_id, title_text, author_name
    except Exception as e:
        print(f"Erreur lors de l'analyse du fichier RDF {rdf_file} : {e}")
        return None


# Étape 2 : Télécharger le contenu du livre
def download_book_content(book_id, max_words=10000):
    """Télécharge le contenu du livre et le limite à un certain nombre de mots."""
    try:
        # Télécharger le texte brut
        text = get_text_by_id(book_id).decode('utf-8')

        # Limiter à max_words mots
        words = text.split()
        truncated_text = ' '.join(words[:max_words])
        return truncated_text
    except Exception as e:
        print(f"Erreur lors du téléchargement du livre ID {book_id} : {e}")
        return None

# Étape 3 : Initialiser la base de données SQLite
def initialize_database(db_name="books.db"):
    """Initialise une base de données SQLite avec une table pour les livres."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Créer la table books
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY,
        title TEXT,
        author TEXT,
        content TEXT
    )
    """)
    conn.commit()
    return conn


# Étape 4 : Insérer les données dans la base de données
def insert_book(conn, book_id, title, author, content):
    """Insère un livre dans la base de données."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO books (id, title, author, content)
        VALUES (?, ?, ?, ?)
        """, (book_id, title, author, content))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Le livre ID {book_id} existe déjà dans la base de données.")


# Étape 5 : Parcourir les sous-dossiers et traiter les fichiers RDF
def process_rdf_files(rdf_root_dir, db_name="books.db"):
    """Traite tous les fichiers RDF dans les sous-dossiers (1 à 1665) et insère les données dans la base."""
    conn = initialize_database(db_name)

    # Parcourir les dossiers de 1 à 1665
    for folder_number in range(1, 1666):  # 1665 inclus
        subdir_path = os.path.join(rdf_root_dir, str(folder_number))
        if os.path.isdir(subdir_path):
            # Rechercher un fichier RDF dans le sous-dossier
            rdf_file = next((f for f in os.listdir(subdir_path) if f.endswith(".rdf")), None)
            if rdf_file:
                rdf_path = os.path.join(subdir_path, rdf_file)

                # Extraire les métadonnées en utilisant le numéro du dossier comme ID
                data = extract_rdf_data(rdf_path, str(folder_number))
                if data is None:
                    continue

                book_id, title, author = data
                print(f"Traitement du livre ID {book_id} : {title} par {author}")

                # Télécharger et limiter le contenu à 10 000 mots
                content = download_book_content(book_id, max_words=10000)
                if content is None:
                    continue

                # Insérer dans la base de données
                insert_book(conn, book_id, title, author, content)

    conn.close()
    print("Traitement terminé.")

# Étape 6 : Exécuter le script
if __name__ == "__main__":
    # Répertoire contenant les sous-dossiers avec les fichiers RDF
    rdf_root_dir = "books"
    process_rdf_files(rdf_root_dir)
