import unittest
from .helper import execute_main


def execute(argv, units_suffix='ok'):
    return execute_main(
        argv=argv,
        stdout=[
            'systemctl-list-units_{}.txt'.format(units_suffix),
            'systemd-analyze_12.345.txt',
        ]
    )


class TestOk(unittest.TestCase):

    def test_ok(self):
        result = execute(argv=[])
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - all '
            '| count_units=386 startup_time=12.345;60;120 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111',
            result.first_line
        )

    @unittest.skip
    def test_ok_verbose(self):
        result = execute(argv=['--verbose'])
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - all\n'
            'ok: all\n'
            'ok: startup_time is 12.35\n'
            '| count_units=386 startup_time=12.345;60;120 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111\n',
            result.output
        )

    def test_multiple_units(self):
        result = execute_main()
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - all | count_units=386 startup_time=12.345;60;120 '
            'units_activating=0 units_active=275 units_failed=0 '
            'units_inactive=111',
            result.first_line
        )


class TestFailure(unittest.TestCase):

    def test_failure(self):
        result = execute(argv=[], units_suffix='failed')
        self.assertEqual(2, result.exitcode)
        self.assertEqual(
            'SYSTEMD CRITICAL - smartd.service: failed '
            '| count_units=3 startup_time=12.345;60;120 '
            'units_activating=0 units_active=1 units_failed=1 '
            'units_inactive=1',
            result.first_line
        )

    @unittest.skip
    def test_failure_verbose(self):
        result = execute(argv=['--verbose'], units_suffix='failed')
        self.assertEqual(2, result.exitcode)
        self.assertEqual(
            'SYSTEMD CRITICAL - smartd.service: failed\n'
            'critical: smartd.service: failed\n'
            '| count_units=3 startup_time=12.154;60;120 units_activating=0 '
            'units_active=1 units_failed=1 units_inactive=1\n',
            result.output
        )


class TestMultipleFailure(unittest.TestCase):

    def test_failure_multiple(self):
        result = execute(argv=[], units_suffix='multiple-failure')
        self.assertEqual(2, result.exitcode)
        self.assertIn('rtkit-daemon.service: failed', result.first_line)
        self.assertIn('smartd.service: failed', result.first_line)

    @unittest.skip
    def test_failure_multiple_verbose(self):
        result = execute(argv=['--verbose'], units_suffix='multiple-failure')
        self.assertEqual(2, result.exitcode)
        self.assertEqual(
            'SYSTEMD CRITICAL - rtkit-daemon.service: failed, '
            'smartd.service: failed\n'
            'critical: rtkit-daemon.service: failed\n'
            'critical: smartd.service: failed\n'
            '| count_units=3 startup_time=12.345;60;120 units_activating=0 '
            'units_active=1 units_failed=2 units_inactive=0\n',
            result.output
        )


if __name__ == '__main__':
    unittest.main()
