import unittest
from .helper import read_file_as_bytes
from check_systemd import TableParserNg


def read_stdout(file_name: str) -> str:
    return read_file_as_bytes(file_name).decode('utf-8')


def get_parser():
    return TableParserNg(read_stdout('systemctl-list-units_v246.txt'))


class TestTableParser(unittest.TestCase):

    def test_initialization(self):
        parser = get_parser()
        self.assertIn('description', parser.header_row)
        self.assertIn('systemd-tmpfiles-clean.timer', parser.body_rows[-1])
        self.assertEquals([2, 111, 10, 9, 10], parser.column_lengths)

        self.assertEquals(['', 'unit', 'load', 'active',
                           'sub', 'description'], parser.columns)

    def test_normalize_header_line(self):
        normalize = TableParserNg._TableParserNg__normalize_header
        self.assertEqual('unit_one  unit_two', normalize('UNIT ONE  UNIT TWO'))

    def test_detect_column_lengths(self):
        detect = TableParserNg._TableParserNg__detect_lengths
        self.assertEqual([3, 3], detect('1  2  3'))
        self.assertEqual([2, 3, 3], detect('  1  2  3  '))
        self.assertEqual([2, 5, 5], detect('  1 1  2 2  3 3  '))

    def test_split_line_into_columns(self):
        split = TableParserNg._TableParserNg__split_row
        self.assertEqual(['123', '456', '789'], split('123456789', [3, 3]))
        self.assertEqual(['UNIT', 'STATE', 'LOAD'],
                         split('UNIT  STATE  LOAD  ', [6, 7]))

    def test_get_row(self):
        parser = get_parser()
        row = parser.get_row(0)
        self.assertEqual('', row['column_0'])
        self.assertEqual('dev-block-254:0.device', row['unit'])
        self.assertEqual('loaded', row['load'])
        self.assertEqual('active', row['active'])
        self.assertEqual('plugged', row['sub'])
        self.assertEqual('/dev/block/254:0', row['description'])

    def test_get_row_all(self):
        parser = get_parser()
        row = parser.row_count
        for i in range(0, parser.row_count):
            row = parser.get_row(i)
        self.assertEqual('systemd-tmpfiles-clean.timer', row['unit'])


if __name__ == '__main__':
    unittest.main()
