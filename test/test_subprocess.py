import unittest
import os
import subprocess


class AddBin(object):
    """
    :param string bin_path: Path relative to the test folder.
    """

    def __init__(self, bin_path):
        self.bin_path = bin_path
        self.old_path = os.environ['PATH']

    def __enter__(self):
        BIN = os.path.abspath(os.path.join(os.path.dirname(__file__),
                              self.bin_path))
        os.environ['PATH'] = BIN + ':' + os.environ['PATH']

    def __exit__(self, exc_type, exc_value, traceback):
        os.environ['PATH'] = self.old_path


class TestOk(unittest.TestCase):

    def test_ok(self):
        with AddBin('bin/ok'):
            process = subprocess.run(
                ['./check_systemd.py'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stdout,
            'SYSTEMD OK - all '
            '| count_units=386 startup_time=12.154;60;120 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111\n'
        )

    def test_ok_verbose(self):
        with AddBin('bin/ok'):
            process = subprocess.run(
                ['./check_systemd.py', '--verbose'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stdout,
            'SYSTEMD OK - all\n'
            'ok: all\n'
            'ok: startup_time is 12.15\n'
            '| count_units=386 startup_time=12.154;60;120 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111\n'
        )


class TestFailure(unittest.TestCase):

    def test_failure(self):
        with AddBin('bin/failure'):
            process = subprocess.run(
                ['./check_systemd.py'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - smartd.service: failed '
            '| count_units=3 startup_time=12.154;60;120 '
            'units_activating=0 units_active=1 units_failed=1 '
            'units_inactive=1\n'
        )

    def test_failure_verbose(self):
        with AddBin('bin/failure'):
            process = subprocess.run(
                ['./check_systemd.py', '-v'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - smartd.service: failed\n'
            'critical: smartd.service: failed\n'
            '| count_units=3 startup_time=12.154;60;120 units_activating=0 '
            'units_active=1 units_failed=1 units_inactive=1\n'
        )


class TestMultipleFailure(unittest.TestCase):

    def test_failure_multiple(self):
        with AddBin('bin/multiple_failure'):
            process = subprocess.run(
                ['./check_systemd.py'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - rtkit-daemon.service: failed, smartd.service: '
            'failed | count_units=3 startup_time=46.292;60;120 '
            'units_activating=0 units_active=1 units_failed=2 '
            'units_inactive=0\n'
        )

    def test_failure_multiple_verbose(self):
        with AddBin('bin/multiple_failure'):
            process = subprocess.run(
                ['./check_systemd.py', '--verbose'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - rtkit-daemon.service: failed, '
            'smartd.service: failed\n'
            'critical: rtkit-daemon.service: failed\n'
            'critical: smartd.service: failed\n'
            '| count_units=3 startup_time=46.292;60;120 units_activating=0 '
            'units_active=1 units_failed=2 units_inactive=0\n'
        )


class TestCli(unittest.TestCase):

    def test_exclusive_group(self):
        process = subprocess.run(
            ['./check_systemd.py', '-u', 'test1.service', '-e',
             'test2.service'],
            encoding='utf-8',
            stderr=subprocess.PIPE
        )
        self.assertEqual(process.returncode, 2)
        self.assertIn(
            'error: argument -e/--exclude: not allowed with argument '
            '-u/--unit',
            process.stderr,
        )

    def test_option_critical(self):
        with AddBin('bin/ok'):
            process = subprocess.run(
                ['./check_systemd.py', '-c', '1'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - startup_time is 12.15 (outside range 0:1) '
            '| count_units=386 startup_time=12.154;60;1 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111\n'
        )

    def test_option_warning(self):
        with AddBin('bin/ok'):
            process = subprocess.run(
                ['./check_systemd.py', '-w', '2'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 1)
        self.assertEqual(
            process.stdout,
            'SYSTEMD WARNING - startup_time is 12.15 (outside range 0:2) '
            '| count_units=386 startup_time=12.154;2;120 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111\n'
        )

    def test_option_exclude_known_service(self):
        with AddBin('bin/failure'):
            process = subprocess.run(
                ['./check_systemd.py', '-e', 'smartd.service'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stdout,
            'SYSTEMD OK - all | count_units=2 startup_time=12.154;60;120 '
            'units_activating=0 units_active=1 units_failed=0 '
            'units_inactive=1\n'
        )

    def test_option_exclude_unknown_service(self):
        with AddBin('bin/failure'):
            process = subprocess.run(
                ['./check_systemd.py', '-e', 'testX.service'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - smartd.service: failed | count_units=3 '
            'startup_time=12.154;60;120 '
            'units_activating=0 units_active=1 units_failed=1 '
            'units_inactive=1\n'
        )

    def test_option_exclude_regexp(self):
        with AddBin('bin/regexp_excludes'):
            process = subprocess.run(
                ['./check_systemd.py', '-e', 'user@\\d+\\.service'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stdout,
            'SYSTEMD OK - all | count_units=2 '
            'startup_time=12.154;60;120 '
            'units_activating=0 units_active=1 units_failed=0 '
            'units_inactive=1\n'
        )

    def test_option_exclude_regexp_dot(self):
        with AddBin('bin/regexp_excludes'):
            process = subprocess.run(
                ['./check_systemd.py', '-e', '.*'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stdout,
            'SYSTEMD OK - all | count_units=0 '
            'startup_time=12.154;60;120 '
            'units_activating=0 units_active=0 units_failed=0 '
            'units_inactive=0\n'
        )

    def test_option_version(self):
        process = subprocess.run(
            ['./check_systemd.py', '--version'],
            encoding='utf-8',
            stdout=subprocess.PIPE
        )
        self.assertEqual(process.returncode, 0)
        self.assertIn('check_systemd', process.stdout)

    def test_option_help(self):
        process = subprocess.run(
            ['./check_systemd.py', '--help'],
            encoding='utf-8',
            stdout=subprocess.PIPE
        )
        self.assertEqual(process.returncode, 0)
        self.assertIn('check_systemd', process.stdout)

    def test_entry_point(self):
        process = subprocess.run(
            ['check_systemd', '--help'],
            encoding='utf-8',
            stdout=subprocess.PIPE
        )
        self.assertEqual(process.returncode, 0)
        self.assertIn('check_systemd', process.stdout)


class TestOptionUnit(unittest.TestCase):

    def test_option_unit_ok(self):
        with AddBin('bin/is_active/active'):
            process = subprocess.run(
                ['./check_systemd.py', '-u', 'test.service'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stdout,
            'SYSTEMD OK - test.service: active\n'
        )

    def test_option_unit_failed(self):
        with AddBin('bin/is_active/failed'):
            process = subprocess.run(
                ['./check_systemd.py', '--unit', 'test.service'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - test.service: failed\n'
        )

    def test_option_unit_inactive(self):
        with AddBin('bin/is_active/inactive'):
            process = subprocess.run(
                ['./check_systemd.py', '--unit', 'test.service'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - test.service: inactive\n'
        )


class TestBootupNotFinished(unittest.TestCase):

    def test_bootup_not_finished(self):
        with AddBin('bin/bootup_not_finished'):
            process = subprocess.run(
                ['./check_systemd.py'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stdout,
            'SYSTEMD OK - all '
            '| count_units=386 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111\n'
        )

    def test_bootup_not_finished_verbose(self):
        with AddBin('bin/bootup_not_finished'):
            process = subprocess.run(
                ['./check_systemd.py', '--verbose'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stdout,
            'SYSTEMD OK - all\n'
            'ok: all\n'
            '| count_units=386 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111\n'
        )


class TestDeadTimers(unittest.TestCase):

    def test_dead_timers_1(self):
        with AddBin('bin/dead_timers_1'):
            process = subprocess.run(
                ['./check_systemd.py', '-t'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - phpsessionclean.timer '
            '| count_units=3 startup_time=12.154;60;120 units_activating=0 '
            'units_active=3 units_failed=0 units_inactive=0\n'
        )

    def test_dead_timers_2(self):
        with AddBin('bin/dead_timers_2'):
            process = subprocess.run(
                ['./check_systemd.py', '-t'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - dfm-auto-jf.timer, '
            'rsync_nrasp_serverway-etc-letsencrypt_etc-letsencrypt.timer '
            '| count_units=3 startup_time=12.154;60;120 units_activating=0 '
            'units_active=3 units_failed=0 units_inactive=0\n'
        )

    def test_dead_timers_2_ok(self):
        with AddBin('bin/dead_timers_2'):
            process = subprocess.run(
                ['./check_systemd.py', '-t', '-W', '2764801', '-C', '2764802'],
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 0)

    def test_dead_timers_2_warning(self):
        with AddBin('bin/dead_timers_2'):
            process = subprocess.run(
                ['./check_systemd.py', '-t', '-W', '2764799', '-C', '2764802'],
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 1)

    def test_dead_timers_2_warning_equal(self):
        with AddBin('bin/dead_timers_2'):
            process = subprocess.run(
                ['./check_systemd.py', '-t', '-W', '2764800', '-C', '2764802'],
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 1)

    def test_dead_timers_ok(self):
        with AddBin('bin/dead_timers_ok'):
            process = subprocess.run(
                ['./check_systemd.py', '-t'],
                encoding='utf-8',
                stdout=subprocess.PIPE,
            )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stdout,
            'SYSTEMD OK - all '
            '| count_units=3 startup_time=12.154;60;120 units_activating=0 '
            'units_active=3 units_failed=0 units_inactive=0\n'
        )


if __name__ == '__main__':
    unittest.main()
