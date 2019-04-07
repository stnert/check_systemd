import os
import re
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with open(os.path.join(HERE, *parts), 'r', encoding='utf-8') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        version_file,
        re.M,
    )
    if version_match:
        return version_match.group(1)

    raise RuntimeError("Unable to find version string.")


setup(
    name='check_systemd',
    packages=find_packages(),
    version=find_version('check_systemd.py'),
    scripts=['check_systemd.py'],
    install_requires=[
        'nagiosplugin>=1.2',
    ],
    description='Nagios / Icinga monitoring plugin to check systemd for '
                'failed units.',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Josef Friedrich',
    author_email='josef@friedrich.rocks',
    url='https://github.com/Josef-Friedrich/check_systemd',
    keywords=['nagios', 'systemd'],
    license='GNU LGPL v2',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Lesser General Public License v2 '
        '(LGPLv2)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Networking :: Monitoring'
    ],
    entry_points={
        'console_scripts': [
            'check_systemd = check_systemd:main',
        ],
    },
)
