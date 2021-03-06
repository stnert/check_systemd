import unittest
import os
import subprocess
from .helper import execute_main


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

    def test_multiple_units(self):
        result = execute_main()
        self.assertEqual(0, result.exitcode)
        self.assertEqual(
            'SYSTEMD OK - all | count_units=386 startup_time=12.345;60;120 '
            'units_activating=0 units_active=275 units_failed=0 '
            'units_inactive=111',
            result.first_line
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

    def test_option_no_startup_time_long(self):
        with AddBin('bin/ok'):
            process = subprocess.run(
                ['./check_systemd.py', '-c', '1', '--no-startup-time'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stdout,
            'SYSTEMD OK - all | '
            'count_units=386 startup_time=12.154 units_activating=0 '
            'units_active=275 units_failed=0 units_inactive=111\n'
        )

    def test_option_no_startup_time_short(self):
        with AddBin('bin/ok'):
            process = subprocess.run(
                ['./check_systemd.py', '-c', '1', '-n'],
                encoding='utf-8',
                stdout=subprocess.PIPE
            )
        self.assertEqual(process.returncode, 0)


if __name__ == '__main__':
    unittest.main()
