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

import nagiosplugin
from nagiosplugin import Metric

__version__ = '2.0.2'


class SystemdStatus(nagiosplugin.Resource):
    """
    :param list excludes: A list of systemd unit names.
    """
    name = 'SYSTEMD'

    def __init__(self, excludes=[]):
        self.excludes = excludes

    def probe(self):
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


class ServiceStatus(nagiosplugin.Resource):
    name = 'SYSTEMD'

    def __init__(self, *args, **kwargs):
        self.unit = kwargs.pop('unit')
        self.failed_units = 0
        super(nagiosplugin.Resource, self).__init__(*args, **kwargs)

    def probe(self):
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
                if active == 'failed':
                    yield Metric(name='failed_units', value=1,
                                 context='performance_data')
                yield Metric(name=self.unit, value=active, context='unit')


class UnitContext(nagiosplugin.Context):

    def __init__(self):
        super(UnitContext, self).__init__('unit')

    def evaluate(self, metric, resource):
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
        return nagiosplugin.Performance(label=metric.name, value=metric.value)


class SystemdSummary(nagiosplugin.Summary):

    def ok(self, results):
        for result in results.most_significant:
            if isinstance(result.context, UnitContext):
                return '{0}'.format(result)
        return 'all'

    def problem(self, results):
        show = []
        for result in results.most_significant:
            if isinstance(result.context, UnitContext):
                show.append(result)
        return ', '.join(['{0}'.format(result) for result in show])

    def verbose(self, results):
        show = []
        for result in results.most_significant:
            if isinstance(result.context, UnitContext):
                show.append(result)
        return ['{0}: {1}'.format(result.state, result) for result in show]


def get_argparser():
    parser = argparse.ArgumentParser(
        description='Nagios / Icinga monitoring plugin to check systemd for '
                    'failed units.'
    )

    exclusive_group = parser.add_mutually_exclusive_group()

    exclusive_group.add_argument(
        '-e', '--exclude',
        metavar='UNIT',
        action='append',
        default=[],
        help='Exclude a systemd unit from the checks. This option can be '
             'applied multiple times. For example: -e mnt-data.mount -e '
             'task.service'
    )

    exclusive_group.add_argument(
        '-u', '--unit',
        type=str,
        dest='unit',
        help='Name of the systemd unit that is beeing tested.'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Increase output verbosity (use up to 3 times)'
    )

    return parser


def main():
    args = get_argparser().parse_args()

    if args.unit:
        resource = ServiceStatus(unit=args.unit)
    else:
        resource = SystemdStatus(excludes=args.exclude)

    check = nagiosplugin.Check(
        resource,
        UnitContext(),
        PerformanceDataContext(),
        SystemdSummary()
    )

    check.main(args.verbose)


if __name__ == '__main__':
    main()
