#!/usr/bin/env python3

"""
``check_system`` is a `Nagios <https://www.nagios.org>`_ / `Icinga
<https://icinga.com>`_ monitoring plugin to check systemd. This Python script
will report a degraded system to your monitoring solution. It can also be used
to monitor individual systemd services (with the ``-u, --unit`` parameter) and
timers units (with the ``-t, --dead-timers`` parameter).

To learn more about the project, please visit the repository on `Github
<https://github.com/Josef-Friedrich/check_systemd>`_.

This plugin is based on a Python package named `nagiosplugin
<https://pypi.org/project/nagiosplugin/>`_. ``nagiosplugin`` has a fine-grained
class model to separate concerns. A Nagios / Icinga plugin must perform these
three steps: data `acquisition`, `evaluation` and `presentation`.
``nagiosplugin`` provides for this three steps three classes: ``Resource``,
``Context``, ``Summary``. ``check_systemd`` extends this three model classes in
the following subclasses:

Acquisition (``Resource``)
==========================

* :class:`SystemctlIsActiveResource`
* :class:`SystemctlListTimersResource`
* :class:`SystemctlListUnitsResource`
* :class:`SystemdAnalyseResource`

Evaluation (``Context``)
========================

* :class:`DeadTimersContext` (``context=dead_timers``)
* :class:`PerformanceDataContext` (``context=performance_data``)
* :class:`UnitContext` (``context=unit``)

Presentation (``Summary``)
==========================

* :class:`SystemdSummary`

Monitoring scopes
=================

* Startup time
* State of unites
* Timers

Naming scheme for the classes
=============================

* data source: ``Dbus|Cli`` +
* Custom name: ``CustomName`` +
* inherited class model: ``Resource|Context|Summary``

"""
import io
import subprocess
import argparse
import re

import nagiosplugin
from nagiosplugin import Metric

__version__ = '2.3.1'


data_source = 'dbus'
"""This variable indicates which data source should be used for the acquisition
of monitoring informations. It accepts the values ``dbus`` or ``cli``. It
prefers the D-Bus source. """

opts = None
"""
We make is variable global to be able to access the command line arguments
everywhere in the plugin. In this variable the result of `parse_args()
<https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.parse_args>`_
is stored. It is an instance of the
`argparse.Namespace
<https://docs.python.org/3/library/argparse.html#argparse.Namespace>`_ class.
This variable is initialized in the main function. The variable is
intentionally not named ``args`` to avoid confusion with ``*args`` (Non-Keyword
Arguments).
"""

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

    def get_all_unit_names(self):
        all_units = self.__manager.ListUnits()
        units_set = set()
        for (name, _, _, _, _, _, _, _, _, _) in all_units:
            units_set.add(name)
        return units_set


dbus_manager = None
"""
The systemd D-Bus API main entry point object, the so called “manager”.
"""
if data_source == 'dbus':
    dbus_manager = DbusManager()


class Unit:
    """This class bundles all state related informations of a systemd unit in a
    object. This class is inherited by the class ``DbusUnit`` and the
    attributes are overwritten by properties.
    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        """The name of the system unit, for example ``nginx.service``. In the
        command line table of the command ``systemctl list-units`` is the
        column containing unit names titled with “UNIT”.
        """

        self.active_state = kwargs.get('active_state')
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

        self.sub_state = kwargs.get('sub_state')
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

        All sub states are listed in the file `basic/unit-def.c
        <https://github.com/systemd/systemd/blob/main/src/basic/unit-def.c>`_
        of the systemd source code:

        * automount: ``dead``, ``waiting``, ``running``, ``failed``
        * device: ``dead``, ``tentative``, ``plugged``
        * mount: ``dead``, ``mounting``, ``mounting-done``, ``mounted``,
          ``remounting``, ``unmounting``, ``remounting-sigterm``,
          ``remounting-sigkill``, ``unmounting-sigterm``,
          ``unmounting-sigkill``, ``failed``, ``cleaning``
        * path: ``dead``, ``waiting``, ``running``, ``failed``
        * scope: ``dead``, ``running``, ``abandoned``, ``stop-sigterm``,
          ``stop-sigkill``, ``failed``
        * service: ``dead``, ``condition``, ``start-pre``, ``start``,
          ``start-post``, ``running``, ``exited``, ``reload``, ``stop``,
          ``stop-watchdog``, ``stop-sigterm``, ``stop-sigkill``, ``stop-post``,
          ``final-watchdog``, ``final-sigterm``, ``final-sigkill``, ``failed``,
          ``auto-restart``, ``cleaning``
        * slice: ``dead``, ``active``
        * socket: ``dead``, ``start-pre``, ``start-chown``, ``start-post``,
          ``listening``, ``running``, ``stop-pre``, ``stop-pre-sigterm``,
          ``stop-pre-sigkill``, ``stop-post``, ``final-sigterm``,
          ``final-sigkill``, ``failed``, ``cleaning``
        * swap: ``dead``, ``activating``, ``activating-done``, ``active``,
          ``deactivating``, ``deactivating-sigterm``, ``deactivating-sigkill``,
          ``failed``, ``cleaning``
        * target:``dead``, ``active``
        * timer: ``dead``, ``waiting``, ``running``, ``elapsed``, ``failed``
        """

        self.load_state = kwargs.get('load_state')
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

    def convert_to_exitcode(self):
        """Convert the different systemd states into a Nagios compatible
        exit code.

        :return: A Nagios compatible exit code: 0, 1, 2, 3
        :rtype: int"""
        if self.load_state == 'error' or self.active_state == 'failed':
            return nagiosplugin.Critical
        return nagiosplugin.Ok


class UnitCache:

    def __init__(self):
        self.__units = {}

    def add(self, unit):
        self.__units[unit.name] = unit

    def get(self, name=None, exclude=None, include=None):
        if name:
            return self.__units[name]

    def list(self, exclude=None, include=None):
        for name in self.__units:

            if include and not re.match(include, name):
                name = None

            if name and exclude and re.match(exclude, name):
                name = None

            if name:
                yield self.__units[name]


class DbusUnit(Unit):
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
        """
        See :func:`UnitState.active_state`
        """
        return self.__get_dbus_property('ActiveState')

    @property
    def sub_state(self):
        """
        See :func:`UnitState.sub_state`
        """
        return self.__get_dbus_property('SubState')

    @property
    def load_state(self):
        """
        See :func:`UnitState.load_state`
        """
        return self.__get_dbus_property('LoadState')


class DbusSingleUnitResource(nagiosplugin.Resource):
    """Get informations about one specific systemd unit."""

    name = 'SYSTEMD'

    def __init__(self, *args, **kwargs):
        self.unit = kwargs.pop('unit')
        super().__init__(*args, **kwargs)

    def probe(self):
        unit_state = DbusUnit(self.unit)
        return Metric(name=self.unit, value=unit_state,
                      context='unit')


class DbusAllUnitsResource(nagiosplugin.Resource):

    name = 'SYSTEMD'

    def probe(self):
        """Query system state and return metrics.

        :return: generator that emits
          :class:`~nagiosplugin.metric.Metric` objects
        """
        unit_names = dbus_manager.get_all_unit_names()

        for unit_name in unit_names:
            unit_state = DbusUnit(unit_name)
            yield Metric(name=unit_name, value=unit_state,
                         context='unit')


class SystemctlListUnitsResource(nagiosplugin.Resource):
    """
    Resource that calls ``systemctl list-units --all`` on the command line to
    get informations about all systemd units.

    :param list excludes: A list of systemd unit names.
    """
    name = 'SYSTEMD'

    def __init__(self, excludes=[]):
        self.excludes = excludes

    def re_match(self, unit):
        for exclude in self.excludes:
            if re.match(exclude, unit):
                return(True)
        return(False)

    def probe(self):
        """Query system state and return metrics.

        :return: generator that emits
          :class:`~nagiosplugin.metric.Metric` objects
        """
        # We don’t use `systemctl --failed --no-legend`, because we want to
        # collect performance data of all units.
        stdout = execute_cli(['systemctl', 'list-units', '--all'])

        # Dictionary to store all units according their active state.
        units = {
            'failed': [],
            'active': [],
            'activating': [],
            'inactive': [],
        }
        if stdout:
            lines = stdout.splitlines()
            table_heading = lines[0]

            # Remove the first line because it is the header.

            # Remove the  last seven lines:

            # empty line
            # LOAD   = Reflects whether the unit definition...
            # ACTIVE = The high-level unit activation state...
            # SUB    = The low-level unit activation state...
            # empty line
            # xxx loaded units listed. Pass --all to see ...
            # To show all installed unit files use...
            table_body = lines[1:-7]
            table_parser = TableParser(table_heading)
            # Output of `systemctl list-units --all:
            # UNIT           LOAD   ACTIVE SUB     JOB   DESCRIPTION
            # foobar.service loaded active waiting       Description text
            count_units = 0
            for line in table_body:
                # foobar.service
                unit = table_parser.get_column_text(line, 'UNIT')
                # failed
                active = table_parser.get_column_text(line, 'ACTIVE')

                # Only count not excluded units.
                if not self.re_match(unit):
                    # Quick fix:
                    # Issue on Arch: “not-found” in column ACTIVE
                    # maybe cli table output changed on newer versions of
                    # systemd?
                    # maybe .split() is not working correctly?
                    if active not in units:
                        units[active] = []
                    units[active].append(unit)
                    count_units += 1

            for unit in units['failed']:
                if not self.re_match(unit):
                    yield Metric(name=unit, value='failed', context='unit')

            for active, unit_names in units.items():
                yield Metric(name='units_{}'.format(active),
                             value=len(units[active]),
                             context='performance_data')

            yield Metric(name='count_units', value=count_units,
                         context='performance_data')

        if len(units['failed']) == 0:
            yield Metric(name='all', value=None, context='unit')


def format_timespan_to_seconds(fmt_timespan):
    """Convert a timespan format string into secondes. Take a look at the
    systemd `time-util.c
    <https://github.com/systemd/systemd/blob/master/src/basic/time-util.c>`_
    source code.

    :param str fmt_timespan: for example ``2.345s`` or ``3min 45.234s`` or
      ``34min left`` or ``2 months 8 days``

    :return: The seconds :rtype: float
    """
    for replacement in [
        ['years', 'y'],
        ['months', 'month'],
        ['weeks', 'w'],
        ['days', 'd'],
    ]:
        fmt_timespan = fmt_timespan.replace(
            ' ' + replacement[0], replacement[1]
        )
    seconds = {
        'y': 31536000,  # 365 * 24 * 60 * 60
        'month': 2592000,  # 30 * 24 * 60 * 60
        'w': 604800,  # 7 * 24 * 60 * 60
        'd': 86400,  # 24 * 60 * 60
        'h': 3600,  # 60 * 60
        'min': 60,
        's': 1,
        'ms': 0.001,
    }
    result = 0
    for span in fmt_timespan.split():
        match = re.search(r'([\d\.]+)([a-z]+)', span)
        if match:
            value = match.group(1)
            unit = match.group(2)
            result += float(value) * seconds[unit]
    return round(float(result), 3)


def execute_cli(args):
    """Execute a command on the command line (cli = command line interface))
    and capture the stdout. This is a wrapper around ``subprocess.Popen``.

    :param list args: A list of programm arguments.

    :raises nagiosplugin.CheckError: If the command produces some stderr output
      or if an OSError exception occurs.

    :return: The stdout of the command.
    :rtype: str
    """
    try:
        p = subprocess.Popen(args,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
    except OSError as e:
        raise nagiosplugin.CheckError(e)

    if stderr:
        raise nagiosplugin.CheckError(stderr)

    if stdout:
        stdout = stdout.decode('utf-8')
        return stdout


def get_unitstate_from_cli(unit_name):
    """
    Run the command ``systemctl show unit-name.service`` on the command line
    and extract the three keys ``ActiveState``, ``SubState``, and
    ``LoadState``.

    :param str unit_name: A systemd unit name like ``tor.service``,
          ``mnt-nextcloud.automount`` or ``update-motd.timer``.

    :return: A unit state object.
    :rtype: UnitState
    """
    def search(stdout, key):
        result = re.search(key + '=(.*)', stdout)
        return result.group(1)

    stdout = execute_cli(['systemctl', 'show', unit_name])
    return Unit(
        active_state=search(stdout, 'ActiveState'),
        sub_state=search(stdout, 'SubState'),
        load_state=search(stdout, 'LoadState'),
    )


class SystemdAnalyseResource(nagiosplugin.Resource):
    """Resource that calls ``systemd-analyze`` on the command line to get
    informations about the startup time."""

    name = 'SYSTEMD'

    def probe(self):
        """Query system state and return metrics.

        :return: generator that emits
          :class:`~nagiosplugin.metric.Metric` objects
        """
        stdout = execute_cli(['systemd-analyze'])

        if stdout:
            # First line:
            # Startup finished in 1.672s (kernel) + 21.378s (userspace) =
            # 23.050s

            # On raspian no second line
            # Second line:
            # graphical.target reached after 1min 2.154s in userspace
            match = re.search(r'reached after (.+) in userspace', stdout)

            if not match:
                match = re.search(r' = (.+)\n', stdout)

            # Output when boot process is not finished:
            # Bootup is not yet finished. Please try again later.
            if match:
                yield Metric(name='startup_time',
                             value=format_timespan_to_seconds(match.group(1)),
                             context='startup_time')


class TableParser:
    """A parser for the various table outputs of different systemd commands."""

    def __init__(self, heading_row):
        """
        :param str heading_row: A row with column titles.
        """
        self.heading_row = heading_row

    def detect_column_boundaries(self, column_title):
        """
        :param str column_title: The title of the column, for example UNIT,
          ACTIVE. The column title must be included in the heading row.
        """
        match = re.search(re.compile(column_title + r'\s*'), self.heading_row)
        return [match.start(), match.end()]

    def get_column_text(self, row, column_title):
        """Get the text of a certain column, that is specified by the column
        title. Leading and trailing whitespaces are removed.

        :param str row: The current row of the table to extract a certain
          column.
        :param str column_title: The title of the column, for example UNIT,
          ACTIVE. The column title must be included in the heading row.
        """
        boundaries = self.detect_column_boundaries(column_title)
        column = row[boundaries[0]:boundaries[1]]
        return column.strip()


class SystemctlListTimersResource(nagiosplugin.Resource):
    """
    Resource that calls ``systemctl list-timers --all`` on the command line to
    get informations about dead / inactive timers. There is one type of systemd
    “degradation” which is normally not detected: dead / inactive timers.

    :param list excludes: A list of systemd unit names to exclude from the
      checks.
    """

    def __init__(self, excludes=[], *args, **kwargs):
        self.excludes = excludes
        self.warning = kwargs.pop('warning')
        self.critical = kwargs.pop('critical')
        super().__init__(*args, **kwargs)

    name = 'SYSTEMD'

    column_names = [
        'NEXT', 'LEFT', 'LAST', 'PASSED', 'UNIT', 'ACTIVATES'
    ]

    column_boundaries = None

    def re_match(self, unit):
        for exclude in self.excludes:
            if re.match(exclude, unit):
                return(True)
        return(False)

    def detect_column_boundaries(self, heading):
        boundaries = []
        previous_column_start = 0
        for column_title in self.column_names[1:]:
            next_column_start = heading.index(column_title)
            boundaries.append([previous_column_start, next_column_start])
            previous_column_start = next_column_start
        return boundaries

    def get_column_text(self, row, column_name):
        boundaries = self.column_boundaries[
            self.column_names.index(column_name)
        ]
        return row[boundaries[0]:boundaries[1]].strip()

    def probe(self):
        """
        :return: generator that emits
          :class:`~nagiosplugin.metric.Metric` objects
        """
        stdout = execute_cli(['systemctl', 'list-timers', '--all'])

        # NEXT                          LEFT
        # Sat 2020-05-16 15:11:15 CEST  34min left

        # LAST                          PASSED
        # Sat 2020-05-16 14:31:56 CEST  4min 20s ago

        # UNIT             ACTIVATES
        # apt-daily.timer  apt-daily.service
        if stdout:
            lines = stdout.splitlines()
            table_heading = lines[0]
            self.column_boundaries = self.detect_column_boundaries(
                table_heading
            )
            # Remove the first line because it is the header.
            # Remove the two last lines: empty line + "XX timers listed."
            table_body = lines[1:-2]

            state = nagiosplugin.Ok  # ok

            for row in table_body:
                unit = self.get_column_text(row, 'UNIT')
                if self.re_match(unit):
                    continue
                next_date_time = self.get_column_text(row, 'NEXT')

                if next_date_time == 'n/a':
                    passed_text = self.get_column_text(row, 'PASSED')

                    if passed_text == 'n/a':
                        state = nagiosplugin.Critical
                    else:
                        passed = format_timespan_to_seconds(
                            passed_text
                        )

                        if passed_text == 'n/a' or passed >= self.critical:
                            state = nagiosplugin.Critical
                        elif passed >= self.warning:
                            state = nagiosplugin.Warn

                yield Metric(
                    name=unit,
                    value=state,
                    context='dead_timers'
                )


class SystemctlIsActiveResource(nagiosplugin.Resource):
    """Resource that calls ``systemctl is-active <service>`` on the command
    line to get informations about one specifiy systemd unit."""

    name = 'SYSTEMD'

    def __init__(self, *args, **kwargs):
        self.unit = kwargs.pop('unit')
        super().__init__(*args, **kwargs)

    def probe(self):
        """Query system state and return metrics.

        :return: generator that emits
          :class:`~nagiosplugin.metric.Metric` objects
        """
        # Execute `systemctl is-active <service>` and get output
        # - active
        # - inactive (by unkown unit file)
        # - failed
        stdout = execute_cli(['systemctl', 'is-active', self.unit])
        if stdout:
            for line in io.StringIO(stdout):
                active = line.strip()
                yield Metric(name=self.unit, value=active, context='unit')


class UnitContext(nagiosplugin.Context):

    def __init__(self):
        super(UnitContext, self).__init__('unit')

    def evaluate(self, metric, resource):
        """Determines state of a given metric.

        :param metric: associated metric that is to be evaluated
        :param resource: resource that produced the associated metric
            (may optionally be consulted)

        :returns: :class:`~.result.Result`
        """
        if isinstance(metric.value, Unit):
            unit_state = metric.value
            hint = '{}: {}'.format(metric.name, unit_state.active_state)
            return self.result_cls(unit_state.convert_to_exitcode(),
                                   metric=metric, hint=hint)
        if metric.value:
            hint = '{}: {}'.format(metric.name, metric.value)
        else:
            hint = metric.name

        # The option -u is not specifed
        if not metric.value:
            return self.result_cls(nagiosplugin.Ok, metric=metric, hint=hint)

        if opts.ignore_inactive_state and metric.value == 'failed':
            return self.result_cls(nagiosplugin.Critical, metric=metric,
                                   hint=hint)
        elif not opts.ignore_inactive_state and metric.value != 'active':
            return self.result_cls(nagiosplugin.Critical, metric=metric,
                                   hint=hint)
        else:
            return self.result_cls(nagiosplugin.Ok, metric=metric, hint=hint)


class DeadTimersContext(nagiosplugin.Context):

    def __init__(self):
        super(DeadTimersContext, self).__init__('dead_timers')

    def evaluate(self, metric, resource):
        """Determines state of a given metric.

        :param metric: associated metric that is to be evaluated
        :param resource: resource that produced the associated metric
            (may optionally be consulted)

        :returns: :class:`~.result.Result`
        """
        return self.result_cls(metric.value, metric=metric, hint=metric.name)


class PerformanceDataContext(nagiosplugin.Context):

    def __init__(self):
        super(PerformanceDataContext, self).__init__('performance_data')

    def performance(self, metric, resource):
        """Derives performance data from a given metric.

        :param metric: associated metric from which performance data are
            derived
        :param resource: resource that produced the associated metric
            (may optionally be consulted)

        :returns: :class:`Perfdata` object
        """
        return nagiosplugin.Performance(label=metric.name, value=metric.value)


class SystemdSummary(nagiosplugin.Summary):
    """Format the different status lines. A subclass of `nagiosplugin.Summary
    <https://github.com/mpounsett/nagiosplugin/blob/master/nagiosplugin/summary.py>`_.
    """

    def ok(self, results):
        """Formats status line when overall state is ok.

        :param results: :class:`~nagiosplugin.result.Results` container
        :returns: status line
        """
        for result in results.most_significant:
            if isinstance(result.context, UnitContext):
                return '{0}'.format(result)
        return 'all'

    def problem(self, results):
        """Formats status line when overall state is not ok.

        :param results: :class:`~.result.Results` container

        :returns: status line
        """
        summary = []
        for result in results.most_significant:
            if result.context.name in ['startup_time', 'unit', 'dead_timers']:
                summary.append(result)
        return ', '.join(['{0}'.format(result) for result in summary])

    def verbose(self, results):
        """Provides extra lines if verbose plugin execution is requested.

        :param results: :class:`~.result.Results` container

        :returns: list of strings
        """
        summary = []
        for result in results.most_significant:
            if result.context.name in ['startup_time', 'unit', 'dead_timers']:
                summary.append('{0}: {1}'.format(result.state, result))
        return summary


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

    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Increase output verbosity (use up to 3 times).'
    )

    parser.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s {}'.format(__version__),
    )

    unit = parser.add_argument_group(
        'Options related to unit selection',
        'By default all systemd units are checked. '
        'Use the option \'-e\' to exclude units \nby a regular expression. '
        'Use the option \'-u\' to check only one unit.'
    )

    unit_exclusive_group = unit.add_mutually_exclusive_group()

    unit_exclusive_group.add_argument(
        '-u', '--unit',
        type=str,
        dest='unit',
        help='Name of the systemd unit that is being tested.',
    )

    unit.add_argument(
        '-i', '--ignore-inactive-state',
        action='store_true',
        help='Ignore an inactive state on a specific unit. Oneshot services '
             'for example are only active while running and not enabled. '
             'The rest of the time they are inactive. This option has only '
             'an affect if it is used with the option -u.'
    )

    unit_exclusive_group.add_argument(
        '-e', '--exclude',
        metavar='UNIT',
        action='append',
        default=[],
        help='Exclude a systemd unit from the checks. This option can be '
             'applied multiple times, for example: -e mnt-data.mount -e '
             'task.service. Regular expressions can be used to exclude '
             'multiple units at once, for example: '
             '-e \'user@\\d+\\.service\'. '
             'For more informations see the Python documentation about '
             'regular expressions '
             '(https://docs.python.org/3/library/re.html).',
    )

    startup_time = parser.add_argument_group('Startup time related options')

    startup_time.add_argument(
        '-n', '--no-startup-time',
        action='store_true',
        default=False,
        help='Don’t check the startup time. Using this option the options '
             '\'-w, --warning\' and \'-c, --critical\' have no effect. '
             'Performance data about the startup time is collected, but '
             'no critical, warning etc. states are triggered.',
    )

    startup_time.add_argument(
        '-w', '--warning',
        default=60,
        metavar='SECONDS',
        help='Startup time in seconds to result in a warning status. The'
             'default is 60 seconds.',
    )

    startup_time.add_argument(
        '-c', '--critical',
        metavar='SECONDS',
        default=120,
        help='Startup time in seconds to result in a critical status. The'
             'default is 120 seconds.',
    )

    dead_timer = parser.add_argument_group('Timers related options')

    dead_timer.add_argument(
        '-t', '--dead-timers',
        action='store_true',
        help='Detect dead / inactive timers. See the corresponding options '
             '\'-W, --dead-timer-warning\' and '
             '\'-C, --dead-timers-critical\'. '
             'Dead timers are detected by parsing the output of '
             '\'systemctl list-timers\'. '
             'Dead timer rows displaying \'n/a\' in the NEXT and LEFT '
             'columns and the time span in the column PASSED exceeds the '
             'values specified with the options \'-W, --dead-timer-warning\' '
             'and \'-C, --dead-timers-critical\'.'
    )

    dead_timer.add_argument(
        '-W', '--dead-timers-warning',
        metavar='SECONDS',
        type=float,
        default=60 * 60 * 24 * 6,
        help='Time ago in seconds for dead / inactive timers to trigger a '
             'warning state (by default 6 days).'
    )

    dead_timer.add_argument(
        '-C', '--dead-timers-critical',
        metavar='SECONDS',
        type=float,
        default=60 * 60 * 24 * 7,
        help='Time ago in seconds for dead / inactive timers to trigger a '
             'critical state (by default 7 days).'
    )

    acquisition = parser.add_argument_group('Monitoring data acquisition')
    acquisition_exclusive_group = acquisition.add_mutually_exclusive_group()

    acquisition_exclusive_group.add_argument(
        '--dbus',
        action='store_true',
        help='Use the systemd’s D-Bus API instead of parsing the text output '
             'of various systemd related command line interfaces to monitor '
             'systemd. At the moment the D-Bus backend of this plugin is '
             'only partially implemented.'
    )

    acquisition_exclusive_group.add_argument(
        '--cli',
        action='store_true',
        help='Use the text output of serveral systemd command line interface '
             '(cli) binaries to gather the required data for the monitoring '
             'process.'
    )

    return parser


def main():
    """The main entry point of the monitoring plugin. First the command line
    arguments are read into the variable ``opts``. The configuration of this
    ``opts`` object decides which instances of the `Resource
    <https://github.com/mpounsett/nagiosplugin/blob/master/nagiosplugin/resource.py>`_,
    `Context
    <https://github.com/mpounsett/nagiosplugin/blob/master/nagiosplugin/context.py>`_
    and `Summary
    <https://github.com/mpounsett/nagiosplugin/blob/master/nagiosplugin/summary.py>`_
    subclasses are assembled in a list called ``tasks``. This list is passed
    the main class of the ``nagiosplugin`` library: the `Check
    <https://nagiosplugin.readthedocs.io/en/stable/api/core.html#nagiosplugin-check>`_
    class.
    """
    global opts
    opts = get_argparser().parse_args()

    if opts.dbus and data_source == 'cli':
        print('D-Bus backend could not be used. Fall back to the CLI backend.')

    use_dbus = False
    if opts.dbus and data_source == 'dbus':
        use_dbus = True

    tasks = []

    if opts.dead_timers:
        tasks += [
            SystemctlListTimersResource(
                excludes=opts.exclude,
                warning=opts.dead_timers_warning,
                critical=opts.dead_timers_critical,
            ),
            DeadTimersContext()
        ]

    if opts.unit:
        if use_dbus:
            tasks.append(DbusSingleUnitResource(unit=opts.unit))
        else:
            tasks.append(SystemctlIsActiveResource(unit=opts.unit))
    else:
        if use_dbus:
            tasks.append(DbusAllUnitsResource())
        else:
            tasks += [
                SystemctlListUnitsResource(excludes=opts.exclude),
                PerformanceDataContext(),
            ]
            analyse = subprocess.run(
                ['systemd-analyze'],
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            # systemd-analyze: boot not finshed exits with 1
            if analyse.returncode == 0:
                tasks.append(SystemdAnalyseResource())

    tasks += [
        UnitContext(),
        SystemdSummary()
    ]

    if not opts.no_startup_time:
        tasks.append(
            nagiosplugin.ScalarContext(
                name='startup_time',
                warning=opts.warning,
                critical=opts.critical,
            )
        )
    else:
        tasks.append(
            nagiosplugin.ScalarContext(
                name='startup_time'
            )
        )

    check = nagiosplugin.Check(*tasks)
    check.main(opts.verbose)


if __name__ == '__main__':
    main()
