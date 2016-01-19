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
    for tree in Parser().parse(tokens):
#        print(tree)
        database.define(tree)

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
            trees = Parser().parse(tokens)
        except ParseError as err:
            print('\nerror: ', err)
            continue
#        print(trees)
#        print('-' * 20)

        if prompt == QUERY:
            assert len(trees) == 1

            try:
                results = database.query(trees[0])
#                print('-' * 20)
#                print(results)
#                print('-' * 20)
            except DatalogError as err:
                print('\nerror: ', err)
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
            for tree in trees:
                try:
                    database.define(tree)
                except DatalogError as err:
                    print('\nerror: ', err)
                    break
                print(tree)

except EOFError:
    print('')
