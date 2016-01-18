from gdl.ast import ASTNode
from gdl.error import GDLError


class ParseError(GDLError):
    pass


class Parser(object):
    def __init__(self):
        self.head = ASTNode()
        self.warnings = []

    def parse(self, tokens):
        new_sentence = False
        curr = self.head
        parents = []
        for token in tokens:
            if new_sentence:
                if not token.is_constant():
                    raise ParseError(GDLError.EXPECTED_CONSTANT, token)
                parents.append(curr)
                curr = curr.create_child(token)
                if curr.is_not() and parents and parents[-1].is_not():
                    raise ParseError(GDLError.DOUBLE_NOT, token)
                new_sentence = False
            elif token.is_open():
                new_sentence = True
            elif token.is_close():
                try:
                    curr = parents.pop()
                except IndexError:
                    raise ParseError(GDLError.UNEXPECTED_CLOSE, token)
            else:
                curr.create_child(token)
        return self.head
