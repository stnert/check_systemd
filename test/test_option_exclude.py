import unittest
from .helper import execute_main


def execute_with_opt_e(argv, unit_suffix='failed'):
    return execute_main(
        argv=argv,
        stdout=[
            'systemctl-list-units_{}.txt'.format(unit_suffix),
            'systemd-analyze_12.345.txt',
        ]
    )


class TestOptionExclude(unittest.TestCase):

    def test_known_service(self):
        result = execute_with_opt_e(
            argv=['-e', 'smartd.service'],
            unit_suffix='failed',
        )
        self.assertEqual(result.exitcode, 0)
        self.assertEqual(
            'SYSTEMD OK - all | count_units=2 startup_time=12.345;60;120 '
            'units_activating=0 units_active=1 units_failed=0 '
            'units_inactive=1',
            result.first_line
        )

    def test_unknown_service(self):
        result = execute_with_opt_e(
            argv=['-e', 'testX.service'],
            unit_suffix='failed',
        )
        self.assertEqual(result.exitcode, 2)
        self.assertEqual(
            'SYSTEMD CRITICAL - smartd.service: failed | count_units=3 '
            'startup_time=12.345;60;120 '
            'units_activating=0 units_active=1 units_failed=1 '
            'units_inactive=1',
            result.first_line
        )

    def test_regexp(self):
        result = execute_with_opt_e(
            argv=['-e', 'user@\\d+\\.service'],
            unit_suffix='regexp-excludes',
        )
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - all | count_units=2 '
            'startup_time=12.345;60;120 '
            'units_activating=0 units_active=1 units_failed=0 '
            'units_inactive=1',
            result.first_line
        )

    def test_regexp_dot(self):
        result = execute_with_opt_e(
            argv=['-e', '.*'],
            unit_suffix='regexp-excludes',
        )
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - all | count_units=0 '
            'startup_time=12.345;60;120 '
            'units_activating=0 units_active=0 units_failed=0 '
            'units_inactive=0',
            result.first_line
        )


if __name__ == '__main__':
    unittest.main()
