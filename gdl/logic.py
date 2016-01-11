from gdl.error import GDLError


class DatalogError(GDLError):
    pass


class Database(object):
    def __init__(self):
        self.db = {}

    def define_fact(self, term, arity, args):
        key = (term, arity)
        if key not in self.db:
            self.db[key] = []
        self._sanity_check_fact_arguments(args)
        self.db[key].append((args, []))

    def query(self, ast_head):
        key = (ast_head.term, ast_head.arity)
        if key not in self.db:
            raise DatalogError(GDLError.NO_RULE % key, ast_head.token)

        ret = []
        for args, body in self.db[key]:
            if not body:
                match = self._compare_fact(ast_head.children, args)
                if match is True:
                    return True
                elif match:
                    ret.append(match)
        return ret if ret else False

    def _compare_fact(self, query_args, fact_args, matches=None):
        if matches is None:
            matches = {}
        for query, fact in zip(query_args, fact_args):
            if query.is_variable():
                if query.term in matches:
                    if matches[query.term] != fact:
                        return False
                else:
                    matches[query.term] = fact.copy()
            elif query.term == fact.term and query.arity == fact.arity:
                if self._compare_fact(query.children, fact.children, matches) is False:
                    return False
            else:
                return False
        return matches if matches else True

    def _sanity_check_fact_arguments(self, args):
        if type(args) is not list:
            raise TypeError('fact arguments should be a list')
        for arg in args:
            if arg.arity > 0:
                self._sanity_check_fact_arguments(arg.children)
            if arg.is_variable():
                raise DatalogError(GDLError.FACT_VARIABLE, arg.token)
