import unittest
from gdl import StateMachine, GameError

# FIXME:  needs fakes or mocks or something else instead
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
        query = ASTNode.new('true')
        query.children = [ASTNode.new('?state')]
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
        query = ASTNode.new('does')
        query.children = [ASTNode.new(x) for x in ('x', '1')]
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
        cell = ASTNode.new('cell')
        cell.children = [ASTNode.new(x) for x in ('1', '1', 'b')]
        query = ASTNode.new('does')
        query.children = [ASTNode.new('x'), cell]
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

    def test_legal_player_and_move_success(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init 1)
        (<= (legal x ?x) (true ?x))
        '''
        fsm.store(data=data)
        self.assertTrue(fsm.legal(player='x', move='1'))

    def test_legal_player_and_move_failure(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init 1)
        (<= (legal x ?x) (true ?x))
        '''
        fsm.store(data=data)
        self.assertFalse(fsm.legal(player='x', move='2'))

    def test_legal_no_such_player(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init 1)
        (<= (legal x ?x) (true ?x))
        '''
        fsm.store(data=data)
        self.assertFalse(fsm.legal(player='o', move='1'))

    def test_legal_player_moves(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (role o)
        (init 1) (init 2) (init 3) (init 4)
        (even 2) (even 4)
        (odd 1) (odd 3)
        (<= (legal x ?x) (true ?x) (even ?x))
        (<= (legal o ?x) (true ?x) (odd ?x))
        '''
        fsm.store(data=data)
        self.assertEqual(['2', '4'], fsm.legal(player='x'))

    def test_legal_all_moves(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (role o)
        (init 1) (init 2) (init 3) (init 4)
        (even 2) (even 4)
        (odd 1) (odd 3)
        (<= (legal x ?x) (true ?x) (even ?x))
        (<= (legal o ?x) (true ?x) (odd ?x))
        '''
        fsm.store(data=data)
        self.assertEqual({'x': ['2', '4'], 'o': ['1', '3']}, fsm.legal())

    def test_is_terminal_success(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init (control x))
        (init (cell x))
        (<= terminal (true (control ?x)) (true (cell ?x)))
        '''
        fsm.store(data=data)
        self.assertTrue(fsm.is_terminal())

    def test_is_terminal_failure(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init (control x))
        (init (cell o))
        (<= terminal (true (control ?x)) (true (cell ?x)))
        '''
        fsm.store(data=data)
        self.assertFalse(fsm.is_terminal())

    def test_score_player(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init (control x))
        (<= (goal ?player 100) (true (control ?player)))
        '''
        fsm.store(data=data)
        self.assertEqual(100, fsm.score('x'))

    def test_score_no_such_player_error(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (init (control x))
        (<= (goal ?player 100) (true (control ?player)))
        '''
        fsm.store(data=data)
        with self.assertRaises(GameError):
            fsm.score('o')

    def test_score_all_players(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (role o)
        (init (control x))
        (enemies x o) (enemies o x)
        (<= (goal ?player 100) (true (control ?player)))
        (<= (goal ?player 0) (true (control ?other)) (enemies ?player ?other))
        '''
        fsm.store(data=data)
        self.assertEqual({'x': 100, 'o': 0}, fsm.score())
