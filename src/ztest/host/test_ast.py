import ast_utils
import functools


print ast_utils.parse_env_setup('/home/frank/test1.py')


def for_handler(handler_name):
    def wrap(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            return f(*args, **kwargs)

        return inner

    return wrap


@for_handler(handler_name='this is handler')
def greeting(txt):
    print txt


greeting('hello world')


