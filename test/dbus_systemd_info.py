#!/usr/bin/python3

# https://raw.githubusercontent.com/pengutronix/monitoring-check-systemd-service/master/check-systemd-service

try:
    from gi.repository.Gio import DBusProxy, BusType
except ImportError as e:
    print("Please install python3-gi")
    raise e

# https://lazka.github.io/pgi-docs/#Gio-2.0/classes/DBusProxy.html#Gio.DBusProxy

# https://www.freedesktop.org/wiki/Software/systemd/dbus/

dbus = DBusProxy.new_for_bus_sync(BusType.SYSTEM,
                                  0,
                                  None,
                                  'org.freedesktop.systemd1',
                                  '/org/freedesktop/systemd1',
                                  'org.freedesktop.systemd1.Manager',
                                  None)

print(dbus.get_name())
# org.freedesktop.systemd1

print(dbus.get_flags())
# <flags 0 of type Gio.DBusProxyFlags>

print(dbus.get_cached_property_names())
# ['Architecture', 'ConfirmSpawn', 'ControlGroup', 'DefaultBlockIOAccounting',
# 'DefaultCPUAccounting', 'DefaultLimitAS', 'DefaultLimitASSoft',
# 'DefaultLimitCORE', 'DefaultLimitCORESoft', 'DefaultLimitCPU',
# 'DefaultLimitCPUSoft', 'DefaultLimitDATA', 'DefaultLimitDATASoft',
# 'DefaultLimitFSIZE', 'DefaultLimitFSIZESoft', 'DefaultLimitLOCKS',
# 'DefaultLimitLOCKSSoft', 'DefaultLimitMEMLOCK', 'DefaultLimitMEMLOCKSoft',
# 'DefaultLimitMSGQUEUE', 'DefaultLimitMSGQUEUESoft', 'DefaultLimitNICE',
# 'DefaultLimitNICESoft', 'DefaultLimitNOFILE', 'DefaultLimitNOFILESoft',
# 'DefaultLimitNPROC', 'DefaultLimitNPROCSoft', 'DefaultLimitRSS',
# 'DefaultLimitRSSSoft', 'DefaultLimitRTPRIO', 'DefaultLimitRTPRIOSoft',
# 'DefaultLimitRTTIME', 'DefaultLimitRTTIMESoft', 'DefaultLimitSIGPENDING',
# 'DefaultLimitSIGPENDINGSoft', 'DefaultLimitSTACK', 'DefaultLimitSTACKSoft',
# 'DefaultMemoryAccounting', 'DefaultOOMPolicy', 'DefaultRestartUSec',
# 'DefaultStandardError', 'DefaultStandardOutput', 'DefaultStartLimitBurst',
# 'DefaultStartLimitIntervalUSec', 'DefaultTasksAccounting', 'DefaultTasksMax',
# 'DefaultTimeoutAbortUSec', 'DefaultTimeoutStartUSec',
# 'DefaultTimeoutStopUSec', 'DefaultTimerAccuracyUSec', 'Environment',
# 'ExitCode', 'Features', 'FinishTimestamp', 'FinishTimestampMonotonic',
# 'FirmwareTimestamp', 'FirmwareTimestampMonotonic',
# 'GeneratorsFinishTimestamp', 'GeneratorsFinishTimestampMonotonic',
# 'GeneratorsStartTimestamp', 'GeneratorsStartTimestampMonotonic',
# 'InitRDGeneratorsFinishTimestamp',
# 'InitRDGeneratorsFinishTimestampMonotonic', 'InitRDGeneratorsStartTimestamp',
# 'InitRDGeneratorsStartTimestampMonotonic', 'InitRDSecurityFinishTimestamp',
# 'InitRDSecurityFinishTimestampMonotonic', 'InitRDSecurityStartTimestamp',
# 'InitRDSecurityStartTimestampMonotonic', 'InitRDTimestamp',
# 'InitRDTimestampMonotonic', 'InitRDUnitsLoadFinishTimestamp',
# 'InitRDUnitsLoadFinishTimestampMonotonic', 'InitRDUnitsLoadStartTimestamp',
# 'InitRDUnitsLoadStartTimestampMonotonic', 'KExecWatchdogUSec',
# 'KernelTimestamp', 'KernelTimestampMonotonic', 'LoaderTimestamp',
# 'LoaderTimestampMonotonic', 'LogLevel', 'LogTarget', 'NFailedJobs',
# 'NFailedUnits', 'NInstalledJobs', 'NJobs', 'NNames', 'Progress',
# 'RebootWatchdogUSec', 'RuntimeWatchdogUSec', 'SecurityFinishTimestamp',
# 'SecurityFinishTimestampMonotonic', 'SecurityStartTimestamp',
# 'SecurityStartTimestampMonotonic', 'ServiceWatchdogs', 'ShowStatus',
# 'SystemState', 'Tainted', 'TimerSlackNSec', 'UnitPath',
# 'UnitsLoadFinishTimestamp', 'UnitsLoadFinishTimestampMonotonic',
# 'UnitsLoadStartTimestamp', 'UnitsLoadStartTimestampMonotonic',
# 'UserspaceTimestamp', 'UserspaceTimestampMonotonic', 'Version',
# 'Virtualization']

print(dbus.get_cached_property('Version'))
# '245.4-4ubuntu3.2'

# print(dbus.ListUnits())

# https://www.freedesktop.org/wiki/Software/systemd/dbus/
# ListUnits() returns an array with all currently loaded units. Note that units
# may be known by multiple names at the same name, and hence there might be
# more unit names loaded than actual units behind them. The array consists of
# structures with the following elements:

# The sub state (a more fine-grained version of the active state that is
# specific to the unit type, which the active state is not)

# A unit that is being followed in its state by this unit, if there is any,
# otherwise the empty string.

# The unit object path

# If there is a job queued for the job unit the numeric job id, 0 otherwise

# The job type as string

# The job object path

# ('time-set.target', 'System Time Set', 'loaded', 'active', 'active', '',
# '/org/freedesktop/systemd1/unit/time_2dset_2etarget', 0, '', '/')
for (name, description, load, active, _, _, _, _, _, _) in dbus.ListUnits():
    # The primary unit name as string
    print("\nPrimary unit name: {}".format(name))

    # The human readable description string
    print("Human readable description: {}".format(description))

    # The load state (i.e. whether the unit file has been loaded successfully)
    print("The load state: {}".format(load))

    # The active state (i.e. whether the unit is currently started or not)
    print("The active state: {}".format(active))
