#! /usr/bin/python3

import argparse
import package_dbus_python
import utils
import typing

parser = argparse.ArgumentParser(description='Process some integers.')

parser.add_argument(
    '--unit-type', '-t',
    choices=typing.get_args(utils.UnitType)
)

parser.add_argument('--properties', '-p', type=str, nargs='+')

args = parser.parse_args()

package_dbus_python.list_units(
    unit_type=args.unit_type, properties=args.properties)
