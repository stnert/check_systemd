[![pypi.org](http://img.shields.io/pypi/v/check_systemd.svg)](https://pypi.python.org/pypi/check_systemd)
[![Build Status](https://travis-ci.org/Josef-Friedrich/check_systemd.svg?branch=master)](https://travis-ci.org/Josef-Friedrich/check_systemd)

# check_systemd

`check_systemd` is a [Nagios](https://www.nagios.org) /
[Icinga](https://icinga.com) monitoring plugin to check
[systemd](https://systemd.io). This Python script will report a degraded
system to your monitoring solution. It can also be used to monitor
individual systemd services (with the `-u, --unit` parameter) and timers
units (with the `-t, --dead-timers` parameter). The only dependency the
plugin needs is the Python library
[nagiosplugin](https://nagiosplugin.readthedocs.io/en/stable).

## Installation

```
pip3 install check_systemd
```

## Packages

* Debian ([package](https://packages.debian.org/search?keywords=monitoring%2Dplugins%2Dsystemd), [source code](https://salsa.debian.org/python-team/packages/monitoring-plugins-systemd/-/tree/debian/master/debian)): in unstable
* NixOS ([package](https://search.nixos.org/packages?channel=unstable&query=check_systemd), [source code](https://github.com/NixOS/nixpkgs/blob/nixos-unstable/pkgs/servers/monitoring/nagios/plugins/check_systemd.nix)): `nix-env -iA nixos.check_systemd`

## Command line interface

```
usage: check_systemd [-h] [-v] [-V] [-u UNIT] [-i] [-e UNIT] [-n] [-w SECONDS]
                     [-c SECONDS] [-t] [-W SECONDS] [-C SECONDS]
                     [--dbus | --cli]

Copyright (c) 2014-18 Andrea Briganti <kbytesys@gmail.com>
Copyright (c) 2019-21 Josef Friedrich <josef@friedrich.rocks>

Nagios / Icinga monitoring plugin to check systemd.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Increase output verbosity (use up to 3 times).
  -V, --version         show program's version number and exit

Options relation to unit selection:
  By default all systemd units are checked. Use the option '-e' to exclude units by a regular expression. Use the option '-u' to check only one unit.

  -u UNIT, --unit UNIT  Name of the systemd unit that is being tested.
  -i, --ignore-inactive-state
                        Ignore an inactive state on a specific unit. Oneshot
                        services for example are only active while running and
                        not enabled. The rest of the time they are inactive.
                        This option has only an affect if it is used with the
                        option -u.
  -e UNIT, --exclude UNIT
                        Exclude a systemd unit from the checks. This option can
                        be applied multiple times, for example: -e mnt-
                        data.mount -e task.service. Regular expressions can be
                        used to exclude multiple units at once, for example: -e
                        'user@\d+\.service'. For more informations see the
                        Python documentation about regular expressions
                        (https://docs.python.org/3/library/re.html).

Startup time related options:
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

Timers related options:
  -t, --dead-timers     Detect dead / inactive timers. See the corresponding
                        options '-W, --dead-timer-warning' and '-C, --dead-
                        timers-critical'. Dead timers are detected by parsing
                        the output of 'systemctl list-timers'. Dead timer rows
                        displaying 'n/a' in the NEXT and LEFT columns and the
                        time span in the column PASSED exceeds the values
                        specified with the options '-W, --dead-timer-warning'
                        and '-C, --dead-timers-critical'.
  -W SECONDS, --dead-timers-warning SECONDS
                        Time ago in seconds for dead / inactive timers to
                        trigger a warning state (by default 6 days).
  -C SECONDS, --dead-timers-critical SECONDS
                        Time ago in seconds for dead / inactive timers to
                        trigger a critical state (by default 7 days).

Monitoring data acquisition:
  --dbus                Use the systemd’s D-Bus API instead of parsing the text
                        output of various systemd related command line
                        interfaces to monitor systemd. At the moment the D-Bus
                        backend of this plugin is only partially implemented.
  --cli                 Use the text output of serveral systemd command line
                        interface (cli) binaries to gather the required data for
                        the monitoring process.

Performance data:
  - count_units
  - startup_time
  - units_activating
  - units_active
  - units_failed
  - units_inactive

```

## Project pages

* on [github.com](https://github.com/Josef-Friedrich/check_systemd)
* on [icinga.com](https://exchange.icinga.com/joseffriedrich/check_systemd)
* on [nagios.org](https://exchange.nagios.org/directory/Plugins/System-Metrics/Processes/check_systemd/details)

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

Edit the version number in check_systemd.py (without `v`). Use the `-s`
option to sign the tag (required for the Debian package).

```
git tag -s v2.0.11
git push --tags
```
