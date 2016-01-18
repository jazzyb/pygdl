import unittest
from gdl.ast import ASTNode


class MockToken(object):
    def __init__(self, filename, line, lineno, col, value):
        self.value = value
        self.filename = filename
        self.line = line
        self.lineno = lineno,
        self.column = col

    def copy(self):
        return MockToken(self.filename, self.line, self.lineno, self.column, self.value)


class TestASTNode(unittest.TestCase):
    def _new_tree(self):
        pred = ASTNode(MockToken(None, None, None, None, '<='))
        legal = ASTNode(MockToken(None, None, None, None, 'legal'))
        legal.create_child(MockToken(None, None, None, None, '?player'))
        legal.create_child(MockToken(None, None, None, None, '?move'))
        true = ASTNode(MockToken(None, None, None, None, 'true'))
        pred.children = [legal, true]
        return pred

    def test_copy(self):
        pred = self._new_tree()
        legal = pred.children[0]
        copy = legal.copy()
        self.assertEqual(copy.term, 'legal')
        legal.children = []
        self.assertEqual([child.term for child in copy.children], ['?player', '?move'])
        legal.token.token = 'foo'
        self.assertEqual(copy.term, 'legal')

    def test_eqality(self):
        a = self._new_tree()
        b = self._new_tree()
        self.assertEqual(a, b)

    def test_inequality(self):
        a = self._new_tree()
        b = self._new_tree()
        b.children[0].children[0].token.value = 'player'
        self.assertNotEqual(a, b)
