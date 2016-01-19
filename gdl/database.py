from functools import reduce
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

    def define(self, tree):
        if tree.is_rule():
            head, body = tree.children[0], tree.children[1:]
            self.define_rule(head.term, head.arity, head.children, body)
        else:
            self.define_fact(tree.term, tree.arity, tree.children)

    def define_fact(self, term, arity, args):
        self._sanity_check_fact_arguments(args)
        pred = (term, arity)
        self.facts.setdefault(pred, []).append(args)
        self._delete_derived_facts(pred)

    def define_rule(self, term, arity, args, body):
        self._sanity_check_new_rule(term, arity, args, body)
        body = self._move_negative_sentences_to_end(body)
        pred = (term, arity)
        self.rules.setdefault(pred, []).append((args, body))
        self._set_rule_requirements(pred, body)
        self._delete_derived_facts(pred)

    def query(self, ast_head):
        pred = ast_head.predicate
        if pred not in self.facts and pred not in self.rules:
            raise DatalogError(GDLError.NO_PREDICATE % pred, ast_head.token)

        facts = self._find_facts(self.facts.get(pred, []), ast_head.children)
        if facts is True:
            return True
        derived_facts = self._derive_facts(pred, ast_head.children)
        if derived_facts is True:
            return True

        results = facts + derived_facts
        return results if results else False

    ## HELPERS

    def _move_negative_sentences_to_end(self, body):
        pos, neg = [], []
        for sentence in body:
            if self._contains_negative(sentence):
                neg.append(sentence)
            else:
                pos.append(sentence)
        return pos + neg

    def _contains_negative(self, literal):
        if literal.is_not() or literal.is_distinct():
            return True
        for child in literal.children:
            if self._contains_negative(child):
                return True
        return False

    ### DETERMINE RULE DEPENDENCIES:

    def _set_rule_requirements(self, rule, sentences):
        for sentence in sentences:
            self._add_to_requirements(rule, sentence)

    def _add_to_requirements(self, pred, rule):
        if rule.is_not():
            self._add_to_requirements(pred, rule.children[0])
        elif rule.is_or():
            self._add_to_requirements(pred, rule.children[0])
            self._add_to_requirements(pred, rule.children[1])
        elif rule.is_distinct():
            for child in rule.children:
                if child.is_constant():
                    self._add_to_requirements(pred, child)
        elif rule.predicate != pred:
            self.requirements.setdefault(rule.predicate, set()).add(pred)

    def _delete_derived_facts(self, pred):
        for rule in self._collect_requirements(pred, [pred]):
            self.derived_facts.pop(rule, None)

    def _collect_requirements(self, pred, predicates):
        for rule in self.requirements.get(pred, []):
            if rule not in predicates:
                predicates.append(rule)
                self._collect_requirements(rule, predicates)
        return predicates

    ### PROCESS AND ANSWER FACT QUERIES:

    def _find_facts(self, table, query, variables=None):
        results = []
        for args in table:
            match = self._compare_fact(query, args, variables)
            if match is True:
                return True
            elif match:
                results.append(match)
        return results

    def _compare_fact(self, query_args, fact_args, variables=None):
        matches = variables.copy() if variables is not None else {}
        for query, fact in zip(query_args, fact_args):
            if query.is_variable():
                if query.term in matches:
                    if matches[query.term] != fact:
                        return False
                else:
                    matches[query.term] = fact.copy()
            elif query.predicate == fact.predicate:
                if self._compare_fact(query.children, fact.children, matches) is False:
                    return False
            else:
                return False
        return matches if matches else True

    ### PROCESS AND ANSWER RULE QUERIES:

    def _derive_facts(self, pred, query):
        if pred not in self.rules:
            return []
        if pred in self.derived_facts:
            return self._find_facts(self.derived_facts[pred], query)

        new_facts = self._process_rule(pred)
        for key in new_facts:
            self.derived_facts[key] = new_facts[key]

        return self._find_facts(self.derived_facts.get(pred, []), query)

    def _process_rule(self, rule, facts=None, rules=None):
        rules = rules or []
        facts = facts or {}
        nfacts = -1
        while self._num_facts(facts) > nfacts:
            nfacts = self._num_facts(facts)
            for args, body in self.rules[rule]:
                variables = self._evaluate_body(body, facts, rules + [rule])
                for fact in self._set_variables(args, variables):
                    if fact not in facts.get(rule, []):
                        facts.setdefault(rule, []).append(fact)
        return facts

    def _num_facts(self, facts):
        return reduce(lambda total, key: total + len(facts.get(key, [])), facts, 0)

    def _evaluate_body(self, body, facts, rules):
        variables = [None]
        for literal in body:
            variables = self._process_literal(literal, variables, facts, rules)
            if not variables:
                break
        return variables

    def _process_literal(self, literal, variables, facts, rules):
        if literal.is_not():
            literal = literal.children[0]
            return self._evaluate_not(literal, variables, facts, rules)
        elif literal.is_distinct():
            a, b = literal.children
            return self._evaluate_distinct(a, b, variables)
        elif literal.is_or():
            return self._evaluate_or(literal, variables, facts, rules)

        return self._evaluate_literal(literal, variables, facts, rules)

    def _iter_var_results(self, literal, variables, facts, rules):
        pred = literal.predicate
        if self._needs_processing(pred, rules):
            facts = self._process_rule(pred, facts, rules)
        table = self.facts.get(pred, []) + \
                self.derived_facts.get(pred, []) + \
                facts.get(pred, [])
        for var_dict in variables:
            yield self._find_facts(table, literal.children, var_dict), var_dict

    def _needs_processing(self, rule, rules):
        return rule in self.rules and \
               rule not in rules and \
               rule not in self.derived_facts

    def _evaluate_literal(self, literal, variables, facts, rules):
        new_varlist = []
        for results, var_dict in self._iter_var_results(literal, variables, facts, rules):
            if results is True:
                new_varlist.append(var_dict)
            elif results:
                new_varlist.extend(results)
        return new_varlist

    def _evaluate_not(self, literal, variables, facts, rules):
        has_variable = False
        for child in literal.children:
            if child.is_variable():
                has_variable = True

        new_varlist = []
        for results, var_dict in self._iter_var_results(literal, variables, facts, rules):
            if has_variable:
                assert var_dict
            if not results:
                new_varlist.append(var_dict)
        return new_varlist

    def _evaluate_distinct(self, a, b, variables):
        new_variables = []
        for var_dict in map(lambda x: x or {}, variables):
            term_dict = {k: var_dict[k].term for k in var_dict}
            acopy, bcopy = a.copy(), b.copy()
            acopy.set_variables(term_dict)
            bcopy.set_variables(term_dict)
            if acopy != bcopy:
                new_variables.append(var_dict)
        return new_variables

    def _evaluate_or(self, or_, variables, facts, rules):
        first, second = or_.children
        first_vars = self._process_literal(first, variables, facts, rules)
        second_vars = self._process_literal(second, variables, facts, rules)
        new_varlist = first_vars[:]
        for var_dict in second_vars:
            if var_dict not in first_vars:
                new_varlist.append(var_dict)
        return new_varlist

    def _set_variables(self, args, variables):
        ret = []
        for var_dict in map(lambda x: x or {}, variables):
            ret.append([])
            for arg in args:
                copy = arg.copy()
                copy.set_variables({k: var_dict[k].term for k in var_dict})
                ret[-1].append(copy)
        return ret

    ### FACT VALIDATION:

    def _sanity_check_fact_arguments(self, args):
        if type(args) is not list:
            raise TypeError('fact arguments should be a list')
        for arg in args:
            if arg.is_variable():
                raise DatalogError(GDLError.FACT_VARIABLE, arg.token)
            if arg.is_not() or arg.is_distinct() or arg.is_or():
                raise DatalogError(GDLError.FACT_RESERVED % arg.term, arg.token)
            if arg.arity > 0:
                self._sanity_check_fact_arguments(arg.children)

    ### RULE VALIDATION:

    def _sanity_check_new_rule(self, term, arity, args, body):
        self._check_negative_variables(args, body)
        self._check_negative_cycles(term, arity, body)
        self._check_reserved_rule_arguments(args)

    def _check_negative_variables(self, args, body):
        pos_vars = []
        for sentence in body:
            pos_vars.extend(self._collect_positive_variables(sentence))

        neg_vars = []
        for arg in args:
            neg_vars.extend(self._collect_negative_variables(arg))
        for sentence in body:
            neg_vars.extend(self._collect_negative_variables(sentence))

        for token in neg_vars:
            if token.value not in pos_vars:
                raise DatalogError(GDLError.NEGATIVE_VARIABLE % token.value, token)

    def _collect_positive_variables(self, node):
        if node.is_variable():
            return [node.term]
        if node.is_not() or node.is_distinct():
            return []
        pos_vars = []
        for child in node.children:
            pos_vars.extend(self._collect_positive_variables(child))
        return pos_vars

    def _collect_negative_variables(self, node):
        if node.is_variable():
            return [node.token]
        if not node.is_not() and not node.is_distinct():
            return []
        neg_vars = []
        for child in node.children:
            neg_vars.extend(self._collect_negative_variables(child))
        return neg_vars

    def _check_negative_cycles(self, term, arity, body):
        for sentence in body:
            if self._follow_sentence(sentence, [(term, arity)]):
                raise DatalogError(GDLError.NEGATIVE_CYCLE, sentence.token)

    def _follow_sentence(self, sentence, visited):
        if sentence.is_not():
            pred = sentence.children[0].predicate
            if self._find_neg_cycle(pred, visited + [pred, None]):
                return True
        elif sentence.is_distinct() or sentence.is_or():
            a, b = [x.predicate for x in sentence.children]
            if self._find_neg_cycle(a, visited + [a]) or \
                    self._find_neg_cycle(b, visited + [b]):
                return True
        else:
            pred = sentence.predicate
            if self._find_neg_cycle(pred, visited + [pred]):
                return True
        return False

    def _find_neg_cycle(self, pred, visited):
        if pred == visited[0] and None in visited:
            return True
        if visited[-1] is None:
            if pred in visited[:-2]:
                return False
        elif pred in visited[:-1]:
            return False
        for _, body in self.rules.get(pred, []):
            for sentence in body:
                if self._follow_sentence(sentence, visited):
                    return True
        return False

    def _check_reserved_rule_arguments(self, args):
        for arg in args:
            if arg.is_not() or arg.is_distinct() or arg.is_or():
                raise DatalogError(GDLError.RULE_HEAD_RESERVED % arg.term, arg.token)
            if arg.arity > 0:
                self._check_reserved_rule_arguments(arg.children)
