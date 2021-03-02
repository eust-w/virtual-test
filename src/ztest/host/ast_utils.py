import ast
import astunparse
import traceback
import tokenize
import StringIO
from utils.error import ZTestError


class AstVisitor(ast.NodeVisitor):
    def generic_visit(self, node):
        return super(AstVisitor, self).generic_visit(node)


class ParseEnvSetup(object):
    ENV_SETUP = '__ENV_SETUP__'

    def __init__(self, case_file_path):
        self.case_file_path = case_file_path

        with open(case_file_path, 'r') as fd:
            try:
                self.tree = ast.parse(fd.read())
            except SyntaxError:
                content = traceback.format_exc()
                raise ZTestError('syntax error in file: %s\n%s' % (case_file_path, content))

    def _is_env_setup_node(self, node):
        return len(filter(lambda n: n.id == self.ENV_SETUP, node.targets)) != 0

    def _find_env_setup_assign(self):
        nodes = []

        for node in self.tree.body:
            if not isinstance(node, ast.Assign):
                continue

            if self._is_env_setup_node(node):
                nodes.append(node)

        if not nodes:
            return None

        if len(nodes) > 1:
            errors = ['line %s:%s %s' % (n.lineno, n.col_offset, astunparse.unparse(n)) for n in nodes]
            raise ZTestError('multiple %s definitions found in file: %s:\n%s' % (self.ENV_SETUP, self.case_file_path, '\n'.join(errors)))

        return nodes[0]

    def parse(self):
        node = self._find_env_setup_assign()
        if node is None:
            return None

        code = astunparse.unparse(node)
        context = {}
        exec(code, context)

        return context[self.ENV_SETUP]


def parse_env_setup(case_file_path):
    # type: (str) -> typing.Union[None, dict]

    return ParseEnvSetup(case_file_path).parse()


class ZHints(object):
    def __init__(self, comment):
        self.comment = comment  # type: str
        self.hints = {}

        body = self.comment.split(':')[1]
        lst = body.split(',')
        for l in lst:
            l = l.strip('\t\r\n ')
            if '=' in l:
                k, v = l.split('=', 2)
                self.hints[k.strip('\t\r\n ')] = v.strip('\t\r\n ')
            else:
                self.hints[l] = None


class ZHintsParser(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.lines = None
        self.results = []

    def _parse(self, str_io, line_num):
        code = []
        comment = None

        for toktype, tokval, begin, end, line in tokenize.generate_tokens(str_io):
            if toktype == tokenize.COMMENT:
                comment = tokval
            else:
                code.append((toktype, tokval, begin, end, line))

        if comment is not None and comment.lstrip('\t\r\n #').startswith('zhints:'):
            self.results.append((comment, tokenize.untokenize(code).strip(' \t\r\n'), line_num))

    def parse(self):
        with open(self.file_path, 'r') as fd:
            self.lines = fd.readlines()

        for idx, line in enumerate(self.lines, start=1):
            str_io = StringIO.StringIO(line).readline
            try:
                self._parse(str_io, idx)
            except tokenize.TokenError:
                # not single line statement code
                pass

        return self.results


class HandlerInfo(object):
    def __init__(self, handler, file_path, line_num):
        self.file_path = file_path
        self.line_num = line_num
        self.handler = handler


def collect_agent_handler_in_file(file_path):
    parser = ZHintsParser(file_path)
    res = parser.parse()

    handlers = {}

    for comment, code, line_num in res:
        hints = ZHints(comment)
        if 'handler' not in hints.hints:
            continue

        try:
            node = ast.parse(code)
        except SyntaxError as e:
            raise SyntaxError('handler hints can only be on an assign statement, e.g. CONNECT_PATH = "/host/connect", but get: '
                              '%s (%s:%s), %s' % (code, file_path, line_num, e))

        if len(node.body) != 1 or not isinstance(node.body[0], ast.Assign):
            raise SyntaxError('handler hints can only be on an assign statement, e.g. CONNECT_PATH = "/host/connect", but get: '
                              '%s: %s (%s:%s)' % (ast.dump(node), code, file_path, line_num))

        expr = node.body[0]
        h = expr.value.s
        handlers[h] = HandlerInfo(h, file_path, line_num)

    return handlers





