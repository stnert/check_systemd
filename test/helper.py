from io import StringIO
import sys
import re
from unittest.mock import Mock
from os import path

# https://github.com/Josef-Friedrich/jflib/blob/master/jflib/capturing.py


class Capturing(list):
    """Capture the stdout or stderr output. This class is designed for unit
    tests.
    :param stream: `stdout` or `stderr`.
    :param clean_ansi: Clean out ANSI colors from the captured output.
    .. seealso::
        `Answer on Stackoverflow <https://stackoverflow.com/a/16571630>`_
    """

    def __init__(self, stream: str = 'stdout', clean_ansi: bool = False):
        if stream not in ['stdout', 'stderr']:
            raise(ValueError('“stream” must be either “stdout” or “stderr”'))
        self.stream = stream
        self.clean_ansi = clean_ansi

    def __enter__(self):
        if self.stream == 'stdout':
            self._pipe = sys.stdout
            sys.stdout = self._stringio = StringIO()
        elif self.stream == 'stderr':
            self._pipe = sys.stderr
            sys.stderr = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        if self.clean_ansi:
            output = self._clean_ansi(self._stringio.getvalue())
        else:
            output = self._stringio.getvalue()
        self.extend(output.splitlines())
        del self._stringio
        if self.stream == 'stdout':
            sys.stdout = self._pipe
        elif self.stream == 'stderr':
            sys.stderr = self._pipe

    def tostring(self):
        """Convert the output into an string. By default a list of output
        lines is returned."""
        return '\n'.join(self)

    @staticmethod
    def _clean_ansi(text):
        return re.sub(r'\x1b.*?m', '', text)


def read_file_as_bytes(file_name):
    """Read a text file as bytes.

    :param str file_name: The name of the text file which is placed in the
      folder ``cli_output``.

    :return: The text as a byte format.
    """
    in_file = open(path.join('cli_output', file_name), 'rb')
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
