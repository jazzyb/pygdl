from collections import deque
from gdl.error import GDLError


class DatalogError(GDLError):
    pass


class Database(object):
    def __init__(self):
        self.facts = {}
        self.derived_facts = {}
        self.rules = {}
        self.requirements = {}

    ## PUBLIC API

    def define_fact(self, term, arity, args):
        self._sanity_check_fact_arguments(args)
        self.facts.setdefault((term, arity), []).append(args)

    def define_rule(self, term, arity, args, body):
        self._sanity_check_new_rule(term, arity, args, body)
        key = (term, arity)
        self.rules.setdefault(key, []).append((args, body))
        self._set_rule_requirements(key, body)
        self._delete_derived_facts(key)

    def query(self, ast_head):
        key = (ast_head.term, ast_head.arity)
        if key not in self.facts and key not in self.rules:
            raise DatalogError(GDLError.NO_PREDICATE % key, ast_head.token)

        facts = self._find_facts(self.facts.get(key, []), ast_head.children)
        if facts is True:
            return True
        derived_facts = self._derive_facts(key, ast_head.children)
        if derived_facts is True:
            return True

        results = facts + derived_facts
        return results if results else False

    ## HELPERS

    def _set_rule_requirements(self, rule, sentences):
        for sentence in sentences:
            req = (sentence.term, sentence.arity)
            if req != rule:
                self.requirements.setdefault(req, set()).add(rule)

    def _delete_derived_facts(self, key):
        for rule in self._collect_requirements(key, [key]):
            self.derived_facts.pop(rule, None)

    def _collect_requirements(self, key, keys):
        for rule in self.requirements.get(key, []):
            if rule not in keys:
                keys.append(rule)
                self._collect_requirements(rule, keys)
        return keys

    def _find_facts(self, table, query, variables=None):
        results = []
        for args in table:
            variables = None if variables is None else variables.copy()
            match = self._compare_fact(query, args, variables)
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
        if key not in self.rules:
            return []
        if key in self.derived_facts:
            return self._find_facts(self.derived_facts[key], query)
        self._process_rule(key)
        return self._find_facts(self.derived_facts.get(key, []), query)

    def _process_rule(self, rule):
        rules = deque([rule])
        new_facts = {}
        while rules:
            name = rules.popleft()
            nrules = len(rules)
            nfacts = len(new_facts.get(name, []))
            for args, body in self.rules.get(name, []):
                found_rules, variable_list = self._evaluate_body(body, new_facts)
                rules.extend(filter(lambda x: x != rule and x not in rules, found_rules))
                for fact in self._set_variables(args, variable_list):
                    if fact not in new_facts.get(name, []):
                        new_facts.setdefault(name, []).append(fact)

            if len(new_facts.get(name, [])) > nfacts or len(rules) > nrules:
                rules.append(name)
            else:
                self.derived_facts[name] = new_facts[name]

    def _evaluate_body(self, body, more_facts):
        found_rules = set()
        variable_list = [None]
        for literal in body:
            name = (literal.term, literal.arity)
            if name in self.rules and name not in self.derived_facts:
                found_rules.add(name)

            table = self.facts.get(name, []) + \
                    self.derived_facts.get(name, []) + \
                    more_facts.get(name, [])

            new_varlist = []
            for var_dict in variable_list:
                results = self._find_facts(table, literal.children, var_dict)
                if results is True:
                    new_varlist.append(var_dict)
                elif results:
                    new_varlist.extend(results)
            variable_list = new_varlist

        return found_rules, filter(lambda x: x is not None, variable_list)

    def _set_variables(self, args, variables):
        ret = []
        for var_dict in variables:
            new_args = []
            for arg in args:
                const_tree = arg.copy()
                self._vars_to_consts(const_tree, var_dict)
                new_args.append(const_tree)
            ret.append(new_args)
        return ret

    def _vars_to_consts(self, node, var_dict):
        if node.is_variable():
            node.token.token = var_dict[node.term].term
        for child in node.children:
            self._vars_to_consts(child, var_dict)

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
