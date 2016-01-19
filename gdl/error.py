import os


class GDLError(Exception):
    EXPECTED_CONSTANT = 'A constant was expected.'
    UNEXPECTED_CLOSE = 'Unexpected closed parenthesis.'
    MISSING_CLOSE = 'Missing closed parenthesis.'
    BAD_PREDICATE = "The built-in predicate '%s/%d' has the wrong arity."
    FACT_VARIABLE = 'Variables are not allowed in facts.'
    NO_PREDICATE = "No such predicate '%s/%d'."
    DOUBLE_NOT = "Double negatives aren't not disallowed."
    NEGATIVE_VARIABLE = "'%s' must appear in a positive literal in the body."
    NEGATIVE_CYCLE = 'Literal in rule creates a recursive cycle with at least one negative edge.'
    FACT_RESERVED = "Reserved keyword '%s' is not allowed in facts."
    RULE_HEAD_RESERVED = "Reserved keyword '%s' is not allowed in the head of a rule."

    def __init__(self, message, token):
        errmsg = message + os.linesep + self._errmsg(token)
        super(GDLError, self).__init__(errmsg)

    def _errmsg(self, token):
        lineno = '%d: ' % token.lineno
        nspaces = len(lineno) + token.column - 1
        err = lineno + token.line.rstrip() + os.linesep + (' ' * nspaces) + '^'
        return err
