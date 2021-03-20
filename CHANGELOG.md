# Change log

## Master branch

* The D-Bus API can be used as a new data source. The options `--cli`
  and `--dbus` can be used to switch between the two data sources.
* The options `-i`, `--ignore-inactive-state` have been removed.
* The options `--dead-timers`, `--dead-timers-warning` and
  `--dead-timers-critical` have been renamed to `--timers`,
  `--timers-warning` and `--timers-critical`
* In the command line help, the options have been grouped according to
  their monitoring scope.
* The options `--include`, `--include-unit`, `--include-type`,
  `--exclude`, `--exclude-unit`, `--exclude-type` have been added to
  have better control over which units should be selected for testing.
