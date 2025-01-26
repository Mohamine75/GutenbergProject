import sqlite3
import os
import numpy as np
import networkx as nx
from typing import List, Tuple, Dict

# Configuration globale
TOP_WORDS_COUNT = 100 # Nombre de mots pris en compte pour les similarités de Jaccard
SIMILARITY_THRESHOLD = 0.1

class BookSimilarityAnalyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.initialize_tables()
        
    def initialize_tables(self):
        """Initialise toutes les tables nécessaires."""
        cursor = self.conn.cursor()

        # Nettoyage des tables existantes
        print("Nettoyage des tables existantes...")
        cursor.execute("DELETE FROM similarity_edges")
        cursor.execute("DELETE FROM centrality_measures")
        
        # Table pour les similarités
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS similarity_edges (
            source_book_id INTEGER,
            target_book_id INTEGER,
            similarity_score FLOAT,
            FOREIGN KEY (source_book_id) REFERENCES books(id),
            FOREIGN KEY (target_book_id) REFERENCES books(id),
            PRIMARY KEY (source_book_id, target_book_id)
        )
        """)
        
        # Table pour les mesures de centralité
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centrality_measures (
            book_id INTEGER PRIMARY KEY,
            closeness_score FLOAT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
        """)
        
        # Index pour optimiser les requêtes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_similarity_source ON similarity_edges(source_book_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_similarity_target ON similarity_edges(target_book_id)")
        
        self.conn.commit()

    def get_top_words_by_book(self) -> Dict[int, List[str]]:
        """Récupère les N mots les plus fréquents pour chaque livre."""
        cursor = self.conn.cursor()
        
        # Requête SQL avec ROW_NUMBER() pour classer les mots par fréquence
        query = f"""
        WITH RankedWords AS (
            SELECT 
                book_id,
                word,
                occurrences,
                ROW_NUMBER() OVER (PARTITION BY book_id ORDER BY occurrences DESC) as rank
            FROM word_count
        )
        SELECT book_id, word
        FROM RankedWords
        WHERE rank <= {TOP_WORDS_COUNT}
        ORDER BY book_id, occurrences DESC
        """
        
        cursor.execute(query)
        
        # Organisation des résultats par livre
        book_words = {}
        for book_id, word in cursor.fetchall():
            if book_id not in book_words:
                book_words[book_id] = []
            book_words[book_id].append(word)
            
        return book_words

    def calculate_similarities(self):
        """Calcule et stocke les similarités de Jaccard entre tous les livres."""
        book_words = self.get_top_words_by_book()
        book_ids = list(book_words.keys())
        n_books = len(book_ids)
        
        # Matrice de similarité pour NetworkX
        similarity_matrix = np.zeros((n_books, n_books))
        
        cursor = self.conn.cursor()
        
        # Calcul des similarités de Jaccard
        for i, book1_id in enumerate(book_ids):
            words1 = set(book_words[book1_id])
            for j, book2_id in enumerate(book_ids):
                if i != j:
                    words2 = set(book_words[book2_id])
                    intersection = len(words1 & words2)
                    union = len(words1 | words2)
                    similarity = intersection / union if union > 0 else 0
                    
                    # Stockage dans la matrice pour NetworkX
                    similarity_matrix[i][j] = similarity
                    
                    # Stockage dans la base de données
                    if similarity >= SIMILARITY_THRESHOLD:
                        cursor.execute("""
                        INSERT OR REPLACE INTO similarity_edges 
                        (source_book_id, target_book_id, similarity_score)
                        VALUES (?, ?, ?)
                        """, (book1_id, book2_id, similarity))
        
        self.conn.commit()
        
        # Calcul de la centralité closeness
        G = nx.from_numpy_array(similarity_matrix)
        closeness_scores = nx.closeness_centrality(G)
        
        # Stockage des scores de centralité
        for i, book_id in enumerate(book_ids):
            cursor.execute("""
            INSERT OR REPLACE INTO centrality_measures (book_id, closeness_score)
            VALUES (?, ?)
            """, (book_id, closeness_scores[i]))
        
        self.conn.commit()

if __name__ == "__main__":
    db_path = os.path.join("./", "db.sqlite3")
    analyzer = BookSimilarityAnalyzer(db_path)
    analyzer.calculate_similarities()