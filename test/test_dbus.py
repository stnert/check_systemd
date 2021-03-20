"""Test the D-Bus API as a data source."""

import unittest
import check_systemd
from unittest.mock import patch


class TestDbus(unittest.TestCase):

    def test_mocking(self):

        with patch('sys.exit'), \
             patch('sys.argv', ['check_systemd.py', '--dbus']):
            check_systemd.main()


if __name__ == '__main__':
    unittest.main()
