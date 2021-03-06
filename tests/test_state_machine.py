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

    def test_store_true_error(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (role o)
        (true (cell a))
        (true (cell b))
        (true (cell c))
        (true (cell d))
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

    def test_score_player_false(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (role o)
        (init (control x))
        (<= (goal ?player 100) (true (control ?player)))
        '''
        fsm.store(data=data)
        self.assertEqual(None, fsm.score('o'))

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

    def test_next(self):
        fsm = StateMachine()
        data = '''
        (role x)
        (role o)
        (init (control x))
        (init (cell 0 0 b))
        (init (cell 0 1 b))
        (init (cell 1 0 b))
        (init (cell 1 1 b))

        (<= (legal ?player (mark ?x ?y))
            (true (cell ?x ?y b))
            (true (control ?player)))
        (<= (legal x noop) (true (control o)))
        (<= (legal o noop) (true (control x)))

        ; swap control on every turn
        (<= (next (control x)) (true (control o)))
        (<= (next (control o)) (true (control x)))

        (<= (next (cell ?x ?y ?player))
            (does ?player (mark ?x ?y))
            (true (cell ?x ?y b)))

        (<= (next (cell ?x ?y b))
            (does ?player (mark ?m ?n))
            (true (cell ?x ?y b))
            (or (distinct ?m ?x) (distinct ?n ?y)))
        '''
        fsm.store(data=data)
        fsm.move('x', '(mark 0 0)')
        fsm.move('o', 'noop')
        next = fsm.next()
        fsm.db.facts = {}
        states = [str(x[0]) for x in next.db.facts[('true', 1)]]
        self.assertIn('(cell 0 0 x)', states)
        self.assertIn('(control o)', states)
        self.assertNotIn(('does', 2), next.db.facts)

    def test_next_no_moves_error(self):
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
        with self.assertRaises(GameError):
            fsm.next()

    def test_hash(self):
        one = StateMachine()
        data = '''
        (role x)
        (role o)
        (init (cell a))
        (init (cell b))
        (init (cell c))
        (init (control x))
        '''
        one.store(data=data)

        two = StateMachine()
        data = '''
        (role x)
        (role o)
        (init (cell b))
        (init (cell a))
        (init (control x))
        (init (cell c))
        '''
        two.store(data=data)
        self.assertEqual(hash(one), hash(two))

        three = StateMachine()
        data = '''
        (role x)
        (role o)
        (init (cell b))
        (init (cell a))
        (init (control o))
        (init (cell c))
        '''
        three.store(data=data)
        self.assertNotEqual(hash(two), hash(three))
