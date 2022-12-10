import unittest

from .helper import execute_main


def execute_with_opt_u(argv, list_units="ok"):
    if "--no-performance-data" not in argv:
        argv.append("--no-performance-data")
    return execute_main(
        argv=argv,
        stdout=[
            "systemctl-list-units_{}.txt".format(list_units),
            "systemd-analyze_12.345.txt",
        ],
    )


class TestOptionUnit(unittest.TestCase):
    def test_ok(self) -> None:
        result = execute_with_opt_u(argv=["--unit", "nginx.service"], list_units="ok")
        result.assert_ok()
        self.assertEqual(
            "SYSTEMD OK - nginx.service: active",
            result.first_line,
        )

    def test_failed(self) -> None:
        result = execute_with_opt_u(
            argv=["--unit", "smartd.service"], list_units="failed"
        )

        result.assert_critical()
        self.assertEqual(
            "SYSTEMD CRITICAL - smartd.service: failed",
            result.first_line,
        )

    def test_different_unit_name(self) -> None:
        result = execute_with_opt_u(argv=["--unit", "XXXXX.service"], list_units="ok")
        self.assertEqual(result.exitcode, 3)
        self.assertEqual(
            "SYSTEMD UNKNOWN: ValueError: Please verify your --include-* and "
            "--exclude-* options. No units have been added for testing.",
            result.first_line,
        )


if __name__ == "__main__":
    unittest.main()
