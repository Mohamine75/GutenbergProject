from typing import List, Tuple, Dict
from django.db import connection
from .regex_tree import RegexParser, RegExTree
from .nfa import NonDeterministicAutomaton
from .dfa import DeterministicAutomaton

class RegexSearcher:
    def __init__(self):
        self.automaton = None
        
    def compile_pattern(self, pattern: str):
        # Parse le pattern en arbre syntaxique
        parser = RegexParser(pattern)
        tree = parser.parse()
        
        # Convertit l'arbre en automate
        nfa = NonDeterministicAutomaton.construct(tree)
        dfa = DeterministicAutomaton(nfa)
        self.automaton = dfa.minimize()
    
    def search_pattern(self, pattern: str) -> List[Tuple[int, int, float]]:
        """
        Recherche le pattern dans la base de données.
        Retourne une liste de tuples (book_id, occurrences, closeness_score)
        """
        print(f"Pattern: {pattern}")
        parser = RegexParser(pattern)
        tree = parser.parse()
        print(f"Arbre: {tree}")
        
        nfa = NonDeterministicAutomaton.construct(tree)
        print(f"NFA transitions:")
        for i, trans in enumerate(nfa.transitions):
            print(f"État {i}: {trans}")
        print(f"NFA accepting states: {nfa.accepting_states}")
        
        dfa = DeterministicAutomaton(nfa)
        print(f"DFA:\n{dfa}")
        
        self.automaton = dfa.minimize()
        print(f"DFA minimisé:\n{self.automaton}")
        
        # Récupère tous les mots et leurs occurrences
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT wc.book_id, wc.word, wc.occurrences, cm.closeness_score
                FROM word_count wc
                JOIN centrality_measures cm ON cm.book_id = wc.book_id
            """)
            rows = cursor.fetchall()
        
        # Regroupe les résultats par livre
        book_results = {}
        for book_id, word, occurrences, closeness_score in rows:
            if self.automaton.match(word):
                if book_id not in book_results:
                    book_results[book_id] = (occurrences, closeness_score)
                else:
                    current_occurrences, current_score = book_results[book_id]
                    book_results[book_id] = (current_occurrences + occurrences, current_score)
        
        return [(book_id, occurrences, score) 
                for book_id, (occurrences, score) in book_results.items()]