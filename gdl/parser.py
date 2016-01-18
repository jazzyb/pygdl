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
        for token in tokens:
            if new_sentence:
                if not token.is_constant():
                    raise ParseError(GDLError.EXPECTED_CONSTANT, token)
                curr = curr.create_child(token)
                if curr.is_not() and curr.parent.is_not():
                    raise ParseError(GDLError.DOUBLE_NOT, token)
                new_sentence = False
            elif token.is_open():
                new_sentence = True
            elif token.is_close():
                curr = curr.parent
                if curr is None:
                    raise ParseError(GDLError.UNEXPECTED_CLOSE, token)
            else:
                curr.create_child(token)
        return self.head
