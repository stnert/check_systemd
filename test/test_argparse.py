import unittest
from helper import execute_main
import check_systemd


class TestArgparse(unittest.TestCase):

    def test_help_short(self):
        result = execute_main(argv=['-h'])
        self.assertIn('usage: check_systemd', result.output)

    def test_help_long(self):
        result = execute_main(argv=['--help'])
        self.assertIn('usage: check_systemd', result.output)

    def test_version_short(self):
        result = execute_main(argv=['-V'])
        self.assertIn('check_systemd ' +
                      check_systemd.__version__, result.output)

    def test_version_long(self):
        result = execute_main(argv=['--version'])
        self.assertIn('check_systemd ' +
                      check_systemd.__version__, result.output)


if __name__ == '__main__':
    unittest.main()
