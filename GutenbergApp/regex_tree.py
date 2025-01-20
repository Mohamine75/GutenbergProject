from typing import List, Optional, Set
from dataclasses import dataclass

# Constants
CONCAT = 0xC04CA7
ETOILE = 0xE7011E
ALTERN = 0xA17E54
PROTECTION = 0xBADDAD
PARENTHESEOUVRANT = 0x16641664
PARENTHESEFERMANT = 0x51515151
DOT = 0xD07
PLUS = 0x2

@dataclass
class RegExTree:
    root: int
    subTrees: List['RegExTree']

    def __str__(self) -> str:
        if not self.subTrees:
            return self.root_to_string()
        
        result = f"{self.root_to_string()}({self.subTrees[0]}"
        for i in range(1, len(self.subTrees)):
            result += f",{self.subTrees[i]}"
        return result + ")"

    def root_to_string(self) -> str:
        if self.root == CONCAT:
            return "."
        if self.root == ETOILE:
            return "*"
        if self.root == PLUS:
            return "+"
        if self.root == ALTERN:
            return "|"
        if self.root == DOT:
            return "."
        return chr(self.root)

class RegexParser:
    def __init__(self, regex: str):
        self.regex = regex.lower()

    def char_to_root(self, c: str) -> int:
        if c == '.': return DOT
        if c == '*': return ETOILE
        if c == '|': return ALTERN
        if c == '(': return PARENTHESEOUVRANT
        if c == ')': return PARENTHESEFERMANT
        if c == '+': return PLUS
        return ord(c)

    def parse(self) -> RegExTree:
        result = []
        for c in self.regex:
            result.append(RegExTree(self.char_to_root(c), []))
        
        return self._parse_helper(result)

    def _parse_helper(self, result: List[RegExTree]) -> RegExTree:
        while self._contain_parenthese(result):
            result = self._process_parenthese(result)
        while self._contain_etoile(result):
            result = self._process_etoile(result)
        while self._contain_plus(result):
            result = self._process_plus(result)
        while self._contain_concat(result):
            result = self._process_concat(result)
        while self._contain_altern(result):
            result = self._process_altern(result)

        if len(result) > 1:
            raise Exception("Invalid regex")

        return self._remove_protection(result[0])

    def _contain_parenthese(self, trees: List[RegExTree]) -> bool:
        return any(t.root == PARENTHESEFERMANT or t.root == PARENTHESEOUVRANT for t in trees)

    def _process_parenthese(self, trees: List[RegExTree]) -> List[RegExTree]:
        result = []
        found = False
        for t in trees:
            if not found and t.root == PARENTHESEFERMANT:
                done = False
                content = []
                while not done and result:
                    if result[-1].root == PARENTHESEOUVRANT:
                        done = True
                        result.pop()
                    else:
                        content.insert(0, result.pop())
                if not done:
                    raise Exception("Mismatched parentheses")
                found = True
                result.append(RegExTree(PROTECTION, [self._parse_helper(content)]))
            else:
                result.append(t)
        if not found:
            raise Exception("No closing parenthesis found")
        return result
    
    def _contain_etoile(self, trees: List[RegExTree]) -> bool:
        return any(t.root == ETOILE and not t.subTrees for t in trees)

    def _process_etoile(self, trees: List[RegExTree]) -> List[RegExTree]:
        result = []
        found = False
        for t in trees:
            if not found and t.root == ETOILE and not t.subTrees:
                if not result:
                    raise Exception("* operator needs a preceding expression")
                found = True
                last = result.pop()
                result.append(RegExTree(ETOILE, [last]))
            else:
                result.append(t)
        return result

    def _contain_concat(self, trees: List[RegExTree]) -> bool:
        firstFound = False
        for t in trees:
            if not firstFound and t.root != ALTERN:
                firstFound = True
                continue
            if firstFound and t.root != ALTERN:
                return True
            if t.root == ALTERN:
                firstFound = False
        return False

    def _process_concat(self, trees: List[RegExTree]) -> List[RegExTree]:
        result = []
        found = False
        firstFound = False
        for t in trees:
            if not found and not firstFound and t.root != ALTERN:
                firstFound = True
                result.append(t)
                continue
            if not found and firstFound and t.root == ALTERN:
                firstFound = False
                result.append(t)
                continue
            if not found and firstFound and t.root != ALTERN:
                found = True
                last = result.pop()
                subTrees = [last, t]
                result.append(RegExTree(CONCAT, subTrees))
            else:
                result.append(t)
        return result

    def _contain_plus(self, trees: List[RegExTree]) -> bool:
        return any(t.root == PLUS and not t.subTrees for t in trees)

    def _process_plus(self, trees: List[RegExTree]) -> List[RegExTree]:
        result = []
        found = False
        for t in trees:
            if not found and t.root == PLUS and not t.subTrees:
                if not result:
                    raise Exception("+ operator needs a preceding expression")
                found = True
                last = result.pop()
                result.append(RegExTree(PLUS, [last]))
            else:
                result.append(t)
        return result

    def _contain_altern(self, trees: List[RegExTree]) -> bool:
        return any(t.root == ALTERN and not t.subTrees for t in trees)

    def _process_altern(self, trees: List[RegExTree]) -> List[RegExTree]:
        result = []
        found = False
        gauche = None
        done = False
        for t in trees:
            if not found and t.root == ALTERN and not t.subTrees:
                if not result:
                    raise Exception("| operator needs a preceding expression")
                found = True
                gauche = result.pop()
                continue
            if found and not done:
                if gauche is None:
                    raise Exception("Invalid alternation")
                done = True
                subTrees = [gauche, t]
                result.append(RegExTree(ALTERN, subTrees))
            else:
                result.append(t)
        return result

    def _remove_protection(self, tree: RegExTree) -> RegExTree:
        if tree.root == PROTECTION and len(tree.subTrees) != 1:
            raise Exception("Invalid protection")
        if not tree.subTrees:
            return tree
        if tree.root == PROTECTION:
            return self._remove_protection(tree.subTrees[0])

        subTrees = [self._remove_protection(t) for t in tree.subTrees]
        return RegExTree(tree.root, subTrees)