import unittest
from helper import execute_main
import check_systemd
import subprocess


class TestArgparse(unittest.TestCase):

    def test_without_arguments(self):
        result = execute_main()
        self.assertEqual(result.exitcode, 0)

    def test_help_short(self):
        result = execute_main(argv=['-h'])
        self.assertIn('usage: check_systemd', result.output)

    def test_help_long(self):
        result = execute_main(argv=['--help'])
        self.assertIn('usage: check_systemd', result.output)

    def test_help_subprocess(self):
        process = subprocess.run(
            ['./check_systemd.py', '--help'],
            encoding='utf-8',
            stdout=subprocess.PIPE
        )
        self.assertEqual(process.returncode, 0)
        self.assertIn('usage: check_systemd', process.stdout)

    def test_version_short(self):
        result = execute_main(argv=['-V'])
        self.assertIn('check_systemd ' +
                      check_systemd.__version__, result.output)

    def test_version_long(self):
        result = execute_main(argv=['--version'])
        self.assertIn('check_systemd ' +
                      check_systemd.__version__, result.output)

    def test_version_subprocess(self):
        process = subprocess.run(
            ['./check_systemd.py', '--version'],
            encoding='utf-8',
            stdout=subprocess.PIPE
        )
        self.assertEqual(process.returncode, 0)
        self.assertIn('check_systemd ' +
                      check_systemd.__version__, process.stdout)

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

    def test_entry_point(self):
        process = subprocess.run(
            ['check_systemd', '--help'],
            encoding='utf-8',
            stdout=subprocess.PIPE
        )
        self.assertEqual(process.returncode, 0)
        self.assertIn('check_systemd', process.stdout)


if __name__ == '__main__':
    unittest.main()
