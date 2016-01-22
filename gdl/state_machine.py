from gdl.ast import ASTNode
from gdl.database import Database
from gdl.lexer import Lexer
from gdl.parser import Parser


class GameError(Exception):
    NO_PLAYERS = "Players must be defined with 'role/1'"
    NO_SUCH_PLAYER = "No such player: '%s'"
    DOUBLE_MOVE = "'%s' has already moved this turn"
    ILLEGAL_MOVE = "Not a legal move: '(does %s %s)'"
    NO_TRUE_ALLOWED = "'true' facts are not allowed.  Use 'init/1' instead."
    NO_MOVES = 'The following players have not moved: %s.'


class StateMachine(object):
    def __init__(self, database=None):
        '''Create a new state machine.'''
        self.db = database
        self.players = set()
        self.moves = set()

    ## PUBLIC API

    def store(self, **kwargs):
        '''Read GDL rules into the datalog database.'''
        self.db = self.db or Database()
        tokens = Lexer.run_lex(**kwargs)
        for tree in Parser.run_parse(tokens):
            if tree.is_true():
                raise GameError(GameError.NO_TRUE_ALLOWED)
            elif tree.is_init():
                true = tree.copy()
                true.token.set(value='true')
                self.db.define(true)
            self.db.define(tree)
        try:
            roles = self.db.facts[('role', 1)]
        except KeyError:
            raise GameError(GameError.NO_PLAYERS)
        self.players = set([str(x[0]) for x in roles])

    def move(self, player, move):
        '''Store a does/2 fact in the database representing a player's move.'''
        if player not in self.players:
            raise GameError(GameError.NO_SUCH_PLAYER % player)
        if player in self.moves:
            raise GameError(GameError.DOUBLE_MOVE % player)
        move = self._single_move_to_ast(move)
        player = ASTNode.new(player)
        if not self._legal(player, move):
            raise GameError(GameError.ILLEGAL_MOVE % (player, move))
        self.db.define_fact('does', 2, [player, move])
        self.moves.add(player.term)

    def next(self):
        '''Apply player moves and update game state.

        Return a new StateMachine representing the new turn.
        '''
        if self.players != self.moves:
            players = ', '.join(self.players - self.moves)
            raise GameError(GameError.NO_MOVES % players)

        # calculate the new 'true' facts by querying for 'next'
        state = ASTNode.new('?state')
        next_query = ASTNode.new('next')
        next_query.children = [state]
        next_facts = [d[state.term] for d in self.db.query(next_query)]

        new_db = self.db.copy()
        # delete the 'does', 'true', and derived facts
        new_db.derived_facts = {}
        new_db.facts.pop(('true', 1))
        new_db.facts.pop(('does', 2))

        # replace 'true' facts with 'next' facts
        for fact in next_facts:
            new_db.define_fact('true', 1, [fact])

        next = StateMachine(new_db)
        next.players = self.players
        return next

    def score(self, player='?player'):
        '''Return the score for a player this turn.  If player is not
        provided, return a dict of all {player: score}.
        '''
        player = ASTNode.new(player)
        if not player.is_variable() and player.term not in self.players:
            raise GameError(GameError.NO_SUCH_PLAYER % player.term)
        score = ASTNode.new('?score')
        goal = ASTNode.new('goal')
        goal.children = [player, score]
        results = self.db.query(goal)
        if not player.is_variable():
            return int(results[0][score.term].term)
        ret = {}
        for var_dict in results:
            ret[var_dict[player.term].term] = int(var_dict[score.term].term)
        return ret

    def legal(self, player='?player', move='?move'):
        '''If player and move are provided, return whether or not the move is
        legal this turn.

        If move is not provided, get a list of legal moves for player.

        If neither is provided, return a dict of moves for all players where
        player names are keys.
        '''
        move = self._single_move_to_ast(move)
        player = ASTNode.new(player)
        results = self._legal(player, move)
        if type(results) is bool:
            return results
        elif not player.is_variable():
            return [str(res[move.term]) for res in results]
        ret = {}
        for var_dict in results:
            move_str = str(var_dict[move.term])
            ret.setdefault(var_dict[player.term].term, []).append(move_str)
        return ret

    def is_terminal(self):
        '''Query terminal/0.'''
        return self.db.query(ASTNode.new('terminal'))

    ## HELPERS

    def _legal(self, player, move):
        '''Query legal/2.  Arguments player and move are ASTNodes.'''
        legal = ASTNode.new('legal')
        legal.children = [player, move]
        return self.db.query(legal)

    def _single_move_to_ast(self, move):
        '''Converts the move string to an ASTNode.'''
        return Parser.run_parse(Lexer.run_lex(data=move))[0]
