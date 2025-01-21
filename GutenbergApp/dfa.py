from typing import List, Set, Dict, Optional
from dataclasses import dataclass, field
from collections import deque
from .regex_tree import RegExTree
from .nfa import NonDeterministicAutomaton

@dataclass
class DeterministicAutomaton:
    transitions: List[Dict[int, int]] = field(default_factory=list)
    accepting_states: Set[int] = field(default_factory=set)

    def __init__(self, size_or_nfa: int | NonDeterministicAutomaton):
        self.transitions = []
        self.accepting_states = set()
        
        if isinstance(size_or_nfa, int):
            self.transitions = [{} for _ in range(size_or_nfa)]
        else:
            self._determinize(size_or_nfa)

    def add_transition(self, ancestor: int, child: int, input_symbol: int):
        while len(self.transitions) <= ancestor:
            self.transitions.append({})
        self.transitions[ancestor][input_symbol] = child

    def get_transition(self, current_state: int, symbol: int) -> Optional[int]:
        if current_state < len(self.transitions):
            return self.transitions[current_state].get(symbol)
        return None

    def alphabet(self) -> Set[int]:
        alphabet = set()
        for state_transitions in self.transitions:
            alphabet.update(state_transitions.keys())
        return alphabet

    @staticmethod
    def _epsilon_closure(automaton: NonDeterministicAutomaton, states: Set[int]) -> Set[int]:
        closure = set(states)
        stack = deque(states)
        
        while stack:
            current_state = stack.pop()
            for transition in automaton.transitions[current_state]:
                if transition[0] == -1:  # epsilon transition
                    next_state = transition[1]
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)
        
        return closure

    def _determinize(self, nfa: NonDeterministicAutomaton):
        # Map from set of NFA states to DFA state number
        state_map: Dict[frozenset[int], int] = {}
        queue = deque()

        # Initialize with epsilon closure of initial state
        start_state = frozenset(self._epsilon_closure(nfa, {0}))
        queue.append(start_state)
        state_map[start_state] = 0
        new_state_id = 1

        while queue:
            current_set = queue.popleft()
            dfa_state = state_map[current_set]

            # Initialize transitions for new state if needed
            while len(self.transitions) <= dfa_state:
                self.transitions.append({})

            # Group transitions by input symbol
            symbol_to_states: Dict[int, Set[int]] = {}
            
            for nfa_state in current_set:
                for transition in nfa.transitions[nfa_state]:
                    symbol = transition[0]
                    target_state = transition[1]
                    
                    if symbol != -1:  # Ignore epsilon transitions
                        if symbol not in symbol_to_states:
                            symbol_to_states[symbol] = set()
                        symbol_to_states[symbol].add(target_state)

            # Process each group of transitions
            for symbol, target_states in symbol_to_states.items():
                # Get epsilon closure of target states
                next_state_set = frozenset(self._epsilon_closure(nfa, target_states))
                
                # Create new DFA state if needed
                if next_state_set not in state_map:
                    state_map[next_state_set] = new_state_id
                    queue.append(next_state_set)
                    new_state_id += 1

                # Add transition to DFA
                self.add_transition(dfa_state, state_map[next_state_set], symbol)

        # Set accepting states
        for nfa_states, dfa_state in state_map.items():
            if any(state in nfa.accepting_states for state in nfa_states):
                self.accepting_states.add(dfa_state)


    def minimize(self) -> 'DeterministicAutomaton':
        num_states = len(self.transitions)
        alphabet = self.alphabet()

        # Partition initial: accepting and non-accepting states
        partition: List[Set[int]] = []
        final_states = set(self.accepting_states)
        non_final_states = set(range(num_states)) - final_states

        # Important: on garde l'état initial (0) dans son propre groupe
        initial_state_set = {0}
        non_final_states.discard(0)

        if final_states:
            partition.append(final_states)
        if non_final_states:
            partition.append(non_final_states)
        if initial_state_set:
            partition.insert(0, initial_state_set)  # Important: on met l'état initial en premier

        # Queue for processing partition refinement
        work_list = deque(partition)

        while work_list:
            current_set = work_list.popleft()

            for symbol in alphabet:
                pre_image = set()

                # Calculate pre-image
                for state in range(num_states):
                    next_state = self.get_transition(state, symbol)
                    if next_state is not None and next_state in current_set:
                        pre_image.add(state)

                # Refine partitions
                new_partition: List[Set[int]] = []
                for subset in partition:
                    intersection = subset & pre_image
                    difference = subset - pre_image

                    if intersection and difference:
                        new_partition.append(intersection)
                        new_partition.append(difference)

                        if subset in work_list:
                            work_list.remove(subset)
                            work_list.append(intersection)
                            work_list.append(difference)
                        else:
                            if len(intersection) <= len(difference):
                                work_list.append(intersection)
                            else:
                                work_list.append(difference)
                    else:
                        new_partition.append(subset)

                partition = new_partition

        # Build minimized DFA
        state_map = {}
        minimized_dfa = DeterministicAutomaton(len(partition))
        
        # Map original states to new states, en préservant l'état initial
        for new_state, equiv_class in enumerate(partition):
            for old_state in equiv_class:
                state_map[old_state] = new_state
            if equiv_class & self.accepting_states:
                minimized_dfa.accepting_states.add(new_state)

        # Add transitions to minimized DFA
        for old_state, transitions in enumerate(self.transitions):
            new_state = state_map[old_state]
            for symbol, target in transitions.items():
                minimized_dfa.add_transition(new_state, state_map[target], symbol)

        return minimized_dfa

    def match(self, text: str) -> bool:
        """Vérifie si le texte correspond entièrement au pattern de l'automate"""
        current_state = 0
        
        # Pour chaque caractère du texte
        for i in range(len(text)):
            symbol = ord(text[i])
            next_state = self.get_transition(current_state, symbol)
            
            # Si pas de transition possible, le mot ne correspond pas
            if next_state is None:
                return False
                
            current_state = next_state
        
        # Le mot est valide seulement si on termine dans un état acceptant
        # ET qu'on a consommé tout le mot
        return current_state in self.accepting_states

    def __str__(self) -> str:
        result = "Transitions:\n"
        for state, transitions in enumerate(self.transitions):
            for input_symbol, target in transitions.items():
                result += f"(State {state}): [{chr(input_symbol)}] ===> (State {target})\n"
        result += f"Accepting states: {self.accepting_states}\n"
        return result