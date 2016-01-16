import re


class NoInputError(Exception):
    pass


class Lexeme(object):
    def __init__(self, filename, line, lineno, col=-1, token=''):
        self.token = token
        self.filename = filename
        self.line = line
        self.lineno = lineno
        self.column = col

    def set(self, filename=None, line=None, lineno=None, column=None, token=None):
        if filename:
            self.filename = filename
        if line:
            self.line = line
        if lineno:
            self.lineno = lineno
        if column:
            self.column = column
        if token:
            self.token = token

    def is_empty(self):
        return self.column == -1 or self.token == ''

    def is_open(self):
        return self.token == '('

    def is_close(self):
        return self.token == ')'

    def is_variable(self):
        return self.token[0] == '?'

    def is_constant(self):
        return self.token[0] not in ('?', '(', ')')

    def copy(self):
        return Lexeme(self.filename, self.line, self.lineno, self.column, self.token)


class Lexer(object):
    def __init__(self):
        self.tokens = []
        self.wsre = re.compile(r'\s')

    def lex(self, data=None, file=None):
        if file is None:
            if data is None:
                raise NoInputError('no input to tokenize')
            self.lines = data.splitlines(True)
            self.filename = None
        else:
            self.lines = file
            self.filename = file.name

        return self._lex_input()

    def _lex_input(self):
        row = 0
        for line in self.lines:
            row += 1
            self._lex_line(line, row)

        if self.tokens[-1].is_empty():
            self.tokens.pop()
        return self.tokens

    def _lex_line(self, line, row):
        col = 0
        for char in line:
            col += 1
            if char == ';':
                break
            self._process_char(char.lower(), line, row, col)

    def _process_char(self, char, line, row, col):
        last_token = self.tokens[-1] if self.tokens else None
        if self._is_whitespace(char):
            if last_token is None or not last_token.is_empty():
                self.tokens.append(Lexeme(self.filename, line, row))
        elif char == '(' or char == ')':
            if last_token is not None and last_token.is_empty():
                last_token.set(token=char, line=line, lineno=row, column=col)
            else:
                self.tokens.append(Lexeme(self.filename, line, row, col, char))
            self.tokens.append(Lexeme(self.filename, line, row))
        else:
            if last_token is None:
                last_token = Lexeme(self.filename, line, row, col)
                self.tokens.append(last_token)
            if last_token.is_empty():
                last_token.set(line=line, lineno=row, column=col)
            last_token.token += char

    def _is_whitespace(self, char):
        return re.match(self.wsre, char) is not None
