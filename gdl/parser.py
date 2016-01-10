from gdl.error import GDLError


class ParseError(GDLError):
    pass


class ASTNode(object):
    def __init__(self, token=None, parent=None):
        self.parent = parent
        self.token = token
        self.children = []

    def create_child(self, token):
        child = ASTNode(token, self)
        self.children.append(child)
        return child

    @property
    def term(self):
        return self.token.token

    @property
    def arity(self):
        return len(self.children)


class Parser(object):
    def __init__(self):
        self.head = ASTNode()

    def parse(self, tokens):
        new_sentence = False
        curr = self.head
        for token in tokens:
            if new_sentence:
                if not token.is_constant():
                    raise ParseError(GDLError.EXPECTED_CONSTANT, token)
                curr = curr.create_child(token)
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
