import unittest
from helper import execute_main

# POpen class
# Line 334 p = subprocess.Popen(['systemctl', 'list-units', '--all'],
# SystemctlListUnitsResource

# Line 460 p = subprocess.Popen(['systemd-analyze'],
# SystemdAnalyseResource

# Line 576 p = subprocess.Popen(['systemctl', 'list-timers', '--all'],
# SystemctlListTimersResource

# Line 656 p = subprocess.Popen(['systemctl', 'is-active', self.unit],
# SystemctlIsActiveResource


class TestMock(unittest.TestCase):

    def test_ok(self):
        result = execute_main()
        self.assertEqual(result.exitcode, 0)

    def test_help(self):
        result = execute_main(argv=['--help'])
        self.assertIn('usage: check_systemd', result.output)

    def test_single_unit(self):
        result = execute_main(
            argv=['-u', 'nginx.service'],
            stdout=['systemctl-is-active_active.txt',
                    'systemd-analyze_34-min.txt', ])
        self.assertEqual(result.exitcode, 0)
        self.assertEquals(
            'SYSTEMD OK - nginx.service: active',
            result.first_line
        )

    def test_multiple_units(self):
        result = execute_main()
        self.assertEqual(result.exitcode, 0)
        self.assertEquals(
            'SYSTEMD OK - all | count_units=386 startup_time=12.154;60;120 '
            'units_activating=0 units_active=275 units_failed=0 '
            'units_inactive=111',
            result.first_line
        )


if __name__ == '__main__':
    unittest.main()
