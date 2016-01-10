import unittest
import io
from gdl import Lexer, NoInputError


class MockFile(io.StringIO):
    name = '__mock__'


class TestLexer(unittest.TestCase):
    def test_lex_tokens(self):
        answer = ['(', '<=', '(', 'ancestor', '?a', '?c', ')', '(', 'parent', '?a', '?b', ')', '(', 'ancestor', '?b', '?c', ')', ')']
        string = '(<= (ancestor ?a ?c) (parent ?a ?b) (ancestor ?b ?c))'
        tokens = list(t.token for t in Lexer().lex(string))
        self.assertEqual(tokens, answer)

    def test_lex_superflouos_whitespace(self):
        answer = ['(', '<=', '(', 'ancestor', '?a', '?c', ')', '(', 'parent', '?a', '?b', ')', '(', 'ancestor', '?b', '?c', ')', ')']
        string = '''    
        (  <=  (ancestor   ?a  ?c    )                 (
                parent   ?a  ?b
        ) (
                ancestor ?b                ?c  )   )     
        '''
        tokens = list(t.token for t in Lexer().lex(string))
        self.assertEqual(tokens, answer)

    def test_lex_columns(self):
        answer = [1, 2, 5, 6, 15, 18, 20, 22, 23, 30, 33, 35, 37, 38, 47, 50, 52, 53]
        string = '(<= (ancestor ?a ?c) (parent ?a ?b) (ancestor ?b ?c))'
        columns = list(t.column for t in Lexer().lex(string))
        self.assertEqual(columns, answer)

    def test_lex_linenos(self):
        answer = [1] * 7 + [2] * 5 + [3] * 6
        string = '''(<= (ancestor ?a ?c)
                        (parent ?a ?b)
                        (ancestor ?b ?c))
                 '''
        linenos = list(t.lineno for t in Lexer().lex(string))
        self.assertEqual(linenos, answer)

    def test_lex_lines(self):
        answer = ['(<= (ancestor ?a ?c)\n'] * 7 + \
                 ['                        (parent ?a ?b)\n'] * 5 + \
                 ['                        (ancestor ?b ?c))\n'] * 6
        string = '''(<= (ancestor ?a ?c)
                        (parent ?a ?b)
                        (ancestor ?b ?c))
                 '''
        lines = list(t.line for t in Lexer().lex(string))
        self.assertEqual(lines, answer)

    def test_lex_file(self):
        answer = [('(', 1, 1),
                  ('<=', 1, 2),
                  ('(', 1, 5),
                  ('ancestor', 1, 6),
                  ('?a', 1, 15),
                  ('?c', 1, 18),
                  (')', 1, 20),
                  ('(', 2, 30),
                  ('parent', 2, 31),
                  ('?a', 2, 38),
                  ('?b', 2, 41),
                  (')', 2, 43),
                  ('(', 3, 30),
                  ('ancestor', 3, 31),
                  ('?b', 3, 40),
                  ('?c', 3, 43),
                  (')', 3, 45),
                  (')', 3, 46)]
        fp = MockFile('''(<= (ancestor ?a ?c)
                             (parent ?a ?b)
                             (ancestor ?b ?c))
                 ''')
        tokens = list((t.token, t.lineno, t.column) for t in Lexer(fp).lex())
        self.assertEqual(tokens, answer)

    def test_lex_no_input_error(self):
        with self.assertRaises(NoInputError):
            Lexer().lex()

    def test_lex_case_insensitive(self):
        answer = ['(', '<=', '(', 'ancestor', '?a', '?c', ')', '(', 'parent', '?a', '?b', ')', '(', 'ancestor', '?b', '?c', ')', ')']
        string = '(<= (ANCESTOR ?A ?C) (PARENT ?A ?B) (ANCESTOR ?B ?C))'
        tokens = list(t.token for t in Lexer().lex(string))
        self.assertEqual(tokens, answer)

    def test_lex_comments(self):
        answer = ['(', '<=', '(', 'ancestor', '?a', '?c', ')', '(', 'parent', '?a', '?b', ')', '(', 'ancestor', '?b', '?c', ')', ')']
        string = '''(<= (ancestor ?a ?c)
                        ;;; doc string goes here ;;;
                        (parent ?a ?b)
                        (ancestor ?b ?c)) ;NOTE: this is recursive'''
        tokens = list(t.token for t in Lexer().lex(string))
        self.assertEqual(tokens, answer)
