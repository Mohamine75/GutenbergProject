import os
import sqlite3
import xml.etree.ElementTree as ET
from gutenbergpy.textget import get_text_by_id, strip_headers


def extract_rdf_data(rdf_file, folder_name):
    """Extrait les informations RDF pour un livre."""
    try:
        tree = ET.parse(rdf_file)
        root = tree.getroot()

        namespaces = {
            'dcterms': 'http://purl.org/dc/terms/',
            'pgterms': 'http://www.gutenberg.org/2009/pgterms/',
        }

        book_id = int(folder_name)
        title = root.find(".//dcterms:title", namespaces)
        title_text = title.text if title is not None else "Titre inconnu"

        author = root.find(".//pgterms:agent/pgterms:name", namespaces)
        author_name = author.text if author is not None else "Auteur inconnu"

        return book_id, title_text, author_name
    except Exception as e:
        print(f"Erreur lors de l'analyse du fichier RDF {rdf_file} : {e}")
        return None


def initialize_database(db_name="books.db"):
    """Initialise la base de données SQLite avec la table 'books'."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Créer la table books si elle n'existe pas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY,
        title TEXT UNIQUE,
        author TEXT,
        content TEXT UNIQUE,
        cover_path TEXT
    )
    """)
    conn.commit()
    conn.close()




def download_book_content(book_id, max_words=10000):
    """Télécharge et nettoie le contenu d'un livre."""
    try:
        raw_book = get_text_by_id(book_id)
        clean_book = strip_headers(raw_book)
        text = clean_book.decode("utf-8").strip()
        
        # Chercher la fin du livre (différentes variantes possibles)
        end_markers = [
            "*** END OF THE PROJECT GUTENBERG EBOOK",
            "*** END OF THIS PROJECT GUTENBERG EBOOK",
            "***END OF THE PROJECT GUTENBERG EBOOK",
            "End of the Project Gutenberg EBook",
            "End of Project Gutenberg's"
        ]
        
        # Trouver la première occurrence d'un marqueur de fin
        end_index = len(text)
        for marker in end_markers:
            pos = text.find(marker)
            if pos != -1 and pos < end_index:
                end_index = pos
        
        # Tronquer le texte à la marque de fin
        text = text[:end_index].strip()
        
        # Limiter le nombre de mots si nécessaire
        words = text.split()
        truncated_text = ' '.join(words[:max_words])
        return truncated_text
    except Exception as e:
        print(f"Erreur lors du téléchargement du livre ID {book_id} : {e}")
        return None


def insert_or_update_book_with_image_path(conn, book_id, title, author, content, cover_path=None):
    """Insère ou met à jour un livre avec un chemin d'image dans la base de données."""
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM books WHERE id = ?", (book_id,))
        book_exists = cursor.fetchone()

        if book_exists:
            cursor.execute("""
            UPDATE books
            SET title = ?, author = ?, content = ?, cover_path = ?
            WHERE id = ?
            """, (title, author, content, cover_path, book_id))
        else:
            cursor.execute("""
            INSERT INTO books (id, title, author, content, cover_path)
            VALUES (?, ?, ?, ?, ?)
            """, (book_id, title, author, content, cover_path))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erreur lors de l'insertion ou de la mise à jour : {e}")



def is_valid_book_content(content):
    """Vérifie si le contenu du livre est valide selon nos critères."""
    if not content:
        return False
        
    # Vérifier si le livre commence par le texte non désiré
    unwanted_start = "501(c)(3)"
    return not content.strip().contains(unwanted_start)

def process_rdf_files(rdf_root_dir, covers_dir="covers", db_name="books.db"):
    """Traite les fichiers RDF et insère les données dans la base."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Vider la table word_count
    print("Nettoyage de la table books...")
    cursor.execute("DELETE FROM books")
    
    total_books = 0
    skipped_books = 0

    for folder_number in range(1, 603):  # 1 à 1665 inclus
        subdir_path = os.path.join(rdf_root_dir, str(folder_number))
        if os.path.isdir(subdir_path):
            rdf_file = next((f for f in os.listdir(subdir_path) if f.endswith(".rdf")), None)
            if rdf_file:
                rdf_path = os.path.join(subdir_path, rdf_file)
                data = extract_rdf_data(rdf_path, str(folder_number))
                if data:
                    book_id, title, author = data
                    content = download_book_content(book_id, max_words=10000)
                    
                    if content and is_valid_book_content(content):
                        print(f"Traitement du livre ID {book_id} : {title} par {author}")
                        cover_path = os.path.join(covers_dir, f"{book_id}.jpg")
                        if not os.path.exists(cover_path):
                            cover_path = None  # Si la couverture est absente
                        insert_or_update_book_with_image_path(conn, book_id, title, author, content, cover_path)
                        total_books += 1
                    else:
                        print(f"Livre ignoré ID {book_id} : {title} (contenu non valide)")
                        skipped_books += 1

    print(f"\nTraitement terminé.")
    print(f"Total des livres traités avec succès : {total_books}")
    print(f"Livres ignorés : {skipped_books}")

    conn.close()



def detect_and_remove_duplicates(db_name):
    """Détecte et supprime les doublons dans la table books."""
    print("\nRecherche et suppression des doublons...")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title FROM books")
    books = cursor.fetchall()
    
    # Préparer un dictionnaire avec les titres normalisés comme clés
    normalized_titles = {}
    for book_id, title in books:
        normalized = ' '.join(title.lower().replace(',', ' ').replace('.', ' ').split())
        if normalized in normalized_titles:
            normalized_titles[normalized].append((book_id, title))
        else:
            normalized_titles[normalized] = [(book_id, title)]
    
    # Supprimer les doublons
    duplicates_found = False
    for normalized, book_list in normalized_titles.items():
        if len(book_list) > 1:
            duplicates_found = True
            print("\nDoublons détectés:")
            
            # Trier par ID et garder le plus petit (le plus ancien)
            book_list.sort(key=lambda x: x[0])
            kept_book = book_list[0]
            books_to_delete = book_list[1:]
            
            print(f"Conservé: ID {kept_book[0]} - {kept_book[1]}")
            print("Supprimés:")
            
            for book_id, title in books_to_delete:
                print(f"ID {book_id} - {title}")
                cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    
    if duplicates_found:
        conn.commit()
        print("\nSuppression des doublons terminée.")
    else:
        print("Aucun doublon trouvé.")
    
    conn.close()

if __name__ == "__main__":
    rdf_root_dir = "books"  # Répertoire contenant les fichiers RDF
    db_name = "db.sqlite3"

    # Initialiser la base de données
    initialize_database(db_name)

    # Traiter les fichiers RDF
    process_rdf_files(rdf_root_dir, covers_dir="covers", db_name=db_name)
    
    # Détecter et supprimer les doublons
    detect_and_remove_duplicates(db_name)