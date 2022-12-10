import unittest

from .helper import execute_main


def execute(argv, units_suffix="ok"):
    return execute_main(
        argv=argv,
        stdout=[
            "systemctl-list-units_{}.txt".format(units_suffix),
            "systemd-analyze_12.345.txt",
        ],
    )


class TestOk(unittest.TestCase):
    def test_ok(self):
        result = execute(argv=["--no-performance-data"])
        result.assert_ok()
        self.assertEqual("SYSTEMD OK - all", result.first_line)

    def test_multiple_units(self):
        result = execute_main(argv=["--no-performance-data"])
        result.assert_ok()
        self.assertEqual("SYSTEMD OK - all", result.first_line)


class TestFailure(unittest.TestCase):
    def test_failure(self):
        result = execute(argv=["--no-performance-data"], units_suffix="failed")
        result.assert_critical()
        self.assertEqual("SYSTEMD CRITICAL - smartd.service: failed", result.first_line)


class TestMultipleFailure(unittest.TestCase):
    def test_failure_multiple(self):
        result = execute(
            argv=["--no-performance-data"], units_suffix="multiple-failure"
        )
        result.assert_critical()
        self.assertIn("rtkit-daemon.service: failed", result.first_line)
        self.assertIn("smartd.service: failed", result.first_line)


if __name__ == "__main__":
    unittest.main()
