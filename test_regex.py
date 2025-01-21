import sqlite3
import re
from typing import List, Tuple
from termcolor import colored
import time
from collections import Counter

def get_word_frequency(cursor, words) -> dict:
    if not words:
        return {}
    
    placeholders = ','.join(['?' for _ in words])
    cursor.execute(f"""
        SELECT word, SUM(occurrences) as total_occurrences
        FROM word_count
        WHERE word IN ({placeholders})
        GROUP BY word
        ORDER BY total_occurrences DESC
        LIMIT 5
    """, words)
    return {row[0]: row[1] for row in cursor.fetchall()}

def test_regex_patterns(db_path: str = 'db.sqlite3') -> None:
    # Patterns plus rares et plus spécifiques à tester
    test_patterns = [
        ("z.*a", "Mots commençant par 'z' et finissant par 'a' (rare)"),
        ("qu.*x", "Mots commençant par 'qu' et finissant par 'x' (rare)"),
        (".*ology", "Mots finissant par 'ology' (termes scientifiques)"),
        ("xeno.*", "Mots commençant par 'xeno' (très rare)"),
        ("crypto.*y", "Mots commençant par 'crypto' et finissant par 'y'"),
        ("micro.*ic", "Mots commençant par 'micro' et finissant par 'ic'"),
        (".*graph.*y", "Mots contenant 'graph' et finissant par 'y'"),
        ("psych.*ist", "Mots commençant par 'psych' et finissant par 'ist'"),
        (".*ops", "Mots finissant par 'ops'"),
        ("(sea|sun)$", "sea ou sun")
    ]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(colored("\n=== Test de patterns regex rares ===\n", 'yellow', attrs=['bold']))

    # Récupérer le nombre total de livres pour le contexte
    cursor.execute("SELECT COUNT(DISTINCT id) FROM books")
    total_books = cursor.fetchone()[0]
    print(colored(f"Nombre total de livres dans la base: {total_books}\n", 'green'))

    for pattern, description in test_patterns:
        print(colored(f"Pattern: {pattern}", 'cyan'))
        print(f"Description: {description}")

        # Récupérer tous les mots distincts
        cursor.execute("SELECT DISTINCT word FROM word_count")
        all_words = [row[0] for row in cursor.fetchall()]

        # Convertir le pattern en regex Python
        py_pattern = pattern.replace("*", ".*")
        py_regex = re.compile(f"^{py_pattern}$")

        # Trouver les correspondances
        matching_words = [w for w in all_words if py_regex.match(w)]
        
        # Obtenir les fréquences des mots les plus communs
        word_frequencies = get_word_frequency(cursor, matching_words)

        # Compter les livres uniques
        if matching_words:
            placeholders = ','.join(['?' for _ in matching_words])
            cursor.execute(f"""
                SELECT COUNT(DISTINCT book_id) 
                FROM word_count 
                WHERE word IN ({placeholders})
            """, matching_words)
        else:
            cursor.execute("SELECT 0")
            
        num_books = cursor.fetchone()[0]

        # Afficher les résultats détaillés
        print(f"Nombre de mots correspondants: {len(matching_words)}")
        print(f"Nombre de livres concernés: {num_books} ({(num_books/total_books*100):.1f}% du total)")
        
        if matching_words:
            print("\nExemples de mots (par fréquence):")
            for word, freq in word_frequencies.items():
                print(f"  - {word}: {freq} occurrences")
            
            if len(matching_words) > 5:
                print(f"... et {len(matching_words) - 5} autres mots uniques")
        
        # Distribution des mots par longueur
        if matching_words:
            lengths = [len(w) for w in matching_words]
            avg_length = sum(lengths) / len(lengths)
            print(f"\nLongueur moyenne des mots: {avg_length:.1f} caractères")
            
        print("\n" + "="*50 + "\n")

    conn.close()

if __name__ == "__main__":
    try:
        test_regex_patterns()
    except Exception as e:
        print(colored(f"Erreur: {str(e)}", 'red', attrs=['bold']))