from gdl.lexer import Lexeme


class ASTNode(object):
    def __init__(self, token=None):
        self.token = token
        self.children = []

    @staticmethod
    def new(value):
        return ASTNode(Lexeme.new(value))

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

    def is_constant(self):
        return self.token.is_constant()

    def is_rule(self):
        return self.token.is_rule()

    def is_not(self):
        return self.token.is_not()

    def is_distinct(self):
        return self.token.is_distinct()

    def is_or(self):
        return self.token.is_or()

    def is_init(self):
        return self.token.is_init()

    def is_true(self):
        return self.token.is_true()

    def copy(self):
        head = ASTNode(self.token.copy())
        head.children = [child.copy() for child in self.children]
        return head

    def set_variables(self, variable_dict):
        if self.is_variable():
            copy = variable_dict[self.term].copy()
        else:
            copy = ASTNode(self.token.copy())
            copy.children = [child.set_variables(variable_dict) \
                    for child in self.children]
        return copy

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
