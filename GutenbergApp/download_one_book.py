import os
import django
import sys
from gutenbergpy.textget import get_text_by_id


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GutenbergProject.settings')
django.setup()

from gutenbergpy.gutenbergcache import GutenbergCache
from GutenbergApp.models import Book



def load_one_book(gutenberg_id):
    """Télécharge un livre du Projet Gutenberg et l'ajoute à la base de données."""
    try:
        # Télécharger le contenu du livre
        raw_text = get_text_by_id(gutenberg_id).decode('utf-8')

        # Métadonnées fictives pour simplifier
        title = f"Livre {gutenberg_id}"
        author = "Auteur Inconnu"

        # Sauvegarder dans la base de données
        book, created = Book.objects.get_or_create(
            gutenberg_id=gutenberg_id,
            defaults={'title': title, 'author': author, 'content': raw_text},
        )

        if created:
            print(f"Livre {title} (ID {gutenberg_id}) ajouté à la base de données.")
        else:
            print(f"Livre {title} (ID {gutenberg_id}) existe déjà dans la base de données.")
    except Exception as e:
        print(f"Erreur lors du téléchargement ou de l'insertion du livre ID {gutenberg_id}: {e}")

if __name__ == "__main__":
    # Remplacez l'ID par celui d'un livre disponible sur le Projet Gutenberg
    load_one_book(1342)  # Exemple : "Pride and Prejudice"
