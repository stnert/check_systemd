import unittest
from helper import execute_main


def execute_with_opt_u(argv, state='active'):
    return execute_main(
        argv=argv,
        stdout=[
            'systemctl-is-active_{}.txt'.format(state),
            'systemd-analyze_12.345.txt',
        ]
    )


class TestOptionUnit(unittest.TestCase):

    def test_option_unit_ok(self):
        result = execute_with_opt_u(argv=['--unit', 'test.service'],
                                    state='active')
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - test.service: active',
            result.first_line,
        )

    def test_option_unit_failed(self):
        result = execute_with_opt_u(argv=['--unit', 'test.service'],
                                    state='failed')

        self.assertEqual(2, result.exitcode)
        self.assertEqual(
            'SYSTEMD CRITICAL - test.service: failed',
            result.first_line,
        )

    def test_option_unit_inactive(self):
        result = execute_with_opt_u(argv=['--unit', 'test.service'],
                                    state='inactive')
        self.assertEqual(2, result.exitcode)
        self.assertEqual(
            'SYSTEMD CRITICAL - test.service: inactive',
            result.first_line,
        )

    def test_option_ignore_inactive_state(self):
        result = execute_with_opt_u(argv=['--unit', 'test.service',
                                          '--ignore-inactive-state'],
                                    state='inactive')

        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - test.service: inactive',
            result.first_line,
        )


if __name__ == '__main__':
    unittest.main()
