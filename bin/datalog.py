import os, sys
curr_dir = os.path.dirname(os.path.realpath(__file__))
gdl_path = os.path.abspath(os.path.join(curr_dir, os.pardir))
sys.path.append(gdl_path)

from gdl import Lexer, Parser, Database, DatalogError, ParseError

DEFINE = 'GDL> '
QUERY = 'GDL? '
prompt = DEFINE
database = Database()

try:
    while 1:
        raw_string = input(prompt).strip()
        if raw_string == '?':
            prompt = QUERY
            continue
        elif raw_string == '.':
            prompt = DEFINE
            continue
        elif not raw_string:
            continue

        tokens = Lexer().lex(raw_string)
        try:
            tree = Parser().parse(tokens)
        except ParseError as err:
            print('error: ', err)
            continue

        if prompt == QUERY:
            assert tree.arity == 1

            try:
                results = database.query(tree.children[0])
            except DatalogError as err:
                print('error: ', err)
                continue

            if type(results) == list:
                output = ''
                for match in results:
                    for key in match:
                        output += raw_string.lower().replace(key, repr(match[key]))
                    output += '\n'
                print(output)
            else:
                print(results)

        else:
            print(tree)
            for lit in tree.children:
                if lit.term == '<=':
                    head, body = lit.children[0], lit.children[1:]
                    database.define_rule(head.term, head.arity, head.children, body)
                else:
                    database.define_fact(lit.term, lit.arity, lit.children)

except EOFError:
    print('')
