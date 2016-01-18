import re


class NoInputError(Exception):
    pass


class Lexeme(object):
    def __init__(self, filename, line, lineno, col=-1, value=''):
        self.value = value
        self.filename = filename
        self.line = line
        self.lineno = lineno
        self.column = col

    def set(self, filename=None, line=None, lineno=None, column=None, value=None):
        if filename:
            self.filename = filename
        if line:
            self.line = line
        if lineno:
            self.lineno = lineno
        if column:
            self.column = column
        if value:
            self.value = value

    def is_empty(self):
        return self.column == -1 or self.value == ''

    def is_rule(self):
        return self.value == '<='

    def is_open(self):
        return self.value == '('

    def is_close(self):
        return self.value == ')'

    def is_not(self):
        return self.value == 'not'

    def is_distinct(self):
        return self.value == 'distinct'

    def is_or(self):
        return self.value == 'or'

    def is_variable(self):
        return self.value[0] == '?'

    def is_constant(self):
        return self.value[0] not in ('?', '(', ')')

    def copy(self):
        return Lexeme(self.filename, self.line, self.lineno, self.column, self.value)

    def __repr__(self):
        return repr(self.value)


class Lexer(object):
    def __init__(self):
        self.values = []
        self.wsre = re.compile(r'\s')

    def lex(self, data=None, file=None):
        if file is None:
            if data is None:
                raise NoInputError('no input to valueize')
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

        if self.values[-1].is_empty():
            self.values.pop()
        return self.values

    def _lex_line(self, line, row):
        col = 0
        for char in line:
            col += 1
            if char == ';':
                break
            self._process_char(char.lower(), line, row, col)

    def _process_char(self, char, line, row, col):
        last_value = self.values[-1] if self.values else None
        if self._is_whitespace(char):
            if last_value is None or not last_value.is_empty():
                self.values.append(Lexeme(self.filename, line, row))
        elif char == '(' or char == ')':
            if last_value is not None and last_value.is_empty():
                last_value.set(value=char, line=line, lineno=row, column=col)
            else:
                self.values.append(Lexeme(self.filename, line, row, col, char))
            self.values.append(Lexeme(self.filename, line, row))
        else:
            if last_value is None:
                last_value = Lexeme(self.filename, line, row, col)
                self.values.append(last_value)
            if last_value.is_empty():
                last_value.set(line=line, lineno=row, column=col)
            last_value.value += char

    def _is_whitespace(self, char):
        return re.match(self.wsre, char) is not None
