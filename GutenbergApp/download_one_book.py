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


def download_book_content(book_id, max_words=10000):
    """Télécharge et nettoie le contenu d'un livre."""
    try:
        raw_book = get_text_by_id(book_id)
        clean_book = strip_headers(raw_book)
        text = clean_book.decode("utf-8").strip()
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


def process_rdf_files(rdf_root_dir, covers_dir="covers", db_name="books.db"):
    """Traite les fichiers RDF et insère les données dans la base."""
    conn = sqlite3.connect(db_name)

    for folder_number in range(1, 600):  # 1 à 1665 inclus
        subdir_path = os.path.join(rdf_root_dir, str(folder_number))
        if os.path.isdir(subdir_path):
            rdf_file = next((f for f in os.listdir(subdir_path) if f.endswith(".rdf")), None)
            if rdf_file:
                rdf_path = os.path.join(subdir_path, rdf_file)
                data = extract_rdf_data(rdf_path, str(folder_number))
                if data:
                    book_id, title, author = data
                    print(f"Traitement du livre ID {book_id} : {title} par {author}")

                    content = download_book_content(book_id, max_words=10000)
                    if content:
                        cover_path = os.path.join(covers_dir, f"{book_id}.jpg")
                        if not os.path.exists(cover_path):
                            cover_path = None  # Si la couverture est absente
                        insert_or_update_book_with_image_path(conn, book_id, title, author, content, cover_path)

    conn.close()
    print("Traitement terminé.")


if __name__ == "__main__":
    rdf_root_dir = "books"  # Répertoire contenant les fichiers RDF
    process_rdf_files(rdf_root_dir, covers_dir="covers", db_name="db.sqlite3")
