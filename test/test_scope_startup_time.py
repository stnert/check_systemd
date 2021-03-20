import unittest
from .helper import execute_main


class TestScopeStartupTime(unittest.TestCase):

    def test_option_critical(self):
        result = execute_main(argv=['-c', '1', '--no-performance-data'])
        self.assertEqual(2, result.exitcode)
        self.assertEqual(
            'SYSTEMD CRITICAL - startup_time is 12.35 (outside range 0:1)',
            result.first_line
        )

    def test_option_warning(self):
        result = execute_main(argv=['-w', '2', '--no-performance-data'])
        self.assertEqual(1, result.exitcode)
        self.assertEqual(
            'SYSTEMD WARNING - startup_time is 12.35 (outside range 0:2)',
            result.first_line
        )

    def test_option_no_startup_time_long(self):
        result = execute_main(
            argv=['-c', '1', '--no-startup-time', '--no-performance-data'])
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - all',
            result.first_line
        )

    def test_option_no_startup_time_short(self):
        result = execute_main(argv=['-c', '1', '-n'])
        self.assertEqual(0, result.exitcode)
