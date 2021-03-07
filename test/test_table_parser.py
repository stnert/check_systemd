import unittest
from .helper import read_file_as_bytes
from check_systemd import TableParserNg


def read_stdout(file_name: str) -> str:
    return read_file_as_bytes(file_name).decode('utf-8')


class TestTableParser(unittest.TestCase):

    def test_initialization(self):
        parser = TableParserNg(read_stdout('systemctl-list-units_v246.txt'))
        self.assertIn('DESCRIPTION', parser.header_line)
        self.assertIn('systemd-tmpfiles-clean.timer', parser.body_lines[-1])

    def test_detect_column_lengths(self):
        detect = TableParserNg.detect_column_lengths
        self.assertEqual([2, 2], detect('1 2 3'))
        self.assertEqual([2, 2, 2], detect('  1 2 3  '))
