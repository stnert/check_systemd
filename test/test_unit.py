import unittest
import check_systemd


class TestUnit(unittest.TestCase):

    def test_function_format_timespan_to_seconds(self):
        _to_sec = check_systemd.format_timespan_to_seconds
        self.assertEqual(_to_sec('1s'), 1)
        self.assertEqual(_to_sec('11s'), 11)
        self.assertEqual(_to_sec('1min 1s'), 61)
        self.assertEqual(_to_sec('1min 1.123s'), 61.123)
        self.assertEqual(_to_sec('1min 2.15s'), 62.15)


if __name__ == '__main__':
    unittest.main()
