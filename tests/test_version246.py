import unittest

from .helper import execute_main


class TestVersion246(unittest.TestCase):
    def test_version_246(self):
        result = execute_main(
            argv=["--no-performance-data"],
            stdout=[
                "systemctl-list-units_v246.txt",
                "systemd-analyze_12.345.txt",
            ],
        )
        result.assert_critical()
        self.assertEqual(
            "SYSTEMD CRITICAL - nm-wait-online.service: failed", result.first_line
        )


if __name__ == "__main__":
    unittest.main()
