import unittest
from gdl import Database, DatalogError


class MockToken(object):
    def __init__(self, value):
        self.value = value
        self.filename = 'test.gdl'
        self.line = 'foobar'
        self.lineno = 22
        self.column = 3

    def is_variable(self):
        return self.value[0] == '?'

    def is_distinct(self):
        return self.value == 'distinct'

    def is_rule(self):
        return self.value == '<='

    def is_or(self):
        return self.value == 'or'

    def is_not(self):
        return self.value == 'not'

    def is_constant(self):
        return self.value[0] not in ('?', '(', ')')

    def copy(self):
        return MockToken(self.value)


class MockNode(object):
    def __init__(self, token, children=None):
        self.token = token
        self.children = children if children else []
        self.arity = len(self.children)

    @property
    def term(self):
        return self.token.value

    @property
    def predicate(self):
        return (self.term, self.arity)

    def is_rule(self):
        return self.token.is_rule()

    def is_variable(self):
        return self.token.is_variable()

    def is_constant(self):
        return self.token.is_constant()

    def is_distinct(self):
        return self.token.is_distinct()

    def is_or(self):
        return self.token.is_or()

    def is_not(self):
        return self.token.is_not()

    def copy(self):
        return MockNode(self.token.copy(), [x.copy() for x in self.children])

    def set_variables(self, variable_dict):
        if self.is_variable():
            copy = variable_dict[self.term].copy()
        else:
            copy = MockNode(self.token.copy(), [child.set_variables(variable_dict) \
                    for child in self.children])
        return copy

    def __eq__(self, other):
        if (self.term, self.arity) != (other.term, other.arity):
            return False
        for a, b in zip(self.children, other.children):
            if a != b:
                return False
        return True

    def __repr__(self):
        return self.term


def make_mock_node(token, children=None):
    return MockNode(MockToken(token), children)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database()

        # FACTS
        self.db.define_fact('foo', 3, [make_mock_node(x) for x in ('a', 'b', 'c')])
        self.db.define_fact('foo', 3, [make_mock_node(x) for x in ('x', 'y', 'z')])
        self.db.define_fact('foo', 3, [make_mock_node(x) for x in ('x', 'y', 'x')])
        self.db.define_fact('foo', 3, [make_mock_node(x) for x in ('a', 'a', 'a')])
        self.db.define_fact('bar', 2, [make_mock_node('1'),
            make_mock_node('x', [make_mock_node(x) for x in ('2', '3')])])

        # RULES
        # Datalog 2.5
        # > path(X,Y) :- path(X,Z), link(Z,Y).
        # > path(X,Y) :- link(X,Y).
        # > link(3,4).
        # > link(2,3).
        # > link(1,2).
        path = make_mock_node('path', [make_mock_node(x) for x in ('?x', '?z')])
        link = make_mock_node('link', [make_mock_node(x) for x in ('?z', '?y')])
        self.db.define_rule('path', 2, [make_mock_node(x) for x in ('?x', '?y')], [path, link])
        link = make_mock_node('link', [make_mock_node(x) for x in ('?x', '?y')])
        self.db.define_rule('path', 2, [make_mock_node(x) for x in ('?x', '?y')], [link])
        self.db.define_fact('link', 2, [make_mock_node(x) for x in ('3', '4')])
        self.db.define_fact('link', 2, [make_mock_node(x) for x in ('2', '3')])
        self.db.define_fact('link', 2, [make_mock_node(x) for x in ('1', '2')])

        # NEGATION
        # > x(1). x(2). x(3). x(4).
        # > not_path(X, Y) :- x(X), x(Y), not(path(X, Y)).
        self.db.define_fact('x', 1, [make_mock_node('1')])
        self.db.define_fact('x', 1, [make_mock_node('2')])
        self.db.define_fact('x', 1, [make_mock_node('3')])
        self.db.define_fact('x', 1, [make_mock_node('4')])
        xx = make_mock_node('x', [make_mock_node('?x')])
        xy = make_mock_node('x', [make_mock_node('?y')])
        path = make_mock_node('path', [make_mock_node(x) for x in ('?y', '?x')])
        self.db.define_rule('rpath', 2, [make_mock_node(x) for x in ('?x', '?y')], [xx, xy, path])
        not_path = make_mock_node('not', [make_mock_node('path', [make_mock_node(x) for x in ('?x', '?y')])])
        self.db.define_rule('not-path', 2, [make_mock_node(x) for x in ('?x', '?y')], [xx, xy, not_path])

        # CYCLICAL RECURSION
        # Datalog 2.5
        # > s(1).
        # > s(2).
        # > t(1).
        # > p(X) :- q(X), s(X).
        # > q(X) :- p(X), t(X).
        # > q(X) :- t(X).
        self.db.define_fact('s', 1, [make_mock_node('1')])
        self.db.define_fact('s', 1, [make_mock_node('2')])
        self.db.define_fact('t', 1, [make_mock_node('1')])
        p, q, s, t = [make_mock_node(x, [make_mock_node('?x')]) for x in ('p', 'q', 's', 't')]
        self.db.define_rule('p', 1, [make_mock_node('?x')], [q, s])
        self.db.define_rule('q', 1, [make_mock_node('?x')], [p, t])
        self.db.define_rule('q', 1, [make_mock_node('?x')], [t])

        # DISTINCT
        # (<= (diff ?x ?y) (x ?x) (x ?y) (distinct ?x ?y))
        distinct = make_mock_node('distinct', [make_mock_node('?x'), make_mock_node('?y')])
        xx = make_mock_node('x', [make_mock_node('?x')])
        xy = make_mock_node('x', [make_mock_node('?y')])
        self.db.define_rule('diff', 2, [make_mock_node(x) for x in ('?x', '?y')], [xx, xy, distinct])

        # OR
        # (<= (valid? ?x ?y) (not-path ?x ?y) (or (distinct ?y 4) (distinct ?x 4)))
        d1 = make_mock_node('distinct', [make_mock_node('?y'), make_mock_node('4')])
        d2 = make_mock_node('distinct', [make_mock_node('?x'), make_mock_node('4')])
        or_ = make_mock_node('or', [d1, d2])
        not_path = make_mock_node('not-path', [make_mock_node(x) for x in ('?x', '?y')])
        self.db.define_rule('valid?', 2, [make_mock_node(x) for x in ('?x', '?y')], [not_path, or_])

        # 0-ARITY RULES
        cell = make_mock_node('cell', [make_mock_node(x) for x in ['?m', '?n', 'b']])
        self.db.define_rule('open', 0, [], [make_mock_node('true', [cell])])
        self.db.define_rule('terminal', 0, [], [make_mock_node('not', [make_mock_node('open')])])

    def test_fact_list_error(self):
        with self.assertRaises(TypeError):
            Database().define_fact('foo', 2, (1, 2))

    def test_fact_variable_argument_error(self):
        children = [make_mock_node('x'), make_mock_node('?y')]
        arg = make_mock_node('predicate', children)
        with self.assertRaises(DatalogError):
            Database().define_fact('foo', 1, [arg])

    def test_fact_query_error(self):
        children = [make_mock_node('x'), make_mock_node('?x')]
        node = make_mock_node('foo', children)
        with self.assertRaises(DatalogError):
            self.db.query(node)

    def test_fact_query_success(self):
        args = [make_mock_node(x) for x in ('x', 'y', 'z')]
        foo = make_mock_node('foo', args)
        self.assertTrue(self.db.query(foo))

    def test_fact_query_failure(self):
        args = [make_mock_node(x) for x in ('c', 'b', 'a')]
        foo = make_mock_node('foo', args)
        self.assertFalse(self.db.query(foo))

    def test_fact_query_match(self):
        answer = [{'?b': 'b', '?c': 'c'}, {'?b': 'a', '?c': 'a'}]
        args = [make_mock_node(x) for x in ('a', '?b', '?c')]
        foo = make_mock_node('foo', args)
        results = [{k: d[k].term for k in d} for d in self.db.query(foo)]
        self.assertEqual(answer, results)

    def test_fact_query_match_complex(self):
        answer = make_mock_node('x', [make_mock_node(x) for x in ('2', '3')])
        args = [make_mock_node('1'), make_mock_node('?x')]
        bar = make_mock_node('bar', args)
        results = self.db.query(bar)
        self.assertEqual(results, [{'?x': answer}])

    def test_fact_query_repeat_variables(self):
        answer = [{'?1': 'x', '?2': 'y'}, {'?1': 'a', '?2': 'a'}]
        args = [make_mock_node(x) for x in ('?1', '?2', '?1')]
        foo = make_mock_node('foo', args)
        results = [{k: d[k].term for k in d} for d in self.db.query(foo)]
        self.assertEqual(answer, results)

    # > path(1,4)?
    # path(1, 4).
    def test_rule_success(self):
        query = make_mock_node('path', [make_mock_node('1'), make_mock_node('4')])
        self.assertTrue(self.db.query(query))

    def test_rule_success2(self):
        query = make_mock_node('rpath', [make_mock_node('4'), make_mock_node('1')])
        self.assertTrue(self.db.query(query))

    def test_rule_failure(self):
        query = make_mock_node('path', [make_mock_node('4'), make_mock_node('?x')])
        self.assertFalse(self.db.query(query))

    def test_literal_negation_success(self):
        query = make_mock_node('not-path', [make_mock_node('4'), make_mock_node('1')])
        self.assertTrue(self.db.query(query))

    def test_literal_negation_failure(self):
        query = make_mock_node('not-path', [make_mock_node('1'), make_mock_node('3')])
        self.assertFalse(self.db.query(query))

    # > p(X)?
    # p(1).
    def test_rule_cyclical_recursion(self):
        answer = [{'?x': '1'}]
        query = make_mock_node('p', [make_mock_node('?x')])
        results = [{k: d[k].term for k in d} for d in self.db.query(query)]
        self.assertEqual(results, answer)

    def test_rule_redefinition_deletes_old_facts(self):
        answer = [{'?x': '1'}, {'?x': '2'}]
        query = make_mock_node('p', [make_mock_node('?x')])
        self.db.query(query)
        self.db.define_rule('p', 1,
                [make_mock_node('?x')],
                [make_mock_node('s', [make_mock_node('?x')])])
        results = [{k: d[k].term for k in d} for d in self.db.query(query)]
        self.assertEqual(results, answer)

    def test_distinct(self):
        query = make_mock_node('diff', [make_mock_node('?x'), make_mock_node('?y')])
        results = [{k: d[k].term for k in d} for d in self.db.query(query)]
        self.assertEqual(12, len(results))
        for i in range(1, 5):
            self.assertNotIn({'?x': i, '?y': i}, results)

    def test_or(self):
        query = make_mock_node('valid?', [make_mock_node('?x'), make_mock_node('?y')])
        results = [{k: d[k].term for k in d} for d in self.db.query(query)]
        self.assertNotIn({'?x': 4, '?y': 4}, results)

    def test_negative_variable_error(self):
        distinct = make_mock_node('distinct', [make_mock_node('?x'), make_mock_node('?y')])
        path = make_mock_node('path', [make_mock_node('?z'), make_mock_node('?y')])
        body = [path, distinct]
        with self.assertRaises(DatalogError):
            self.db.define_rule('diff', 2, [make_mock_node('?x'), make_mock_node('?y')], body)

    def test_negative_cycle_error(self):
        # > p_(X) :- q_(X)
        # > r_(X) :- p_(X)
        # > q_(X) :- x_(X), ~r_(X)
        p = make_mock_node('p_', [make_mock_node('?x')])
        q = make_mock_node('q_', [make_mock_node('?x')])
        r = make_mock_node('r_', [make_mock_node('?x')])
        x = make_mock_node('x_', [make_mock_node('?x')])
        self.db.define_rule('p_', 1, [make_mock_node('?x')], [q])
        self.db.define_rule('r_', 1, [make_mock_node('?x')], [p])
        with self.assertRaises(DatalogError):
            self.db.define_rule('q_', 1, [make_mock_node('?x')], [x, make_mock_node('not', [r])])

    def test_reserved_word_in_fact_error(self):
        not4 = make_mock_node('not', [make_mock_node('4')])
        with self.assertRaises(DatalogError):
            self.db.define_fact('x', 1, [not4])

    def test_reserved_word_in_fact_error(self):
        q = make_mock_node('q_', [make_mock_node('?x')])
        with self.assertRaises(DatalogError):
            self.db.define_rule('p_', 1, [make_mock_node('not', [make_mock_node('?x')])], [q])

    def test_define_fact(self):
        fact = make_mock_node('new_fact', [make_mock_node(x) for x in ('1', '2', '3')])
        self.db.define(fact)
        results = self.db.query(make_mock_node('new_fact', [make_mock_node(x) for x in ('?x', '?y', '?z')]))
        results = [{k: d[k].term for k in d} for d in results]
        self.assertEqual(results, [{'?x': '1', '?y': '2', '?z': '3'}])

    def test_define_rule(self):
        distinct = make_mock_node('distinct', [make_mock_node('?x'), make_mock_node('1')])
        x = make_mock_node('x', [make_mock_node('?x')])
        head = make_mock_node('new_rule', [make_mock_node('?x')])
        rule = make_mock_node('<=', [head, x, distinct])
        self.db.define(rule)
        results = self.db.query(make_mock_node('new_rule', [make_mock_node('?x')]))
        results = [{k: d[k].term for k in d} for d in results]
        self.assertEqual(results, [{'?x': '2'}, {'?x': '3'}, {'?x': '4'}])

    def test_0_arity_rules(self):
        self.assertFalse(self.db.query(make_mock_node('open')))
        self.assertTrue(self.db.query(make_mock_node('terminal')))
        cell = make_mock_node('cell', [make_mock_node(x) for x in ('2', '2', 'b')])
        self.db.define_fact('true', 1, [cell])
        self.assertTrue(self.db.query(make_mock_node('open')))
        self.assertFalse(self.db.query(make_mock_node('terminal')))

    def test_evaluate_negative_literals_last(self):
        xx = make_mock_node('x', [make_mock_node('?x')])
        not_s = make_mock_node('not', [make_mock_node('s', [make_mock_node('?x')])])
        head = make_mock_node('not-y', [make_mock_node('?x')])
        rule = make_mock_node('<=', [head, not_s, xx])
        self.db.define(rule)
        results = self.db.query(make_mock_node('not-y', [make_mock_node('?x')]))
        results = [{k: d[k].term for k in d} for d in results]
        self.assertEqual(results, [{'?x': '3'}, {'?x': '4'}])
