class ASTNode(object):
    def __init__(self, token=None, parent=None, is_negative=False):
        self.is_negative = is_negative
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

    def is_variable(self):
        return self.token.is_variable()

    def is_distinct(self):
        return self.token.is_distinct()

    def is_neg(self):
        return self.is_negative

    def copy(self, parent=None, is_negative=None):
        is_negative = self.is_negative if is_negative is None else is_negative
        head = ASTNode(self.token.copy(), parent, is_negative)
        head.children = [child.copy(head) for child in self.children]
        return head

    def __eq__(self, other):
        if (self.term, self.arity) != (other.term, other.arity):
            return False
        for a, b in zip(self.children, other.children):
            if a != b:
                return False
        return True

    def __repr__(self):
        if self.token is None:
            return ' '.join(repr(x) for x in self.children)

        ret = ''
        if self.is_neg():
            ret += '~'
        if self.arity > 0:
            ret += '('
        ret += self.term
        for child in self.children:
            ret += ' '
            ret += repr(child)
        if self.arity > 0:
            ret += ')'
        return ret
