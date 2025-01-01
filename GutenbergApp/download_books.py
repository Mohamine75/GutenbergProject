import os
import sys
import django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Définissez le chemin vers le fichier settings.py de votre projet Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GutenbergProject.settings')

# Initialisez Django
django.setup()
from gutenbergpy.gutenbergcache import GutenbergCache

from gutenbergpy.textget import get_text_by_id
from gutenbergpy.gutenbergcache import GutenbergCache
from GutenbergApp.models import Book  # Remplacez par votre application
from django.db import transaction

# Dossier temporaire pour sauvegarder les livres
BOOK_DIR = "books"
if not os.path.exists(BOOK_DIR):
    os.makedirs(BOOK_DIR)
from gutenbergpy.gutenbergcache import GutenbergCache


def initialize_cache():
    """Initialise le cache SQLite de gutenbergpy."""
    cache = GutenbergCache.get_cache()

    # Vérifier si le cache est déjà disponible
    if not GutenbergCache.exists() or not cache:
        print("Le cache n'est pas disponible. Initialisation en cours...")
        GutenbergCache.create()
        print("Cache créé avec succès.")
    else:
        print("Le cache est déjà disponible et prêt à être utilisé.")

    return cache
def has_min_words(text, min_words=10000):
    """Vérifie si le texte contient au moins un certain nombre de mots."""
    return len(text.split()) >= min_words

def save_to_database(gutenberg_id, title, author, content):
    """Enregistre un livre dans la base de données Django."""
    with transaction.atomic():
        Book.objects.create(
            gutenberg_id=gutenberg_id,
            title=title or "Unknown Title",
            author=author or "Unknown Author",
            content=content,
        )

def download_books(min_books=1664, min_words=10000):
    """Télécharge et sauvegarde les livres uniquement avec gutenbergpy."""
    cache = initialize_cache()

    downloaded = 0

    # Parcourir les livres disponibles dans le cache
    for book in cache.get_metadata('type', 'Text'):
        try:
            gutenberg_id = book['id']
            title = book['title']
            author = book.get('creator', None)  # `creator` pour auteur
            language = book.get('language', ['en'])[0]

            # Limite aux livres en anglais
            if language != 'en':
                continue

            # Télécharger le texte complet
            raw_text = get_text_by_id(gutenberg_id).decode('utf-8')

            # Vérification du nombre de mots
            if not has_min_words(raw_text, min_words):
                continue

            # Sauvegarder localement
            file_path = os.path.join(BOOK_DIR, f"{gutenberg_id}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(raw_text)

            # Sauvegarder dans la base de données
            save_to_database(
                gutenberg_id=gutenberg_id,
                title=title,
                author=author,
                content=raw_text,
            )

            downloaded += 1
            print(f"Livre {downloaded}/{min_books} téléchargé : {title}")

            if downloaded >= min_books:
                print("Téléchargement terminé.")
                break
        except Exception as e:
            print(f"Erreur pour le livre ID {book['id']}: {e}")

if __name__ == "__main__":
    download_books()
