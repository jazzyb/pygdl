from gdl.ast import ASTNode
from gdl.error import GDLError


class ParseError(GDLError):
    pass


class Parser(object):
    def __init__(self):
        self.head = ASTNode()

    def parse(self, tokens):
        new_sentence = False
        negative = False
        curr = self.head
        for token in tokens:
            if new_sentence:
                if not token.is_constant():
                    raise ParseError(GDLError.EXPECTED_CONSTANT, token)
                if token.is_not():
                    if negative:
                        raise ParseError(GDLError.DOUBLE_NOT, token)
                    negative = True
                    new_sentence = False
                    continue
                curr = curr.create_child(token)
                if negative:
                    curr.is_negative = negative
                    negative = False
                new_sentence = False
            elif token.is_open():
                new_sentence = True
            elif token.is_close():
                if curr.is_neg():
                    continue
                curr = curr.parent
                if curr is None:
                    raise ParseError(GDLError.UNEXPECTED_CLOSE, token)
            else:
                curr.create_child(token)
        return self.head
