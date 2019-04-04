import unittest
import os
import subprocess

BIN = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bin'))
os.environ['PATH'] = BIN + ':' + os.environ['PATH']


class TestCheckSystemd(unittest.TestCase):

    def test_failure(self):
        process = subprocess.run(
            ['./check_systemd.py'],
            encoding='utf-8',
            stdout=subprocess.PIPE
        )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(
            process.stdout,
            'SYSTEMD CRITICAL - test.service: failed\n'
        )


if __name__ == '__main__':
    unittest.main()
