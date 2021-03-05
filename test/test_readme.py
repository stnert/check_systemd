import unittest
from check_systemd import get_argparser
import re


def argparser_to_readme(argparser, template='README.md',
                        destination='README.md', indentation=0):
    """
    This function is a modified version of the function ``argparser_to_readme``
    from the package `jflib
    <https://github.com/Josef-Friedrich/jflib/blob/master/jflib/argparser_to_readme.py>`_

    Add the formatted help output of a command line utility using the
    Python module `argparse` to a README file. Make sure to set the name
    of the program (`prop`) or you get strange program names.

    :param object argparser: The argparse parser object.
    :param str template: The path of a template text file containing the
      placeholder. Default: `README-template.md`
    :param str destination: The path of the destination file. Default:
      `README.me`
    :param int indentation: Indent the formatted help output by X spaces.
      Default: 0
    :param str placeholder: Placeholder string that gets replaced by the
      formatted help output. Default: `{{ argparse }}`
    """
    help_string = argparser().format_help()

    if indentation > 0:
        indent_lines = []
        lines = help_string.split('\n')
        for line in lines:
            indent_lines.append(' ' * indentation + line)

        help_string = '\n'.join(indent_lines)

    with open(template, 'r', encoding='utf-8') as template_file:
        template_string = template_file.read()
        readme = re.sub(
            r'## Command line interface\n\n```\n.*?\n```',
            r'## Command line interface\n\n```\n' +
            help_string.replace('\\', '\\\\') + '\n```',
            template_string, flags=re.DOTALL
        )

    readme_file = open(destination, 'w')
    readme_file.write(readme)
    readme_file.close()


class TestReadme(unittest.TestCase):

    def test_readme(self):
        """This is not really a test. We “abuse” this test to patch the
        ``README.md`` file with the current ``--help`` text of the ``argparse``
        interface. Run ``make readme`` or ``tox -e py38 --
        test/test_readme.py`` to update the readme file."""
        argparser_to_readme(argparser=get_argparser)


if __name__ == '__main__':
    unittest.main()
