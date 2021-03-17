import unittest
from .helper import execute_main


def execute_with_opt_t(additional_argv=None, stdout_timers_suffix='1',
                       warning=None, critical=None):
    argv = ['-t']
    if warning:
        argv += ['-W', str(warning)]
    if critical:
        argv += ['-C', str(critical)]

    if additional_argv:
        argv += additional_argv

    return execute_main(
        argv=argv,
        stdout=[
            'systemctl-list-units_3units.txt',
            'systemctl-list-timers_{}.txt'.format(stdout_timers_suffix),
            'systemd-analyze_12.345.txt',
        ],
    )


class TestScopeTimers(unittest.TestCase):

    def test_dead_timers_1(self):
        result = execute_with_opt_t()
        self.assertEqual(2, result.exitcode)
        self.assertEqual(
            'SYSTEMD CRITICAL - phpsessionclean.timer '
            '| count_units=3 startup_time=12.345;60;120 units_activating=0 '
            'units_active=3 units_failed=0 units_inactive=0',
            result.first_line
        )

    def test_dead_timers_2(self):
        result = execute_with_opt_t(stdout_timers_suffix='2')
        self.assertEqual(2, result.exitcode)
        self.assertEqual(
            'SYSTEMD CRITICAL - dfm-auto-jf.timer, '
            'rsync.timer '
            '| count_units=3 startup_time=12.345;60;120 units_activating=0 '
            'units_active=3 units_failed=0 units_inactive=0',
            result.first_line
        )

    def test_dead_timers_2_ok(self):
        result = execute_with_opt_t(
            stdout_timers_suffix='2', warning=2764801, critical=2764802)
        self.assertEqual(0, result.exitcode)

    def test_dead_timers_2_warning(self):
        result = execute_with_opt_t(
            stdout_timers_suffix='2', warning=2764799, critical=2764802)
        self.assertEqual(1, result.exitcode)

    def test_dead_timers_2_warning_equal(self):
        result = execute_with_opt_t(
            stdout_timers_suffix='2', warning=2764800, critical=2764802)
        self.assertEqual(1, result.exitcode)

    def test_dead_timers_ok(self):
        result = execute_with_opt_t(stdout_timers_suffix='ok')
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - all '
            '| count_units=3 startup_time=12.345;60;120 units_activating=0 '
            'units_active=3 units_failed=0 units_inactive=0',
            result.first_line
        )

    def test_dead_timers_exclude(self):
        result = execute_with_opt_t(stdout_timers_suffix='2', additional_argv=[
                                    '-e', 'dfm-auto-jf.timer'])
        self.assertEqual(2, result.exitcode)
        self.assertEqual(
            'SYSTEMD CRITICAL - rsync.timer '
            '| count_units=3 startup_time=12.345;60;120 units_activating=0 '
            'units_active=3 units_failed=0 units_inactive=0',
            result.first_line
        )

    def test_dead_timers_exclude_multiple(self):
        result = execute_with_opt_t(stdout_timers_suffix='2', additional_argv=[
                            '-e', 'dfm-auto-jf.timer', '-e', 'rsync.timer'])
        self.assertEqual(0, result.exitcode)

    def test_dead_timers_exclude_regexp(self):
        result = execute_with_opt_t(stdout_timers_suffix='2', additional_argv=[
                    '-e', 'dfm-auto-jf.timer', '-e', '.*timer'])
        self.assertEqual(0, result.exitcode)


if __name__ == '__main__':
    unittest.main()
