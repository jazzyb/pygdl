import os, sys
curr_dir = os.path.dirname(os.path.realpath(__file__))
gdl_path = os.path.abspath(os.path.join(curr_dir, os.pardir))
sys.path.append(gdl_path)

from gdl import Lexer, Parser, Database, DatalogError, ParseError

DEFINE = 'GDL> '
QUERY = 'GDL? '
prompt = DEFINE
database = Database()

for filename in sys.argv[1:]:
    # read in any files from the command line
    with open(filename, 'r') as file:
        tokens = Lexer().lex(file=file)
    for lit in Parser().parse(tokens).children:
#        print(lit)
        if lit.term == '<=':
            head, body = lit.children[0], lit.children[1:]
            database.define_rule(head.term, head.arity, head.children, body)
        else:
            database.define_fact(lit.term, lit.arity, lit.children)

try:
    # interactive loop
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

#        print('-' * 20)
#        print(raw_string)
        tokens = Lexer().lex(raw_string)
#        print(tokens)
        try:
            tree = Parser().parse(tokens)
        except ParseError as err:
            print('error: ', err)
            continue
#        print(tree)
#        print('-' * 20)

        if prompt == QUERY:
            assert tree.arity == 1

            try:
                results = database.query(tree.children[0])
#                print('-' * 20)
#                print(results)
#                print('-' * 20)
            except DatalogError as err:
                print('error: ', err)
                continue

            if type(results) == list:
                output = ''
                for match in results:
                    new_string = raw_string.lower()
                    for key in match:
                        new_string = new_string.replace(key, repr(match[key]))
                    output += new_string + '\n'
                print(output)
            else:
                print(results)

        else:
            print(tree)
            for lit in tree.children:
                try:
                    if lit.term == '<=':
                        head, body = lit.children[0], lit.children[1:]
                        database.define_rule(head.term, head.arity, head.children, body)
                    else:
                        database.define_fact(lit.term, lit.arity, lit.children)
                except DatalogError as err:
                    print('error: ', err)
                    break

except EOFError:
    print('')
