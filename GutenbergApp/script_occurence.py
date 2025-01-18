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
        book_id INTEGER,
        word TEXT,
        occurrences INTEGER,
        PRIMARY KEY (book_id, word)
    )
    """)
    conn.commit()
    return conn

# Étape 2 : Charger la liste de mots interdits
def load_banwords():
    """Retourne une liste de mots à ignorer en utilisant NLTK."""
    return set(stopwords.words('english'))  # Liste des stop words en anglais

# Étape 3 : Compter les mots dans un texte
def count_words(text, banwords):
    """Compte les occurrences des mots dans un texte, en ignorant les mots interdits."""
    # Nettoyer le texte (enlever la ponctuation et convertir en minuscule)
    words = re.findall(r'\b\w+\b', text.lower())
    filtered_words = [word.strip() for word in words if word not in banwords and not (word.isdigit()) and len(word) > 2]
    return Counter(filtered_words)

# Étape 4 : Remplir la table word_count
def populate_word_count_table(conn, banwords):
    """Parcourt les livres et remplit la table word_count."""
    cursor = conn.cursor()

    # Vider la table word_count
    print("Nettoyage de la table word_count...")
    cursor.execute("DELETE FROM word_count")

    # Charger les livres depuis la table books
    cursor.execute("SELECT id, content FROM books")
    books = cursor.fetchall()

    for book_id, content in books:
        print(f"Traitement du livre ID : {book_id}")

        # Compter les mots
        word_counts = count_words(content, banwords)

        # Insérer ou mettre à jour les données dans la table word_count
        for word, occurrences in word_counts.items():
            cursor.execute("""
            INSERT OR REPLACE INTO word_count (book_id, word, occurrences)
            VALUES (?, ?, ?)
            """, (book_id, word, occurrences))

    conn.commit()

# Étape 5 : Script principal
if __name__ == "__main__":
    db_name = os.path.join("./", "db.sqlite3")
    conn = initialize_word_count_table(db_name)

    # Charger les mots interdits
    banwords = load_banwords()

    # Remplir la table avec les mots comptés par livre
    populate_word_count_table(conn, banwords)

    conn.close()
    print("Traitement terminé.")
