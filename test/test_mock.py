import unittest
from unittest import mock
import check_systemd
from helper import mock_main

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
        result = mock_main(popen_stdout_files=[
                           'systemctl-list-units-ok.txt',
                           'systemd-analyze-34-min.txt'])
        result['sys_exit'].assert_called_with(0)

    def test_help(self):
        mock_main(argv=['check_systemd.py', '--help'],
                  popen_stdout_files=[
            'systemctl-list-units-ok.txt',
            'systemd-analyze-34-min.txt'])

        # self.assertIn('usage: check_systemd', result['output'])
        # sys_exit.assert_called_with(0)

    def test_single_unit(self):
        with mock.patch('sys.exit') as sys_exit, \
                mock.patch('check_systemd.subprocess.run') as run, \
                mock.patch('check_systemd.subprocess.Popen') as Popen, \
                mock.patch('sys.argv', ['check_systemd.py', '-u',
                                        'nginx.service']):
            run.return_value.returncode = 0
            process = Popen.return_value
            process.communicate.return_value = (b'active', None)
            check_systemd.main()
            # self.assertIn('SYSTEMD OK - nginx.service: active', output)

            sys_exit.assert_called_with(0)

    def test_multiple_units(self):
        result = mock_main(popen_stdout_files=[
                           'systemctl-list-units-ok.txt',
                           'systemd-analyze-34-min.txt'])
        result['sys_exit'].assert_called_with(0)

        self.assertEquals(
            'SYSTEMD OK - all | count_units=386 startup_time=12.154;60;120 '
            'units_activating=0 units_active=275 units_failed=0 '
            'units_inactive=111\n',
            result['print'].call_args_list[0][0][0]
        )


if __name__ == '__main__':
    unittest.main()
