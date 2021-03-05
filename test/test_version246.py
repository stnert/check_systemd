import unittest
from helper import execute_main


class TestVersion246(unittest.TestCase):

    def test_version_246(self):
        result = execute_main(
            stdout=['systemctl-list-units_v246.txt',
                    'systemd-analyze_12.345.txt', ])
        self.assertEqual(result.exitcode, 2)
        self.assertEqual(
            'SYSTEMD CRITICAL - nm-wait-online.service: failed | '
            'count_units=339 startup_time=12.345;60;120 units_activating=0 '
            'units_active=263 units_failed=1 units_inactive=75',
            result.first_line
        )


if __name__ == '__main__':
    unittest.main()
