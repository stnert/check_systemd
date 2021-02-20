[![pypi.org](http://img.shields.io/pypi/v/check_systemd.svg)](https://pypi.python.org/pypi/check_systemd)
[![Build Status](https://travis-ci.org/Josef-Friedrich/check_systemd.svg?branch=master)](https://travis-ci.org/Josef-Friedrich/check_systemd)

# check_systemd

`check_systemd` is a
[Nagios](https://www.nagios.org) / [Icinga](https://icinga.com)
monitoring plugin to check [systemd](https://systemd.io) for failed
units.

This Python script will report a degraded system to your monitoring solution.
It requires only the
[nagiosplugin](https://nagiosplugin.readthedocs.io/en/stable) library.

You can also test a single service with the `-u, --unit` parameter.

## Installation

```
pip3 install check_systemd
```

## Command line interface

```
{{ argparse }}
```

## Project pages

* https://github.com/Josef-Friedrich/check_systemd
* https://exchange.icinga.com/joseffriedrich/check_systemd
* https://exchange.nagios.org/directory/Plugins/System-Metrics/Processes/check_systemd/details

## Behind the scenes

To detect failed units this monitoring script runs:

```sh
systemctl list-units --all
```

To get the startup time it executes:

```sh
systemd-analyze
```

To check a specific  unit (`-u, --unit`) this command is executed:

```sh
systemctl is-active <unit-name>
```

To find dead timers this plugin launches:

```sh
systemctl list-timers --all
```

To learn how `systemd` produces the text output on the command line, it
is worthwhile to take a look at  `systemd`’s source
code. Files relevant for text output are:
[basic/time-util.c](https://github.com/systemd/systemd/blob/main/src/basic/time-util.c),
[analyze/analyze.c](https://github.com/systemd/systemd/blob/main/src/analyze/analyze.c).

## Testing

```
pyenv install 3.6.12
pyenv install 3.7.9
pyenv local 3.6.12 3.7.9
pip3 install tox
tox
```

## Deploying

Edit version number in check_systemd.py (without `v`)

```
git tag v2.0.11
git push --tags
```
