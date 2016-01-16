import unittest
from gdl import Database, DatalogError


class MockToken(object):
    def __init__(self, token):
        self.token = token
        self.filename = 'test.gdl'
        self.line = 'foobar'
        self.lineno = 22
        self.column = 3

    def is_variable(self):
        return self.token[0] == '?'

    def copy(self):
        return MockToken(self.token)


class MockNode(object):
    def __init__(self, token, children=None):
        self.token = token
        self.children = children if children else []
        self.arity = len(self.children)

    @property
    def term(self):
        return self.token.token

    def is_variable(self):
        return self.token.is_variable()

    def copy(self):
        return MockNode(self.token.copy(), [x.copy() for x in self.children])

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

    def test_rule_failure(self):
        query = make_mock_node('path', [make_mock_node('4'), make_mock_node('?x')])
        self.assertFalse(self.db.query(query))

    # > p(X)?
    # p(1).
    def test_rule_cyclical_recursion(self):
        answer = [{'?x': '1'}]
        query = make_mock_node('p', [make_mock_node('?x')])
        results = [{k: d[k].term for k in d} for d in self.db.query(query)]
        self.assertEqual(results, answer)
