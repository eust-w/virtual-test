import ast
from utils import json
import tokenize
import StringIO
import ast_utils


# node = ast.parse(open('/home/frank/pythonProject/m2.py', 'r').read())
# print ast.dump(node)
# print json.dumps(node)

# code = 'HTTP_SERVER = "/path" # hints: type=true'
# readline = StringIO.StringIO(code).readline
#
# for toktype, tokval, begin, end, line in tokenize.generate_tokens(readline):
#     if toktype == tokenize.COMMENT:
#         print tokval

print ast_utils.ZHintsParser('/home/frank/pythonProject/m2.py').parse()

