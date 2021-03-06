import unittest
from .helper import execute_main


class TestScopeStartupTime(unittest.TestCase):

    def test_option_critical(self):
        result = execute_main(argv=['-c', '1'])
        self.assertEqual(2, result.exitcode)
        self.assertEqual(
            'SYSTEMD CRITICAL - startup_time is 12.35 (outside range 0:1) '
            '| count_units=386 startup_time=12.345;60;1 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111',
            result.first_line
        )

    def test_option_warning(self):
        result = execute_main(argv=['-w', '2'])
        self.assertEqual(1, result.exitcode)
        self.assertEqual(
            'SYSTEMD WARNING - startup_time is 12.35 (outside range 0:2) '
            '| count_units=386 startup_time=12.345;2;120 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111',
            result.first_line
        )

    def test_option_no_startup_time_long(self):
        result = execute_main(argv=['-c', '1', '--no-startup-time'])
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - all | '
            'count_units=386 startup_time=12.345 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111',
            result.first_line
        )

    def test_option_no_startup_time_short(self):
        result = execute_main(argv=['-c', '1', '-n'])
        self.assertEqual(0, result.exitcode)
