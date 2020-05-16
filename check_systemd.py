#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
You can redistribute it and/or modify it under the terms of the GNU General
Public License as published by the Free Software Foundation, either version 2
of the License.
Copyright see argparse help text.
"""
import io
import subprocess
import argparse
import re

import nagiosplugin
from nagiosplugin import Metric

__version__ = '2.1.0'


class SystemdctlListUnitsResource(nagiosplugin.Resource):
    """
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
            p = subprocess.Popen(['systemctl', 'list-units', '--all',
                                  '--no-legend'],
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
            # Output of `systemctl list-units --all --no-legend`:
            # UNIT           LOAD   ACTIVE SUB     JOB   DESCRIPTION
            # foobar.service loaded active waiting       Description text
            count_units = 0
            for line in io.StringIO(stdout.decode('utf-8')):
                split_line = line.split()
                # foobar.service
                unit = split_line[0]
                # failed
                active = split_line[2]
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

    :param str fmt_timespan: for example `2.345s` or `3min 45.234s`

    :return: The seconds
    :rtype: float
    """
    seconds = {
        'y': 365 * 24 * 60 * 60,
        'month': 30 * 24 * 60 * 60,
        'w': 7 * 24 * 60 * 60,
        'd': 24 * 60 * 60,
        'h': 60 * 60,
        'min': 60,
        's': 1,
        'ms': 0.001,
    }
    result = 0
    for span in fmt_timespan.split():
        match = re.search(r'([\d\.]+)([a-z]+)', span)
        value = match.group(1)
        unit = match.group(2)
        result += float(value) * seconds[unit]
    return round(float(result), 3)


class SystemdAnalyseResource(nagiosplugin.Resource):

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


class SystemctlListTimersResource(nagiosplugin.Resource):
    """There is one type of systemd "degradation" which is normally not
    detected: dead / inactive timers.
    """

    name = 'SYSTEMD'

    column_names = [
      'NEXT', 'LEFT', 'LAST', 'PASSED', 'UNIT', 'ACTIVATES'
    ]

    column_boundaries = None

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
        return row[boundaries[0]:boundaries[1]]

    def probe(self):
        """
        :return: generator that emits
          :class:`~nagiosplugin.metric.Metric` objects
        """
        try:
            p = subprocess.Popen(['systemctl', '--all', 'list-timers'],
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
            # Remove the first line because it is the header.
            # Remove the two last lines: empty line + "XX timers listed."
            # table_body = lines[1:-2]
            self.column_boundaries = self.detect_column_boundaries(
                table_heading
            )
            # for row in table_body:
            #     print(self.get_column_text(row, 'UNIT'))

        yield Metric(name='default', value=True)


class SystemctlIsActiveResource(nagiosplugin.Resource):

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

    def __init__(self):
        super(UnitContext, self).__init__('unit')

    def evaluate(self, metric, resource):
        """Determines state of a given metric.

        :param metric: associated metric that is to be evaluated
        :param resource: resource that produced the associated metric
            (may optionally be consulted)
        :returns: :class:`~.result.Result`
        """
        hint = '%s: %s' % (metric.name, metric.value) \
            if metric.value else metric.name
        if metric.value and metric.value != 'active':
            return self.result_cls(nagiosplugin.Critical, metric=metric,
                                   hint=hint)
        else:
            return self.result_cls(nagiosplugin.Ok, metric=metric, hint=hint)


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
            if result.context.name in ['startup_time', 'unit']:
                summary.append(result)
        return ', '.join(['{0}'.format(result) for result in summary])

    def verbose(self, results):
        """Provides extra lines if verbose plugin execution is requested.

        :param results: :class:`~.result.Results` container
        :returns: list of strings
        """
        summary = []
        for result in results.most_significant:
            if result.context.name in ['startup_time', 'unit']:
                summary.append('{0}: {1}'.format(result.state, result))
        return summary


def get_argparser():
    parser = argparse.ArgumentParser(
        prog='check_systemd',  # To get the right command name in the README.
        formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=80),  # noqa: E501
        description=  # noqa: E251
        'Copyright (c) 2014-18 Andrea Briganti a.k.a \'Kbyte\' <kbytesys@gmail.com>\n'  # noqa: E501
        'Copyright (c) 2019-20 Josef Friedrich <josef@friedrich.rocks>\n'
        '\n'
        'Nagios / Icinga monitoring plugin to check systemd for failed units.\n',  # noqa: E501
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

    parser.add_argument(
        '-c', '--critical',
        metavar='SECONDS',
        default=120,
        help='Startup time in seconds to result in critical status.',
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

    exclusive_group.add_argument(
        '-u', '--unit',
        type=str,
        dest='unit',
        help='Name of the systemd unit that is being tested.',
    )

    parser.add_argument(
        '-t', '--dead-timers',
        action='store_true',
        help='Check for dead / inactive timers.'
    )

    parser.add_argument(
        '--dead-timers-critical',
        type=float,
        default=60 * 60 * 24 * 7,
        help='Critical time ago in seconds for dead / inactive timers.'
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

    parser.add_argument(
        '-w', '--warning',
        default=60,
        metavar='SECONDS',
        help='Startup time in seconds to result in warning status.',
    )

    return parser


def main():
    args = get_argparser().parse_args()

    objects = []

    if args.dead_timers:
        objects.append(SystemctlListTimersResource())

    if args.unit:
        objects.append(SystemctlIsActiveResource(unit=args.unit))
    else:
        objects += [
            SystemdctlListUnitsResource(excludes=args.exclude),
            PerformanceDataContext(),
        ]
        analyse = subprocess.run(['systemd-analyze'], stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        # systemd-analyze: boot not finshed exits with 1
        if analyse.returncode == 0:
            objects.append(SystemdAnalyseResource())

    objects += [
        UnitContext(),
        nagiosplugin.ScalarContext(
            name='startup_time',
            warning=args.warning,
            critical=args.critical,
        ),
        SystemdSummary()
    ]

    check = nagiosplugin.Check(*objects)
    check.main(args.verbose)


if __name__ == '__main__':
    main()
