import unittest
from unittest import mock
import check_systemd


def mock_main(argv=['check_systemd.py'], stdout=None, stderr=None):
    with mock.patch('sys.exit') as sys_exit, \
            mock.patch('check_systemd.subprocess.Popen') as Popen, \
            mock.patch('sys.argv', argv):
        process = Popen.return_value
        process.communicate.return_value = (stdout, stderr)
        check_systemd.main()

    return {'sys_exit': sys_exit}


class TestMock(unittest.TestCase):

    def test_ok(self):
        result = mock_main()
        result['sys_exit'].assert_called_with(0)


if __name__ == '__main__':
    unittest.main()
