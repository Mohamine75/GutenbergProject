import sqlite3
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
import os

# Télécharger les stop words au premier démarrage
nltk.download('stopwords')

# Étape 1 : Initialiser la base de données
def initialize_word_count_table(db_name):
    """Crée une table pour stocker les mots comptés."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Créer la table `word_count` si elle n'existe pas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS word_count (
        book_title TEXT,
        word TEXT,
        occurrences INTEGER,
        PRIMARY KEY (book_title, word)
    )
    """)
    conn.commit()
    return conn

def verify_table_exists(conn):
    """Vérifie si la table `word_count` existe dans la base de données."""
    cursor = conn.cursor()
    cursor.execute("""
    SELECT name FROM sqlite_master WHERE type='table' AND name='word_count';
    """)
    table = cursor.fetchone()
    if table:
        print("La table `word_count` existe.")
    else:
        print("Erreur : La table `word_count` n'a pas été créée.")

# Étape 2 : Charger la liste de mots interdits
def load_banwords():
    """Retourne une liste de mots à ignorer en utilisant NLTK."""
    return set(stopwords.words('english'))  # Liste des stop words en anglais


# Étape 3 : Compter les mots dans un texte
def count_words(text, banwords):
    """Compte les occurrences des mots dans un texte, en ignorant les mots interdits."""
    # Nettoyer le texte (enlever la ponctuation et convertir en minuscule)
    words = re.findall(r'\b\w+\b', text.lower())
    filtered_words = [word for word in words if word not in banwords]
    return Counter(filtered_words)


# Étape 4 : Remplir la table word_count
def populate_word_count_table(conn, banwords):
    """Parcourt les livres et remplit la table word_count."""
    cursor = conn.cursor()

    # Charger les livres depuis la table books
    cursor.execute("SELECT title, content FROM books")
    books = cursor.fetchall()

    for book_title, content in books:
        print(f"Traitement du livre : {book_title}")

        # Compter les mots
        word_counts = count_words(content, banwords)

        # Insérer les données dans la table word_count
        for word, occurrences in word_counts.items():
            cursor.execute("""
            INSERT OR IGNORE INTO word_count (book_title, word, occurrences)
            VALUES (?, ?, ?)
            """, (book_title, word, occurrences))

    conn.commit()


# Étape 5 : Script principal
if __name__ == "__main__":
    db_name = os.path.join("E:/Daar/GutenbergProject", "db.sqlite3")
    conn = initialize_word_count_table(db_name)
    verify_table_exists(conn)  # Vérifie si la table existe
    banwords = load_banwords()
    populate_word_count_table(conn, banwords)
    conn.close()

