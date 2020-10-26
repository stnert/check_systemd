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

Released under GNU GPLv2 License.

## Installation

```
pip3 install check_systemd
```

## Command line interface

```
usage: check_systemd [-h] [-u UNIT | -e UNIT] [-n] [-w SECONDS] [-c SECONDS]
                     [-t] [-W SECONDS] [-C SECONDS] [-v] [-V]

Copyright (c) 2014-18 Andrea Briganti a.k.a 'Kbyte' <kbytesys@gmail.com>
Copyright (c) 2019-20 Josef Friedrich <josef@friedrich.rocks>

Nagios / Icinga monitoring plugin to check systemd for failed units.

optional arguments:
  -h, --help            show this help message and exit
  -u UNIT, --unit UNIT  Name of the systemd unit that is being tested.
  -e UNIT, --exclude UNIT
                        Exclude a systemd unit from the checks. This option can
                        be applied multiple times, for example: -e mnt-
                        data.mount -e task.service. Regular expressions can be
                        used to exclude multiple units at once, for example: -e
                        'user@\d+\.service'. For more informations see the
                        Python documentation about regular expressions
                        (https://docs.python.org/3/library/re.html).
  -n, --no-startup-time
                        Don’t check the startup time. Using this option the
                        options '-w, --warning' and '-c, --critical' have no
                        effect. Performance data about the startup time is
                        collected, but no critical, warning etc. states are
                        triggered.
  -w SECONDS, --warning SECONDS
                        Startup time in seconds to result in a warning status.
                        Thedefault is 60 seconds.
  -c SECONDS, --critical SECONDS
                        Startup time in seconds to result in a critical status.
                        Thedefault is 120 seconds.
  -t, --dead-timers     Detect dead / inactive timers. See the corresponding
                        options '-W, --dead-timer-warning' and '-C, --dead-
                        timers-critical'. Dead timers are detected by parsing
                        the output of 'systemctl list-timers'. Dead timer rows
                        displaying 'n/a' in the NEXT and LEFTcolumns and the
                        time span in the column PASSED exceeds the values
                        specified with the options '-W, --dead-timer-warning'
                        and '-C, --dead-timers-critical'.
  -W SECONDS, --dead-timers-warning SECONDS
                        Time ago in seconds for dead / inactive timers to
                        trigger a warning state (by default 6 days).
  -C SECONDS, --dead-timers-critical SECONDS
                        Time ago in seconds for dead / inactive timers to
                        trigger a critical state (by default 7 days).
  -v, --verbose         Increase output verbosity (use up to 3 times).
  -V, --version         show program's version number and exit

Performance data:
  - count_units
  - startup_time
  - units_activating
  - units_active
  - units_failed
  - units_inactive

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
