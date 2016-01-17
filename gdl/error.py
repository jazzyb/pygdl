import os


class GDLError(Exception):
    EXPECTED_CONSTANT = 'A constant was expected.'
    UNEXPECTED_CLOSE = 'Unexpected closed parenthesis.'
    BAD_RELATION = "The builtin relation '%s/%d' has the wrong arity."
    FACT_VARIABLE = 'Variables are not allowed in facts.'
    NO_PREDICATE = "No such predicate '%s/%d'."
    DOUBLE_NOT = "Double negatives aren't not disallowed."

    def __init__(self, message, token):
        errmsg = message + os.linesep + self._errmsg(token)
        super(GDLError, self).__init__(errmsg)

    def _errmsg(self, token):
        lineno = '%d: ' % token.lineno
        nspaces = len(lineno) + token.column - 1
        err = lineno + token.line.rstrip() + os.linesep + (' ' * nspaces) + '^'
        return err
