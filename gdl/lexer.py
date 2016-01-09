import re


class NoInputError(Exception):
    pass


class Lexeme(object):
    def __init__(self, filename, line, col=-1, token=''):
        self.token = token
        self.filename = filename
        self.lineno = line
        self.column = col

    def is_empty(self):
        return self.column == -1 or self.token == ''


class Lexer(object):
    def __init__(self, fp=None):
        self.fp = fp
        self.tokens = []
        self.wsre = re.compile(r'\s')

    def parse(self, data=None):
        if self.fp is None:
            if data is None:
                raise NoInputError('no input to tokenize')
            self.lines = data.splitlines(True)
            self.filename = None
        else:
            self.lines = self.fp
            self.filename = self.fp.name

        return self._parse_input()

    def _parse_input(self):
        row = 0
        for line in self.lines:
            row += 1
            self._parse_line(line, row)

        if self.tokens[-1].is_empty():
            self.tokens.pop()
        return self.tokens

    def _parse_line(self, line, row):
        col = 0
        for char in line:
            col += 1
            self._process_char(char, row, col)

    def _process_char(self, char, row, col):
        last_token = self.tokens[-1] if self.tokens else None
        if self._is_whitespace(char):
            if last_token is None or not last_token.is_empty():
                self.tokens.append(Lexeme(self.filename, row))
        elif char == '(' or char == ')':
            if last_token is not None and last_token.is_empty():
                last_token.token = char
                last_token.lineno = row
                last_token.column = col
            else:
                self.tokens.append(Lexeme(self.filename, row, col, char))
            self.tokens.append(Lexeme(self.filename, row))
        else:
            if last_token is None:
                last_token = Lexeme(self.filename, row, col)
                self.tokens.append(last_token)
            if last_token.is_empty():
                last_token.lineno = row
                last_token.column = col
            last_token.token += char

    def _is_whitespace(self, char):
        return re.match(self.wsre, char) is not None
