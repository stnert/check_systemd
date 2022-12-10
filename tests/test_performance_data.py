import unittest

from .helper import execute_main


class TestPerformanceData(unittest.TestCase):
    def test_ok(self):
        result = execute_main(argv=["--performance-data"])
        result.assert_ok()
        self.assertEqual(
            "SYSTEMD OK - all "
            "| count_units=386 data_source=cli startup_time=12.345;60;120 "
            "units_activating=0 "
            "units_active=275 units_failed=0 units_inactive=111",
            result.first_line,
        )

    def test_dead_timers(self):
        result = execute_main(
            argv=["--timers"],
            stdout=[
                "systemctl-list-units_3units.txt",
                "systemd-analyze_12.345.txt",
                "systemctl-list-timers_1.txt",
            ],
        )
        result.assert_critical()
        self.assertEqual(
            "SYSTEMD CRITICAL - phpsessionclean.timer "
            "| count_units=3 data_source=cli startup_time=12.345;60;120 "
            "units_activating=0 "
            "units_active=3 units_failed=0 units_inactive=0",
            result.first_line,
        )

    def test_options_exclude(self):
        result = execute_main(
            argv=["-e", "testX.service"],
            stdout=[
                "systemctl-list-units_failed.txt",
                "systemd-analyze_12.345.txt",
            ],
        )
        result.assert_critical()
        self.assertEqual(
            "SYSTEMD CRITICAL - smartd.service: failed | count_units=3 "
            "data_source=cli "
            "startup_time=12.345;60;120 "
            "units_activating=0 units_active=1 units_failed=1 "
            "units_inactive=1",
            result.first_line,
        )


if __name__ == "__main__":
    unittest.main()
