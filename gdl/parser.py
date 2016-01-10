import os


class ParseError(Exception):
    EXPECTED_CONSTANT = 'A constant was expected.'
    UNEXPECTED_CLOSE = 'Unexpected closed parenthesis.'

    def __init__(self, message, token):
        errmsg = message + os.linesep + self._errmsg(token)
        super(ParseError, self).__init__(errmsg)

    def _errmsg(self, token):
        lineno = '%d: ' % token.lineno
        nspaces = len(lineno) + token.column - 1
        err = lineno + token.line.rstrip() + os.linesep + (' ' * nspaces) + '^'
        return err


class ASTNode(object):
    def __init__(self, token=None, parent=None):
        self.parent = parent
        self.token = token
        self.children = []

    def create_child(self, token):
        child = ASTNode(token, self)
        self.children.append(child)
        return child


class Parser(object):
    def __init__(self):
        self.head = ASTNode()

    def parse(self, tokens):
        new_sentence = False
        curr = self.head
        for token in tokens:
            if new_sentence:
                if not token.is_constant():
                    raise ParseError(ParseError.EXPECTED_CONSTANT, token)
                curr = curr.create_child(token)
                new_sentence = False
            elif token.is_open():
                new_sentence = True
            elif token.is_close():
                curr = curr.parent
                if curr is None:
                    raise ParseError(ParseError.UNEXPECTED_CLOSE, token)
            else:
                curr.create_child(token)
        return self.head
