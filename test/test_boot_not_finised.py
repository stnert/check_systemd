import unittest
from .helper import execute_main


class TestBootupNotFinished(unittest.TestCase):

    def test_bootup_not_finished(self):
        result = execute_main(
            stdout=['systemctl-list-units_ok.txt',
                    'systemd-analyze_not-finished.txt', ],
            analyze_returncode=1)

        self.assertEqual(result.exitcode, 0)
        self.assertEqual(
            'SYSTEMD OK - all '
            '| count_units=386 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111',
            result.first_line
        )

    def test_bootup_not_finished_verbose(self):
        result = execute_main(
            argv=['--verbose'],
            stdout=['systemctl-list-units_ok.txt',
                    'systemd-analyze_not-finished.txt', ],
            analyze_returncode=1)

        self.assertEqual(result.exitcode, 0)
        self.assertEqual(
            'SYSTEMD OK - all\n'
            'ok: all\n'
            '| count_units=386 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111\n',
            result.output
        )


if __name__ == '__main__':
    unittest.main()
