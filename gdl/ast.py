class ASTNode(object):
    def __init__(self, token=None):
        self.token = token
        self.children = []

    def create_child(self, token):
        child = ASTNode(token)
        self.children.append(child)
        return child

    @property
    def term(self):
        return self.token.value

    @property
    def arity(self):
        return len(self.children)

    @property
    def predicate(self):
        return (self.term, self.arity)

    def is_variable(self):
        return self.token.is_variable()

    def is_not(self):
        return self.token.is_not()

    def is_distinct(self):
        return self.token.is_distinct()

    def is_or(self):
        return self.token.is_or()

    def copy(self):
        head = ASTNode(self.token.copy())
        head.children = [child.copy() for child in self.children]
        return head

    def __eq__(self, other):
        if self.predicate != other.predicate:
            return False
        for a, b in zip(self.children, other.children):
            if a != b:
                return False
        return True

    def __repr__(self):
        ret = ''
        if self.arity > 0:
            ret += '('
        ret += self.term
        for child in self.children:
            ret += ' '
            ret += repr(child)
        if self.arity > 0:
            ret += ')'
        return ret
