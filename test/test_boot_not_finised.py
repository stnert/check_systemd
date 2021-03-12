import unittest
from .helper import execute_main, MPopen


class TestBootupNotFinished(unittest.TestCase):

    def test_bootup_not_finished(self):
        result = execute_main(popen=(
            MPopen(stdout='systemctl-list-units_ok.txt'),
            MPopen(returncode=1, stderr='systemd-analyze_not-finished.txt')
        ))
        self.assertEqual(result.exitcode, 0)
        self.assertEqual(
            'SYSTEMD OK - all '
            '| count_units=386 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111',
            result.first_line
        )

    def test_bootup_not_finished_verbose(self):
        self.maxDiff = None
        result = execute_main(argv=['--verbose'], popen=(
            MPopen(stdout='systemctl-list-units_ok.txt'),
            MPopen(returncode=1, stderr='systemd-analyze_not-finished.txt')
        ))

        self.assertEqual(result.exitcode, 0)
        self.assertIn(
            'SYSTEMD OK - all\n',
            result.output
        )
        self.assertIn(
            '| count_units=386 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111\n',
            result.output
        )


if __name__ == '__main__':
    unittest.main()
