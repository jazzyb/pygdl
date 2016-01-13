from gdl.error import GDLError


class DatalogError(GDLError):
    pass


class Database(object):
    def __init__(self):
        self.facts = {}
        self.derived_facts = {}
        self.rules = {}

    def define_fact(self, term, arity, args):
        self._sanity_check_fact_arguments(args)
        self.facts.setdefault((term, arity), []).append(args)

    def define_rule(self, term, arity, args, body):
        self._sanity_check_new_rule(term, arity, args, body)
        key = (term, arity)
        self.rules.setdefault(key, []).append((args, body))
        self.derived_facts.pop(key, None)

    def query(self, ast_head):
        key = (ast_head.term, ast_head.arity)
        if key not in self.facts and key not in self.rules:
            raise DatalogError(GDLError.NO_PREDICATE % key, ast_head.token)

        f = self._find_facts(self.facts.get(key, []), ast_head.children)
        if f is True:
            return True
        r = self._derive_facts(key, ast_head.children)
        if r is True:
            return True

        results = f + r
        return results if results else False

    def _find_facts(self, table, query):
        results = []
        for args in table:
            match = self._compare_fact(query, args)
            if match is True:
                return True
            elif match:
                results.append(match)
        return results

    def _compare_fact(self, query_args, fact_args, matches=None):
        matches = matches or {}
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

    def _derive_facts(self, key, query):
        if key in self.derived_facts:
            return self._find_facts(self.derived_facts[key], query)
        self._process_rules(key)
        return self._find_facts(self.derived_facts.get(key, []), query)

    def _process_rules(self, key):
        for args, body in self.rules.get(key, []):
            variables = self._process_rule_body(body)
            if variables is not False:
                pass

    def _sanity_check_fact_arguments(self, args):
        if type(args) is not list:
            raise TypeError('fact arguments should be a list')
        for arg in args:
            if arg.arity > 0:
                self._sanity_check_fact_arguments(arg.children)
            if arg.is_variable():
                raise DatalogError(GDLError.FACT_VARIABLE, arg.token)

    def _sanity_check_new_rule(self, term, arity, args, body):
        pass # TODO
