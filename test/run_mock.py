#!/usr/bin/env python3

# A little script to investigate the mocking of multiple Popen calls.

import subprocess
from unittest import mock
from unittest.mock import Mock
from os import path


def print_fortune():
    p = subprocess.Popen(['fortune'], stderr=subprocess.PIPE,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print(stdout.decode('utf-8'))


def read_file_as_bytes(file_name):
    in_file = open(path.join('cli_output', file_name), 'rb')
    data = in_file.read()
    in_file.close()
    return data


def mock_popen_communicate(*file_names):
    mocks = []
    for file_name in file_names:
        mock = Mock()
        mock.communicate.return_value = (read_file_as_bytes(file_name), None)
        mocks.append(mock)
    return mocks


with mock.patch('subprocess.Popen') as Popen:
    Popen.side_effect = mock_popen_communicate('mock2.txt', 'mock1.txt')
    print_fortune()
    print_fortune()
    # print_fortune() -> Error
