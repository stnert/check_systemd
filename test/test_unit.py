import unittest
import check_systemd
from check_systemd import TableParser


class TestUnit(unittest.TestCase):

    def test_function_format_timespan_to_seconds(self):
        _to_sec = check_systemd.format_timespan_to_seconds
        self.assertEqual(_to_sec('1s'), 1)
        self.assertEqual(_to_sec('1s ago'), 1)
        self.assertEqual(_to_sec('11s'), 11)
        self.assertEqual(_to_sec('1min 1s'), 61)
        self.assertEqual(_to_sec('1min 1.123s'), 61.123)
        self.assertEqual(_to_sec('1min 2.15s'), 62.15)
        self.assertEqual(_to_sec('34min 46.292s'), 2086.292)
        self.assertEqual(_to_sec('2 months 8 days'), 5875200)


class TestTableParser(unittest.TestCase):

    def setUp(self):
        self.heading = 'UNIT LOAD     ACTIVE   SUB DESCRIPTION'
        self.row = 'unit+load+1234active   sub+description'
        self.parser = TableParser(self.heading)

    def assert_column(self, column_title, result):
        self.assertEqual(self.parser.get_column_text(self.row, column_title),
                         result)

    def test_get_column_text_unit(self):
        self.assert_column('UNIT', 'unit+')

    def test_get_column_text_load(self):
        self.assert_column('LOAD', 'load+1234')

    def test_get_column_text_active(self):
        self.assert_column('ACTIVE', 'active')

    def test_get_column_text_sub(self):
        self.assert_column('SUB', 'sub+')

    def test_get_column_text_description(self):
        self.assert_column('DESCRIPTION', 'description')


if __name__ == '__main__':
    unittest.main()
