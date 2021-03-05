import unittest
from helper import execute_main


class TestOptionExclude(unittest.TestCase):

    def test_known_service(self):
        result = execute_main(
            argv=['-e', 'smartd.service'],
            stdout=['systemctl-list-units_failed.txt',
                    'systemd-analyze_12.345.txt', ],
        )
        self.assertEqual(result.exitcode, 0)
        self.assertEqual(
            'SYSTEMD OK - all | count_units=2 startup_time=12.345;60;120 '
            'units_activating=0 units_active=1 units_failed=0 '
            'units_inactive=1',
            result.first_line
        )

    def test_unknown_service(self):
        result = execute_main(
            argv=['-e', 'testX.service'],
            stdout=['systemctl-list-units_failed.txt',
                    'systemd-analyze_12.345.txt', ],
        )
        self.assertEqual(result.exitcode, 2)
        self.assertEqual(
            'SYSTEMD CRITICAL - smartd.service: failed | count_units=3 '
            'startup_time=12.345;60;120 '
            'units_activating=0 units_active=1 units_failed=1 '
            'units_inactive=1',
            result.first_line
        )

    # def test_option_exclude_regexp(self):
    #     with AddBin('bin/regexp_excludes'):
    #         process = subprocess.run(
    #             ['./check_systemd.py', '-e', 'user@\\d+\\.service'],
    #             encoding='utf-8',
    #             stdout=subprocess.PIPE
    #         )
    #     self.assertEqual(process.returncode, 0)
    #     self.assertEqual(
    #         process.stdout,
    #         'SYSTEMD OK - all | count_units=2 '
    #         'startup_time=12.154;60;120 '
    #         'units_activating=0 units_active=1 units_failed=0 '
    #         'units_inactive=1\n'
    #     )

    # def test_option_exclude_regexp_dot(self):
    #     with AddBin('bin/regexp_excludes'):
    #         process = subprocess.run(
    #             ['./check_systemd.py', '-e', '.*'],
    #             encoding='utf-8',
    #             stdout=subprocess.PIPE
    #         )
    #     self.assertEqual(process.returncode, 0)
    #     self.assertEqual(
    #         process.stdout,
    #         'SYSTEMD OK - all | count_units=0 '
    #         'startup_time=12.154;60;120 '
    #         'units_activating=0 units_active=0 units_failed=0 '
    #         'units_inactive=0\n'
    #     )


if __name__ == '__main__':
    unittest.main()
