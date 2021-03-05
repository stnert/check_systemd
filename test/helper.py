from unittest import mock
from unittest.mock import Mock
from os import path
import check_systemd


def read_file_as_bytes(file_name):
    """Read a text file as bytes.

    :param str file_name: The name of the text file which is placed in the
      folder ``cli_output``.

    :return: The text as a byte format.
    """
    in_file = open(path.join(path.dirname(
        path.abspath(__file__)), 'cli_output', file_name), 'rb')
    data = in_file.read()
    in_file.close()
    return data


def mock_popen_communicate(*file_names):
    """
    Create multiple mock objects which are suitable to mimic multiple
    calls of `subprocess.Popen()`.

    :param file_names: Multiple file names of text files inside the folder
      ``cli_ouput``.

    :return: A list of mock objects.
      ``Popen.side_effect = result_of_is_function``
    """
    mocks = []
    for file_name in file_names:
        mock = Mock()
        mock.communicate.return_value = (read_file_as_bytes(file_name), None)
        mocks.append(mock)
    return mocks


def mock_main(argv=['check_systemd.py'], popen_stdout_files=[]):
    with mock.patch('sys.exit') as sys_exit, \
            mock.patch('check_systemd.subprocess.run') as run, \
            mock.patch('check_systemd.subprocess.Popen') as Popen, \
            mock.patch('sys.argv', argv), \
            mock.patch('builtins.print') as mocked_print:
        run.return_value.returncode = 0
        Popen.side_effect = mock_popen_communicate(*popen_stdout_files)
        check_systemd.main()

    output = []
    for call in mocked_print.call_args_list:
        output.append(call[0][0])

    return {
        'sys_exit': sys_exit,
        'run': run,
        'print': mocked_print,
        'output': '\n'.join(output)
    }
