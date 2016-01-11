import unittest
from gdl.ast import ASTNode


class MockToken(object):
    def __init__(self, filename, line, lineno, col, token):
        self.token = token
        self.filename = filename
        self.line = line
        self.lineno = lineno,
        self.column = col


class TestASTNode(unittest.TestCase):
    def _new_tree(self):
        pred = ASTNode(MockToken(None, None, None, None, '<='))
        legal = ASTNode(MockToken(None, None, None, None, 'legal'), pred)
        legal.create_child(MockToken(None, None, None, None, '?player'))
        legal.create_child(MockToken(None, None, None, None, '?move'))
        true = ASTNode(MockToken(None, None, None, None, 'true'), pred)
        pred.children = [legal, true]
        return pred

    def test_copy(self):
        pred = self._new_tree()
        legal = pred.children[0]
        copy = legal.copy()
        self.assertEqual(copy.term, 'legal')
        self.assertEqual(copy.parent, None)
        legal.children = []
        self.assertEqual([child.term for child in copy.children], ['?player', '?move'])
        self.assertEqual([child.parent for child in copy.children], [copy] * 2)

    def test_eqality(self):
        a = self._new_tree()
        b = self._new_tree()
        self.assertEqual(a, b)

    def test_inequality(self):
        a = self._new_tree()
        b = self._new_tree()
        b.children[0].children[0].token.token = 'player'
        self.assertNotEqual(a, b)
