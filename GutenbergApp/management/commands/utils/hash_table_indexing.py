import mmh3
import pickle
import re
from typing import List, Tuple, Dict, Optional
from collections import Counter

class WordHashTable:
    def __init__(self, size: int = 100000):
        """
        Initialise la table de hachage pour indexer les mots des livres.
        
        Args:
            size: Taille de la table de hachage
        """
        self.size = size
        self.table = [[] for _ in range(size)]
        self.word_count = 0
        self.total_words_processed = 0
        self.books_processed = set()
    
    def _hash(self, word: str) -> int:
        """Calcule l'index de hachage pour un mot."""
        return mmh3.hash(word, seed=42) % self.size
    
    def _normalize_word(self, word: str) -> str:
        """Normalise un mot (lowercase, suppression ponctuation)."""
        return re.sub(r'[^\w\s]', '', word.lower())
    
    def add_word(self, word: str, book_id: int, occurrences: int):
        """
        Ajoute ou met à jour le nombre total d'occurrences d'un mot pour un livre
        """
        index = self._hash(word)
        bucket = self.table[index]
        
        # Cherche si le mot existe déjà dans ce bucket
        for word_entry in bucket:
            if word_entry[0] == word:
                # Le mot existe, remplace simplement les occurrences pour ce livre
                word_entry[1].append((book_id, occurrences))
                return
                
        # Si le mot n'existe pas, crée une nouvelle entrée
        bucket.append((word, [(book_id, occurrences)]))
        self.word_count += 1
    
    def get_word_occurrences(self, word: str) -> List[Tuple[int, int]]:
        """
        Récupère les occurrences d'un mot dans tous les livres.
        
        Returns:
            Liste de tuples (book_id, occurrences)
        """
        word = self._normalize_word(word)
        if not word:
            return []
            
        index = self._hash(word)
        bucket = self.table[index]
        
        for existing_word, occurrences_list in bucket:
            if existing_word == word:
                return sorted(occurrences_list, key=lambda x: (-x[1], x[0]))  # Tri par occurrences desc
        return []
    
    def process_book(self, book_id: int, text: str) -> Dict[str, int]:
        """
        Traite un livre entier et ajoute tous ses mots à la table.
        
        Args:
            book_id: L'identifiant du livre
            text: Le texte complet du livre
            
        Returns:
            Dictionnaire des mots et leurs occurrences dans ce livre
        """
        # Compte les occurrences avec Counter
        words = [self._normalize_word(word) for word in text.split()]
        word_counts = Counter(word for word in words if word)
        
        # Ajoute chaque mot à la table
        for word, count in word_counts.items():
            self.add_word(word, book_id, count)
        
        self.books_processed.add(book_id)
        return dict(word_counts)
    
    def get_stats(self) -> Dict:
        """Retourne des statistiques sur la table de hachage."""
        bucket_sizes = [len(bucket) for bucket in self.table]
        non_empty_buckets = len([size for size in bucket_sizes if size > 0])
        collisions = len([size for size in bucket_sizes if size > 1])
        
        return {
            'total_unique_words': self.word_count,
            'total_words_processed': self.total_words_processed,
            'books_processed': len(self.books_processed),
            'table_size': self.size,
            'max_bucket_size': max(bucket_sizes),
            'avg_bucket_size': sum(bucket_sizes) / self.size,
            'empty_buckets': bucket_sizes.count(0),
            'buckets_with_collisions': collisions,
            'load_factor': non_empty_buckets / self.size
        }
    
    def serialize(self, filename: str) -> None:
        """
        Sauvegarde la table dans un fichier texte sous format :
        index;mot;(book_id-occurrences),(book_id-occurrences),...;
        """
        with open(filename, 'w', encoding='utf-8') as f:
            # Parcourt tous les buckets
            for index, bucket in enumerate(self.table):
                if bucket:  # Si le bucket n'est pas vide
                    for word, occurrences_list in bucket:
                        # Formate les occurrences : (1-12),(3-4)
                        occurrences_str = ','.join(
                            f"({book_id}-{count})" 
                            for book_id, count in occurrences_list
                        )
                        # Écrit la ligne : index;mot;occurrences;
                        f.write(f"{index};{word};{occurrences_str};\n")

    @classmethod
    def deserialize(cls, filename: str) -> 'WordHashTable':
        """
        Recrée la table à partir du fichier texte.
        """
        # Crée une nouvelle table
        table = cls()
        
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                # Découpe la ligne en : [index, mot, occurrences]
                index, word, occurrences_str, _ = line.strip().split(';')
                index = int(index)
                
                # Parse les occurrences : de "(1-12),(3-4)" à [(1,12), (3,4)]
                occurrences = []
                for occ in occurrences_str.split(','):
                    if occ:  # Ignore les chaînes vides
                        # Enlève les parenthèses et split sur le tiret
                        book_id, count = occ.strip('()').split('-')
                        occurrences.append((int(book_id), int(count)))
                
                # Ajoute l'entrée dans la table
                table.table[index].append((word, occurrences))
                table.word_count += 1
                
        return table

# Exemple d'utilisation
def main():
    # Création de la table
    table = WordHashTable(size=1000)  # Petite taille pour l'exemple
    
    # Exemple avec quelques livres
    books = {
        1: "Alice was beginning to get very tired of sitting by her sister",
        2: "In a hole in the ground there lived a hobbit",
        3: "It was the best of times, it was the worst of times"
    }
    
    # Traitement des livres
    for book_id, text in books.items():
        word_counts = table.process_book(book_id, text)
        print(f"\nLivre {book_id} traité:")
        print(f"Mots uniques: {len(word_counts)}")
    
    # Quelques tests
    print("\nRecherche du mot 'was':")
    occurrences = table.get_word_occurrences('was')
    for book_id, count in occurrences:
        print(f"Livre {book_id}: {count} occurrences")
    
    # Sauvegarde et chargement
    table.serialize('word_index.pkl')
    loaded_table = WordHashTable.deserialize('word_index.pkl')
    
    # Statistiques
    print("\nStatistiques de la table:")
    for key, value in loaded_table.get_stats().items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()