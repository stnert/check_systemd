#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
You can redistribute it and/or modify it under the terms of the GNU General
Public License as published by the Free Software Foundation, either version 2
of the License.
Copyright 2014-18 Andrea Briganti a.k.a 'Kbyte'
Copyright 2019 Josef Friedrich
"""
import io
import subprocess
import argparse
import re

import nagiosplugin
from nagiosplugin import Metric

__version__ = '2.0.3'


class SystemdctlListUnitsResource(nagiosplugin.Resource):
    """
    :param list excludes: A list of systemd unit names.
    """
    name = 'SYSTEMD'

    def __init__(self, excludes=[]):
        self.excludes = excludes

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
                # Only count not excludes units.
                if unit not in self.excludes:
                    units[active].append(unit)
                    count_units += 1

            for unit in units['failed']:
                if unit not in self.excludes:
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
            # Second line:
            # graphical.target reached after 1min 2.154s in userspace
            match = re.search(r'reached after (.+) in userspace',
                              stdout.decode('utf-8'))

        yield Metric(name='startup_time',
                     value=format_timespan_to_seconds(match.group(1)),
                     context='startup_time')


class SystemctlIsActiveResource(nagiosplugin.Resource):

    name = 'SYSTEMD'

    def __init__(self, *args, **kwargs):
        self.unit = kwargs.pop('unit')
        super(nagiosplugin.Resource, self).__init__(*args, **kwargs)

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
        description='Nagios / Icinga monitoring plugin to check systemd for '
                    'failed units.'
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
             'applied multiple times. For example: -e mnt-data.mount -e '
             'task.service.',
    )

    exclusive_group.add_argument(
        '-u', '--unit',
        type=str,
        dest='unit',
        help='Name of the systemd unit that is beeing tested.',
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


@nagiosplugin.guarded
def main():
    args = get_argparser().parse_args()

    objects = []

    if args.unit:
        objects.append(SystemctlIsActiveResource(unit=args.unit))
    else:
        objects += [
            SystemdctlListUnitsResource(excludes=args.exclude),
            PerformanceDataContext(),
            SystemdAnalyseResource(),
        ]

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
