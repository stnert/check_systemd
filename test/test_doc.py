import unittest
from jfscripts._utils import argparser_to_readme
from check_systemd import get_argparser


class TestDoc(unittest.TestCase):

    def test_doc(self):
        argparser_to_readme(argparser=get_argparser)


if __name__ == '__main__':
    unittest.main()
