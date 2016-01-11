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

    def is_variable(self):
        return self.token.is_variable()

    def copy(self, parent=None):
        head = ASTNode(self.token, parent)
        head.children = [child.copy(head) for child in self.children]
        return head

    def __eq__(self, other):
        if (self.term, self.arity) != (other.term, other.arity):
            return False
        for a, b in zip(self.children, other.children):
            if a != b:
                return False
        return True
