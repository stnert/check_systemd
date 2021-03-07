from unittest import mock
from unittest.mock import Mock
from os import path
import check_systemd
from contextlib import redirect_stdout, redirect_stderr
import io
import os


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


def read_file_as_bytes(file_name: str) -> bytes:
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


def get_mocks_for_popen(*file_names):
    """
    Create multiple mock objects which are suitable to mimic multiple
    calls of `subprocess.Popen()`.

    Assign the result of this function to the attribute ``side_effect``:
    ``Popen.side_effect = result_of_is_function``

    :param file_names: Multiple file names of text files inside the folder
      ``cli_ouput``.

    :return: A list of mock objects.
    """
    mocks = []
    for file_name in file_names:
        mock = Mock()
        mock.communicate.return_value = (read_file_as_bytes(file_name), None)
        mocks.append(mock)
    return mocks


class MockResult:
    """A class to collect all results of a mocked execution of the main
    function."""

    def __init__(self, **kwargs):
        self.__sys_exit = kwargs.get('sys_exit')
        self.__print = kwargs.get('print')
        self.__stdout = kwargs.get('stdout')
        self.__stderr = kwargs.get('stderr')

    @property
    def exitcode(self):
        """The captured exit code"""
        return self.__sys_exit.call_args[0][0]

    @property
    def print_calls(self):
        """The captured print calls as a list for each line."""
        output = []
        for call in self.__print.call_args_list:
            output.append(call[0][0])
        return output

    @property
    def stdout(self):
        """The function ``redirect_stdout()`` is used to capture the ``stdout``
        output."""
        if self.__stdout:
            return self.__stdout

    @property
    def stderr(self):
        """The function ``redirect_stderr()`` is used to capture the ``stderr``
        output."""
        if self.__stderr:
            return self.__stderr

    @property
    def output(self):
        """A combined string of the captured stdout, stderr and the print
        calls. Somehow the whole stdout couldn’t be read. The help text could
        be read, but not the plugin output using the function
        ``redirect_stdout()``."""
        out = ''

        if self.print_calls:
            out += '\n'.join(self.print_calls)

        if self.__stdout:
            out += self.__stdout

        if self.__stderr:
            out += self.__stderr

        return out

    @property
    def first_line(self):
        """The first line of the stdout output without a newline break at the
        end as a string.
        """
        if self.output:
            return self.output.split('\n', 1)[0]


def execute_main(
        argv=['check_systemd.py'],
        stdout=['systemctl-list-units_ok.txt',
                'systemd-analyze_12.345.txt', ],
        analyze_returncode=0):
    """Execute the main function with a lot of patched functions and classes.

    :param list argv: A list of command line arguments, e. g.
        ``argv=['-u', 'nginx.service']``

    :param list stdout: A list of file names of files in the directory
        ``test/cli_output``. You have to specify as many text files as there
        are calls of the function ``subprocess.Popen``:

        * Line 334
          ``p = subprocess.Popen(['systemctl', 'list-units', '--all']``,
          ``SystemctlListUnitsResource``
        * Line 460
          ``p = subprocess.Popen(['systemd-analyze']``,
          ``SystemdAnalyseResource``
        * Line 576
          ``p = subprocess.Popen(['systemctl', 'list-timers', '--all']``,
          ``SystemctlListTimersResource``
        * Line 656
          ``p = subprocess.Popen(['systemctl', 'is-active', self.unit]``,
          ``SystemctlIsActiveResource``


    :param int analyze_returncode: The first call `systemctl analyze` to check
        if the startup process is finished

    :return: A results a assembled in the class ``MockResult``
    :rtype: MockResult

    """
    if not argv or argv[0] != 'check_systemd.py':
        argv.insert(0, 'check_systemd.py')
    with mock.patch('sys.exit') as sys_exit, \
            mock.patch('check_systemd.subprocess.run') as run, \
            mock.patch('check_systemd.subprocess.Popen') as Popen, \
            mock.patch('sys.argv', argv), \
            mock.patch('builtins.print') as mocked_print:
        # analyse = subprocess.run(['systemd-analyze'] ...)
        run.return_value.returncode = analyze_returncode
        Popen.side_effect = get_mocks_for_popen(*stdout)

        file_stdout = io.StringIO()
        file_stderr = io.StringIO()
        with redirect_stdout(file_stdout), redirect_stderr(file_stderr):
            check_systemd.main()

    return MockResult(
        sys_exit=sys_exit,
        print=mocked_print,
        stdout=file_stdout.getvalue(),
        stderr=file_stderr.getvalue(),
    )
