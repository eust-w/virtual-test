import ast_utils
import functools
import ast
from utils import json

#
# print ast_utils.parse_env_setup('/home/frank/test1.py')
#
#
# def for_handler(handler_name):
#     def wrap(f):
#         @functools.wraps(f)
#         def inner(*args, **kwargs):
#             return f(*args, **kwargs)
#
#         return inner
#
#     return wrap
#
#
# @for_handler(handler_name='this is handler')
# def greeting(txt):
#     print txt
#
#
# greeting('hello world')


node = ast.parse(open('/home/frank/pythonProject/m3.py', 'r').read())
print ast.dump(node)
print json.dumps(node)




