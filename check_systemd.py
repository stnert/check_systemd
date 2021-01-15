#!/usr/bin/env python3

"""
``check_system`` is a Nagios / Icinga monitoring plugin to check systemd.

This plugin is based on a Python package named `nagiosplugin
<https://pypi.org/project/nagiosplugin/>`_. ``nagiosplugin`` has a fine-grained
class model to separate concerns. A Nagios / Icinga plugin need to perform
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

* :class:`DeadTimersContext`
* :class:`PerformanceDataContext`
* :class:`UnitContext`

Presentation (``Summary``)
==========================

* :class:`SystemdSummary`
"""
import io
import subprocess
import argparse
import re

import nagiosplugin
from nagiosplugin import Metric

__version__ = '2.3.0'


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
        try:
            # p = subprocess.Popen(['./test/bin/ok/systemctl', 'list-units', '--all'],  # noqa: E501
            p = subprocess.Popen(['systemctl', 'list-units', '--all'],
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
            stdout, stderr = p.communicate()
        except OSError as e:
            raise nagiosplugin.CheckError(e)

        if stderr:
            raise nagiosplugin.CheckError(stderr)

        # Dictionary to store all units according their active state.
        units = {
            'failed': [],
            'active': [],
            'activating': [],
            'inactive': [],
        }
        if stdout:
            lines = stdout.decode('utf-8').splitlines()
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
    """Convert a timespan format string into secondes.

    https://github.com/systemd/systemd/blob/master/src/basic/time-util.c#L357

    :param str fmt_timespan: for example `2.345s` or `3min 45.234s` or
      `34min left` or `2 months 8 days`

    :return: The seconds
    :rtype: float
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


class SystemdAnalyseResource(nagiosplugin.Resource):
    """Resource that calls ``systemd-analyze`` on the command line to get
    informations about the startup time.."""

    name = 'SYSTEMD'

    def probe(self):
        """Query system state and return metrics.

        :return: generator that emits
          :class:`~nagiosplugin.metric.Metric` objects
        """
        try:
            p = subprocess.Popen(['systemd-analyze'],
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
        try:
            p = subprocess.Popen(['systemctl', 'list-timers', '--all'],
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
            stdout, stderr = p.communicate()
        except OSError as e:
            raise nagiosplugin.CheckError(e)

        if stderr:
            raise nagiosplugin.CheckError(stderr)

        # NEXT                          LEFT
        # Sat 2020-05-16 15:11:15 CEST  34min left

        # LAST                          PASSED
        # Sat 2020-05-16 14:31:56 CEST  4min 20s ago

        # UNIT             ACTIVATES
        # apt-daily.timer  apt-daily.service
        if stdout:
            lines = stdout.decode('utf-8').splitlines()
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
        try:
            p = subprocess.Popen(['systemctl', 'is-active', self.unit],
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
            stdout, stderr = p.communicate()
        except OSError as e:
            raise nagiosplugin.CheckError(e)

        if stderr:
            raise nagiosplugin.CheckError(stderr)
        if stdout:
            for line in io.StringIO(stdout.decode('utf-8')):
                active = line.strip()
                yield Metric(name=self.unit, value=active, context='unit')


class UnitContext(nagiosplugin.Context):

    def __init__(self, args):
        self.args = args
        super(UnitContext, self).__init__('unit')

    def evaluate(self, metric, resource):
        """Determines state of a given metric.

        :param metric: associated metric that is to be evaluated
        :param resource: resource that produced the associated metric
            (may optionally be consulted)
        :returns: :class:`~.result.Result`
        """
        if metric.value:
            hint = '{}: {}'.format(metric.name, metric.value)
        else:
            hint = metric.name

        # The option -u is not specifed
        if not metric.value:
            return self.result_cls(nagiosplugin.Ok, metric=metric, hint=hint)

        if self.args.ignore_inactive_state and metric.value == 'failed':
            return self.result_cls(nagiosplugin.Critical, metric=metric,
                                   hint=hint)
        elif not self.args.ignore_inactive_state and metric.value != 'active':
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
        'Copyright (c) 2014-18 Andrea Briganti a.k.a \'Kbyte\' <kbytesys@gmail.com>\n'  # noqa: E501
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

    exclusive_group.add_argument(
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

    parser.add_argument(
        '-n', '--no-startup-time',
        action='store_true',
        default=False,
        help='Don’t check the startup time. Using this option the options '
             '\'-w, --warning\' and \'-c, --critical\' have no effect. '
             'Performance data about the startup time is collected, but '
             'no critical, warning etc. states are triggered.',
    )

    parser.add_argument(
        '-w', '--warning',
        default=60,
        metavar='SECONDS',
        help='Startup time in seconds to result in a warning status. The'
             'default is 60 seconds.',
    )

    parser.add_argument(
        '-c', '--critical',
        metavar='SECONDS',
        default=120,
        help='Startup time in seconds to result in a critical status. The'
             'default is 120 seconds.',
    )

    parser.add_argument(
        '-t', '--dead-timers',
        action='store_true',
        help='Detect dead / inactive timers. See the corresponding options '
             '\'-W, --dead-timer-warning\' and '
             '\'-C, --dead-timers-critical\'. '
             'Dead timers are detected by parsing the output of '
             '\'systemctl list-timers\'. '
             'Dead timer rows displaying \'n/a\' in the NEXT and LEFT'
             'columns and the time span in the column PASSED exceeds the '
             'values specified with the options \'-W, --dead-timer-warning\' '
             'and \'-C, --dead-timers-critical\'.'
    )

    parser.add_argument(
        '-W', '--dead-timers-warning',
        metavar='SECONDS',
        type=float,
        default=60 * 60 * 24 * 6,
        help='Time ago in seconds for dead / inactive timers to trigger a '
             'warning state (by default 6 days).'
    )

    parser.add_argument(
        '-C', '--dead-timers-critical',
        metavar='SECONDS',
        type=float,
        default=60 * 60 * 24 * 7,
        help='Time ago in seconds for dead / inactive timers to trigger a '
             'critical state (by default 7 days).'
    )

    parser.add_argument(
        '-i', '--ignore-inactive-state',
        action='store_true',
        help='Ignore an inactive state on a specific unit. Oneshot services '
             'for example are only active while running and not enabled. '
             'The rest of the time they are inactive. This option has only '
             'an affect if it is used with the option -u.'
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

    return parser


def main():
    """The main function"""
    args = get_argparser().parse_args()

    objects = []

    if args.dead_timers:
        objects += [
            SystemctlListTimersResource(
                excludes=args.exclude,
                warning=args.dead_timers_warning,
                critical=args.dead_timers_critical,
            ),
            DeadTimersContext()
        ]

    if args.unit:
        objects.append(SystemctlIsActiveResource(unit=args.unit))
    else:
        objects += [
            SystemctlListUnitsResource(excludes=args.exclude),
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
            objects.append(SystemdAnalyseResource())

    objects += [
        UnitContext(args),
        SystemdSummary()
    ]

    if not args.no_startup_time:
        objects.append(
            nagiosplugin.ScalarContext(
                name='startup_time',
                warning=args.warning,
                critical=args.critical,
            )
        )
    else:
        objects.append(
            nagiosplugin.ScalarContext(
                name='startup_time'
            )
        )

    check = nagiosplugin.Check(*objects)
    check.main(args.verbose)


if __name__ == '__main__':
    main()
