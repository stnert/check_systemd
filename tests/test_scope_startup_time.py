import unittest

from .helper import execute_main


class TestScopeStartupTime(unittest.TestCase):
    def test_option_critical(self):
        result = execute_main(argv=["-c", "1", "--no-performance-data"])
        result.assert_critical()
        self.assertEqual(
            "SYSTEMD CRITICAL - startup_time is 12.35 (outside range 0:1)",
            result.first_line,
        )

    def test_option_warning(self):
        result = execute_main(argv=["-w", "2", "--no-performance-data"])
        result.assert_warn()
        self.assertEqual(
            "SYSTEMD WARNING - startup_time is 12.35 (outside range 0:2)",
            result.first_line,
        )

    def test_option_no_startup_time_long(self):
        result = execute_main(
            argv=["-c", "1", "--no-startup-time", "--no-performance-data"]
        )
        result.assert_ok()
        self.assertEqual("SYSTEMD OK - all", result.first_line)

    def test_option_no_startup_time_short(self):
        result = execute_main(argv=["-c", "1", "-n"])
        result.assert_ok()
