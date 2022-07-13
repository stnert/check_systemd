#! /usr/bin/python3

import argparse
import typing

import package_dbus_python
import package_gio
import package_subprocess
import utils

parser = argparse.ArgumentParser(description='Process some integers.')

parser.add_argument(
    '--unit-type', '-t',
    choices=typing.get_args(utils.UnitType)
)

parser.add_argument('--properties', '-p', type=str, nargs='+')

parser.add_argument(
    '--package', '-P',
    choices=('gio', 'dbus-python', 'cli'),
    default='gio'
)


args = parser.parse_args()

list_units = None
if args.package == 'dbus-python':
    list_units = package_dbus_python.list_units
elif args.package == 'cli':
    list_units = package_subprocess.list_units
else:
    list_units = package_gio.list_units

list_units(
    unit_type=args.unit_type, properties=args.properties)
