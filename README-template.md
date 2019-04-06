[![pypi.org](http://img.shields.io/pypi/v/check_systemd.svg)](https://pypi.python.org/pypi/check_systemd)
[![Build Status](https://travis-ci.org/Josef-Friedrich/check_systemd.svg?branch=master)](https://travis-ci.org/Josef-Friedrich/check_systemd)

# check_systemd

Nagios / Icinga monitoring plugin to check systemd for failed units.

This Python script will report a degraded system to Nagios / Icinage.
It requires only the nagiosplugin library.

You can also test a single service with -s parameter.

Released under GNU GPLv2 License.

```
{{ argparse }}
```

## Project pages

* https://github.com/Josef-Friedrich/check_systemd
* https://exchange.icinga.com/joseffriedrich/check_systemd

## Testing

```
pip3 install tox
tox
```