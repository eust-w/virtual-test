import ast
import astunparse
import traceback
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
            return

        code = astunparse.unparse(node)
        context = {}
        exec(code, context)

        return context[self.ENV_SETUP]


def parse_env_setup(case_file_path):
    # type: (str) -> None

    return ParseEnvSetup(case_file_path).parse()


