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
            argv=['-e', 'smartd.service', '--no-performance-data'],
            unit_suffix='failed',
        )
        self.assertEqual(result.exitcode, 0)
        self.assertEqual(
            'SYSTEMD OK - all',
            result.first_line
        )

    def test_unknown_service(self):
        result = execute_with_opt_e(
            argv=['-e', 'testX.service', '--no-performance-data'],
            unit_suffix='failed',
        )
        self.assertEqual(result.exitcode, 2)
        self.assertEqual(
            'SYSTEMD CRITICAL - smartd.service: failed',
            result.first_line
        )

    def test_regexp(self):
        result = execute_with_opt_e(
            argv=['-e', 'user@\\d+\\.service', '--no-performance-data'],
            unit_suffix='regexp-excludes',
        )
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - all',
            result.first_line
        )

    def test_regexp_dot(self):
        result = execute_with_opt_e(
            argv=['-e', '.*', '--no-performance-data'],
            unit_suffix='regexp-excludes',
        )
        self.assertEqual(3, result.exitcode)

    def test_invalid_regexp(self):
        result = execute_with_opt_e(
            argv=['-e', '*service'],
            unit_suffix='ok',
        )
        self.assertEqual(3, result.exitcode)
        self.assertEqual(
            'SYSTEMD UNKNOWN: check_systemd.CheckSystemdRegexpError: '
            'Invalid regular expression: \'*service\'',
            result.first_line
        )


if __name__ == '__main__':
    unittest.main()
