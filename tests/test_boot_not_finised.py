import unittest

from .helper import MPopen, execute_main


class TestBootupNotFinished(unittest.TestCase):
    def test_bootup_not_finished(self):
        result = execute_main(
            argv=["--no-performance-data"],
            popen=(
                MPopen(stdout="systemctl-list-units_ok.txt"),
                MPopen(returncode=1, stderr="systemd-analyze_not-finished.txt"),
            ),
        )
        self.assertEqual(result.exitcode, 0)
        self.assertEqual("SYSTEMD OK - all", result.first_line)

    def test_bootup_not_finished_verbose(self):
        self.maxDiff = None
        result = execute_main(
            argv=["--verbose"],
            popen=(
                MPopen(stdout="systemctl-list-units_ok.txt"),
                MPopen(returncode=1, stderr="systemd-analyze_not-finished.txt"),
            ),
        )

        self.assertEqual(result.exitcode, 0)
        self.assertIn("SYSTEMD OK - all\n", result.output)


if __name__ == "__main__":
    unittest.main()
