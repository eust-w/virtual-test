from unittest import TestCase
import mocking

mocking.start()


class TestMock(TestCase):

    def test_mock_open(self):
        with open('some_file', 'w+') as fd:
            fd.write('hello')


