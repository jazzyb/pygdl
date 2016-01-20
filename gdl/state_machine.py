from gdl.ast import ASTNode
from gdl.database import Database
from gdl.lexer import Lexer
from gdl.parser import Parser


class GameError(Exception):
    NO_PLAYERS = "Players must be defined with 'role/1'"
    NO_SUCH_PLAYER = "No such player: '%s'"
    DOUBLE_MOVE = "'%s' has already moved this turn"
    ILLEGAL_MOVE = "Not a legal move: '(does %s %s)'"


class StateMachine(object):
    def __init__(self, database=None):
        self.db = database
        self.players = set()
        self.moves = set()

    ## PUBLIC API

    def store(self, **kwargs):
        self.db = self.db or Database()
        tokens = Lexer.run_lex(**kwargs)
        for tree in Parser.run_parse(tokens):
            if tree.is_init():
                tree.token.set(value='true')
            self.db.define(tree)
        try:
            roles = self.db.facts[('role', 1)]
        except KeyError:
            raise GameError(GameError.NO_PLAYERS)
        self.players = set([str(x[0]) for x in roles])

    def move(self, player, move):
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

    # TODO: vvvvvvvvvvvvv  WRITE / TEST  vvvvvvvvvvvvvv

    def next(self):
        # 1. Get list of players ('role')
        # 2. Make sure there is a 'does' for each player
        # 3. Calculate the new 'true' facts by querying for 'next'
        # 4. Copy the database
        # 5. Delete the 'does' and 'true' facts as well as all derived_facts
        # 6. Replace 'true' facts with 'next' facts
        # 7. Return a copy of the engine with new database
        pass

    def score(self, player='?player'):
        # Query 'goal'
        pass

    def legal(self, player='?player', move='?move'):
        move = self._single_move_to_ast(move)
        player = ASTNode.new(player)
        results = self._legal(player, move)
        if results is True or results is False:
            return results
        elif player.is_variable():
            ret = {}
            for var_dict in results:
                move_str = str(var_dict[move.term])
                ret.setdefault(var_dict[player.term].term, []).append(move_str)
            return ret
        return [str(res[move.term]) for res in results]

    def is_terminal(self):
        return self.db.query(ASTNode.new('terminal'))

    ## HELPERS

    def _legal(self, player, move):
        legal = ASTNode.new('legal')
        legal.children = [player, move]
        return self.db.query(legal)

    def _single_move_to_ast(self, move):
        return Parser.run_parse(Lexer.run_lex(data=move))[0]
