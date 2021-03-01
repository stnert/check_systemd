#! /usr/bin/python3

"""
A work in progress rewrite of the plugin using dbus instead of parsing the cli
output.
"""

import argparse

import nagiosplugin
from nagiosplugin import Metric

try:
    from gi.repository.Gio import DBusProxy, BusType
except ImportError as e:
    print("Please install python3-gi")
    raise e

# https://www.freedesktop.org/wiki/Software/systemd/dbus/

# https://www.freedesktop.org/wiki/Software/systemd/dbus/#themanagerobject
dbus_manager = DBusProxy.new_for_bus_sync(
    BusType.SYSTEM, 0, None, 'org.freedesktop.systemd1',
    '/org/freedesktop/systemd1', 'org.freedesktop.systemd1.Manager', None)


class SystemdUnitState:
    """
    Class that provides easy access to the three state properties
    ``ActiveState``, ``SubState`` and ``LoadState`` of the Dbus systemd API.
    """

    def __init__(self, unit_name):
        """
        :param str unit_name: A systemd unit name like ``tor.service``
        """
        try:
            loaded_unit = dbus_manager.LoadUnit('(s)', unit_name)
        except Exception as e:
            raise e

        # https://lazka.github.io/pgi-docs/#Gio-2.0/classes/DBusProxy.html#Gio.DBusProxy.new_for_bus_sync
        self.__dbus_unit = DBusProxy.new_for_bus_sync(
            BusType.SYSTEM, 0, None, 'org.freedesktop.systemd1',
            loaded_unit, 'org.freedesktop.systemd1.Unit', None)

    def __get_dbus_property(self, property_name):
        # https://lazka.github.io/pgi-docs/#Gio-2.0/classes/DBusProxy.html#Gio.DBusProxy.get_cached_property
        # https://lazka.github.io/pgi-docs/#GLib-2.0/classes/Variant.html#GLib.Variant.unpack
        return self.__dbus_unit.get_cached_property(property_name).unpack()

    @property
    def active_state(self):
        return self.__get_dbus_property('ActiveState')

    @property
    def sub_state(self):
        return self.__get_dbus_property('SubState')

    @property
    def loadstate(self):
        return self.__get_dbus_property('LoadState')


class UnitResource(nagiosplugin.Resource):
    """Get informations about one specific systemd unit."""

    name = 'SYSTEMD'

    def __init__(self, *args, **kwargs):
        self.unit = kwargs.pop('unit')
        super().__init__(*args, **kwargs)

    def probe(self):
        return Metric(name=self.unit, value=SystemdUnitState(self.unit),
                      context='unit')


class UnitContext(nagiosplugin.Context):

    def __init__(self):
        super(UnitContext, self).__init__('unit')

    def evaluate(self, metric, resource):
        print(metric.value.active_state)
        return self.result_cls(nagiosplugin.Ok, metric=metric)


def get_argparser():
    parser = argparse.ArgumentParser(
        prog='check_systemd',  # To get the right command name in the README.
        formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=80),  # noqa: E501
        description=  # noqa: E251
        'Copyright (c) 2014-18 Andrea Briganti <kbytesys@gmail.com>\n'
        'Copyright (c) 2019-21 Josef Friedrich <josef@friedrich.rocks>\n'
        '\n'
        'Nagios / Icinga monitoring plugin to check systemd.\n',  # noqa: E501
        epilog=  # noqa: E251
        'Performance data:\n'
        '  - count_units\n'
        '  - startup_time\n'
        '  - units_activating\n'
        '  - units_active\n'
        '  - units_failed\n'
        '  - units_inactive\n',
    )

    exclusive_group = parser.add_mutually_exclusive_group()

    exclusive_group.add_argument(
        '-u', '--unit',
        type=str,
        dest='unit',
        help='Name of the systemd unit that is being tested.',
    )

    return parser


def main():
    """The main function"""
    args = get_argparser().parse_args()

    objects = [UnitContext()]

    if args.unit:
        objects.append(UnitResource(unit=args.unit))

    check = nagiosplugin.Check(*objects)
    check.main()


if __name__ == '__main__':
    main()
