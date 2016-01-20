import unittest
from gdl import StateMachine, GameError

# FIXME:  needs fakes or mocks or something else instead
from gdl.lexer import Lexeme
from gdl.ast import ASTNode


class TestStateMachine(unittest.TestCase):
    def test_store_init(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (role o)
        (init (cell a))
        (init (cell b))
        (init (cell c))
        (init (cell d))
        '''
        fsm.store(data=data)
        query = ASTNode(Lexeme.new('true'))
        query.children = [ASTNode(Lexeme.new('?state'))]
        results = [{k: str(d[k]) for k in d} for d in fsm.db.query(query)]
        for i in ('a', 'b', 'c', 'd'):
            self.assertIn({'?state': '(cell %s)' % i}, results)

    def test_store_roles(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (role o)
        (init (cell a))
        (init (cell b))
        (init (cell c))
        (init (cell d))
        '''
        fsm.store(data=data)
        self.assertEqual(set(['x', 'o']), fsm.players)

    def test_store_no_roles_error(self):
        fsm = StateMachine()
        data = '''
        (init (cell a))
        (init (cell b))
        (init (cell c))
        (init (cell d))
        '''
        with self.assertRaises(GameError):
            fsm.store(data=data)

    def test_move_player(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init 1)
        (<= (legal x ?x) (true ?x))
        '''
        fsm.store(data=data)
        fsm.move('x', '1')
        query = ASTNode(Lexeme.new('does'))
        query.children = [ASTNode(Lexeme.new(x)) for x in ('x', '1')]
        self.assertTrue(fsm.db.query(query))

    def test_move_player_complex(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init (cell 1 1 b))
        (<= (legal x ?x) (true ?x))
        '''
        fsm.store(data=data)
        fsm.move('x', '(cell 1 1 b)')
        cell = ASTNode(Lexeme.new('cell'))
        cell.children = [ASTNode(Lexeme.new(x)) for x in ('1', '1', 'b')]
        query = ASTNode(Lexeme.new('does'))
        query.children = [ASTNode(Lexeme.new('x')), cell]
        self.assertTrue(fsm.db.query(query))

    def test_move_nonexistent_player_error(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init (cell 1 1 b))
        (<= (legal x ?x) (true ?x))
        '''
        fsm.store(data=data)
        with self.assertRaises(GameError):
            fsm.move('o', '(cell 1 1 b)')

    def test_move_player_twice_error(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init (cell 1 1 b))
        (<= (legal x ?x) (true ?x))
        '''
        fsm.store(data=data)
        fsm.move('x', '(cell 1 1 b)')
        with self.assertRaises(GameError):
            fsm.move('x', '(cell 2 2 b)')

    def test_move_illegal_error(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init 1)
        (<= (legal x ?x) (true ?x))
        '''
        fsm.store(data=data)
        with self.assertRaises(GameError):
            fsm.move('x', '2')
