from typing import List, Set, Dict
from dataclasses import dataclass, field
from collections import deque
from .regex_tree import RegExTree, ALTERN, CONCAT, ETOILE

@dataclass
class NonDeterministicAutomaton:
    transitions: List[List[List[int]]] = field(default_factory=list)
    accepting_states: Set[int] = field(default_factory=set)

    def __init__(self, size: int):
        self.transitions = [[] for _ in range(size)]
        self.accepting_states = set()

    def add_transition(self, ancestor: int, child: int, input_symbol: int):
        while len(self.transitions) <= ancestor:
            self.transitions.append([])
        self.transitions[ancestor].append([input_symbol, child])

    def alphabet(self) -> Set[int]:
        alphabet = set()
        for state_transitions in self.transitions:
            for transition in state_transitions:
                if transition[0] > -1:  # Ignore epsilon transitions
                    alphabet.add(transition[0])
        return alphabet

    @staticmethod
    def construct(tree: RegExTree) -> 'NonDeterministicAutomaton':
        if not tree.subTrees:
            return NonDeterministicAutomaton.create_simple_automaton(tree.root)

        if tree.root == ALTERN:
            return NonDeterministicAutomaton.altern_automaton(tree)
        elif tree.root == CONCAT:
            return NonDeterministicAutomaton.concat_automaton(tree)
        elif tree.root == ETOILE:
            return NonDeterministicAutomaton.star_automaton(tree)
        
        raise Exception(f"Unknown operator: {tree.root}")

    @staticmethod
    def create_simple_automaton(input_symbol: int) -> 'NonDeterministicAutomaton':
        automaton = NonDeterministicAutomaton(2)
        automaton.add_transition(0, 1, input_symbol)
        automaton.accepting_states.add(1)
        return automaton

    @staticmethod
    def altern_automaton(tree: RegExTree) -> 'NonDeterministicAutomaton':
        left_child = NonDeterministicAutomaton.construct(tree.subTrees[0])
        right_child = NonDeterministicAutomaton.construct(tree.subTrees[1])
        
        total_states = len(left_child.transitions) + len(right_child.transitions) + 2
        automaton = NonDeterministicAutomaton(total_states)
        
        # Add epsilon transitions from new start state
        automaton.add_transition(0, 1, -1)  # To left automaton
        automaton.add_transition(0, len(left_child.transitions) + 1, -1)  # To right automaton
        
        # Copy transitions from left and right automata
        NonDeterministicAutomaton._merge_automaton(1, left_child, automaton)
        NonDeterministicAutomaton._merge_automaton(len(left_child.transitions) + 1, right_child, automaton)
        
        # Add epsilon transitions to new final state
        automaton.add_transition(len(left_child.transitions), total_states - 1, -1)
        automaton.add_transition(total_states - 2, total_states - 1, -1)
        
        automaton.accepting_states.add(total_states - 1)
        return automaton

    @staticmethod
    def concat_automaton(tree: RegExTree) -> 'NonDeterministicAutomaton':
        left = NonDeterministicAutomaton.construct(tree.subTrees[0])
        right = NonDeterministicAutomaton.construct(tree.subTrees[1])
        
        automaton = NonDeterministicAutomaton(len(left.transitions) + len(right.transitions))
        NonDeterministicAutomaton._merge_automaton(0, left, automaton)
        automaton.add_transition(len(left.transitions) - 1, len(left.transitions), -1)
        NonDeterministicAutomaton._merge_automaton(len(left.transitions), right, automaton)
        
        automaton.accepting_states.add(len(left.transitions) + len(right.transitions) - 1)
        return automaton

    @staticmethod
    def star_automaton(tree: RegExTree) -> 'NonDeterministicAutomaton':
        inner = NonDeterministicAutomaton.construct(tree.subTrees[0])
        automaton = NonDeterministicAutomaton(len(inner.transitions) + 2)
        
        # Add initial epsilon transitions
        automaton.add_transition(0, 1, -1)
        automaton.add_transition(0, len(inner.transitions) + 1, -1)
        
        # Copy inner automaton transitions
        NonDeterministicAutomaton._merge_automaton(1, inner, automaton)
        
        # Add loop back and skip transitions
        automaton.add_transition(len(inner.transitions), 1, -1)
        automaton.add_transition(len(inner.transitions), len(inner.transitions) + 1, -1)
        
        automaton.accepting_states.add(len(inner.transitions) + 1)
        return automaton

    @staticmethod
    def _merge_automaton(offset: int, source: 'NonDeterministicAutomaton', target: 'NonDeterministicAutomaton'):
        for state, transitions in enumerate(source.transitions):
            for transition in transitions:
                target.add_transition(offset + state, offset + transition[1], transition[0])

