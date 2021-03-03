#! /usr/bin/python3

"""
Work in progress! Do not use this script at the moment! Use the file
`check_systemd.py` instead. It is a rewrite of the plugin using D-Bus instead
of parsing the CLI output.
"""

import argparse

import nagiosplugin
from nagiosplugin import Metric

__version__ = '2.3.0'


data_source = 'dbus'
"""This variable indicates which data source should be used for the acquisition
of monitoring informations. It accepts the values ``dbus`` or ``cli``. It
preferes the D-Bus source. """


try:
    # Look for gi https://pygobject.readthedocs.io/en/latest/index.html
    from gi.repository.Gio import DBusProxy, BusType
except ImportError:
    try:
        # Fallback to pgi Pure Python GObject Introspection Bindings
        # https://github.com/pygobject/pgi
        from pgi.repository.Gio import DBusProxy, BusType
    except ImportError:
        # Fallback to the command line interface source.
        data_source = 'cli'


class DbusManager:
    """
    This class holds the main entry point object of the D-Bus systemd API. See
    the section `The Manager Object
    <https://www.freedesktop.org/software/systemd/man/org.freedesktop.systemd1.html#The%20Manager%20Object>`_
    in the systemd D-Bus API.
    """

    def __init__(self):
        self.__manager = DBusProxy.new_for_bus_sync(
            BusType.SYSTEM, 0, None, 'org.freedesktop.systemd1',
            '/org/freedesktop/systemd1', 'org.freedesktop.systemd1.Manager',
            None)

    def load_unit(self, unit_name):
        """
        Load a systemd D-Bus unit object by it’s name.

        :param str unit_name: A systemd unit name like ``tor.service``,
        ``mnt-nextcloud.automount`` or ``update-motd.timer``.
        """
        try:
            return self.__manager.LoadUnit('(s)', unit_name)
        except Exception as e:
            raise e


dbus_manager = None
"""
The systemd D-Bus API main entry point object, the so called “manager”.
"""


class SystemdUnitState:
    """
    Class that provides easy access to the three state properties
    ``ActiveState``, ``SubState`` and ``LoadState`` of the Dbus systemd API.
    """

    def __init__(self, unit_name):
        """
        :param str unit_name: A systemd unit name like ``tor.service``,
        ``mnt-nextcloud.automount`` or ``update-motd.timer``.
        """
        try:
            loaded_unit = dbus_manager.load_unit(unit_name)
        except Exception as e:
            raise e

        self.__dbus_unit = DBusProxy.new_for_bus_sync(
            BusType.SYSTEM, 0, None, 'org.freedesktop.systemd1',
            loaded_unit, 'org.freedesktop.systemd1.Unit', None)
        """
        The systemd D-Bus unit object is fetched by the method
        `Gio.DBusProxy.new_for_bus_sync
        <https://lazka.github.io/pgi-docs/#Gio-2.0/classes/DBusProxy.html#Gio.DBusProxy.new_for_bus_sync>`_.
        """

    def __get_dbus_property(self, property_name):
        """
        Get the property of a systemd D-Bus unit object. This method uses the
        methods `Gio.DBusProxy.get_cached_property
        <https://lazka.github.io/pgi-docs/#Gio-2.0/classes/DBusProxy.html#Gio.DBusProxy.get_cached_property>`_
        and
        `GLib.Variant.unpack
        <https://lazka.github.io/pgi-docs/#GLib-2.0/classes/Variant.html#GLib.Variant.unpack>`_
        for the lookup.
        """
        return self.__dbus_unit.get_cached_property(property_name).unpack()

    @property
    def active_state(self):
        """From the `D-Bus interface of systemd documentation
        <https://www.freedesktop.org/software/systemd/man/org.freedesktop.systemd1.html#Properties1>`_:

        ``ActiveState`` contains a state value that reflects whether the unit
        is currently active or not. The following states are currently defined:

        * ``active``,
        * ``reloading``,
        * ``inactive``,
        * ``failed``,
        * ``activating``, and ``deactivating``.

        ``active`` indicates that unit is active (obviously...).

        ``reloading`` indicates that the unit is active and currently reloading
        its configuration.

        ``inactive`` indicates that it is inactive and the previous run was
        successful or no previous run has taken place yet.

        ``failed`` indicates that it is inactive and the previous run was not
        successful (more information about the reason for this is available on
        the unit type specific interfaces, for example for services in the
        Result property, see below).

        ``activating`` indicates that the unit has previously been inactive but
        is currently in the process of entering an active state.

        Conversely ``deactivating`` indicates that the unit is currently in the
        process of deactivation.
        """
        return self.__get_dbus_property('ActiveState')

    @property
    def sub_state(self):
        """From the `D-Bus interface of systemd documentation
        <https://www.freedesktop.org/software/systemd/man/org.freedesktop.systemd1.html#Properties1>`_:

        ``SubState`` encodes states of the same state machine that
        ``ActiveState`` covers, but knows more fine-grained states that are
        unit-type-specific. Where ``ActiveState`` only covers six high-level
        states, ``SubState`` covers possibly many more low-level
        unit-type-specific states that are mapped to the six high-level states.
        Note that multiple low-level states might map to the same high-level
        state, but not vice versa. Not all high-level states have low-level
        counterparts on all unit types.
        """
        return self.__get_dbus_property('SubState')

    @property
    def load_state(self):
        """From the `D-Bus interface of systemd documentation
        <https://www.freedesktop.org/software/systemd/man/org.freedesktop.systemd1.html#Properties1>`_:

        ``LoadState`` contains a state value that reflects whether the
        configuration file of this unit has been loaded. The following states
        are currently defined:

        * ``loaded``,
        * ``error`` and
        * ``masked``.

        ``loaded`` indicates that the configuration was successfully loaded.

        ``error`` indicates that the configuration failed to load, the
        ``LoadError`` field contains information about the cause of this
        failure.

        ``masked`` indicates that the unit is currently masked out (i.e.
        symlinked to /dev/null or suchlike).

        Note that the ``LoadState`` is fully orthogonal to the ``ActiveState``
        (see below) as units without valid loaded configuration might be active
        (because configuration might have been reloaded at a time where a unit
        was already active).
        """
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
