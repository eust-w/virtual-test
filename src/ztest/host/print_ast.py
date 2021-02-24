import ast
from utils import json


node = ast.parse(open('/home/frank/pythonProject/m2.py', 'r').read())
print ast.dump(node)
print json.dumps(node)


