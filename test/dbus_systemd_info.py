#! /usr/bin/python3

"""
A little script to explore the D-Bus API of systemd.
"""

from colors import color

# https://raw.githubusercontent.com/pengutronix/monitoring-check-systemd-service/master/check-systemd-service

try:
    from gi.repository.Gio import DBusProxy, BusType
except ImportError as e:
    print("Please install python3-gi")
    raise e

# https://lazka.github.io/pgi-docs/#Gio-2.0/classes/DBusProxy.html#Gio.DBusProxy

# https://www.freedesktop.org/wiki/Software/systemd/dbus/

dbus = DBusProxy.new_for_bus_sync(BusType.SYSTEM, 0, None,
                                  'org.freedesktop.systemd1',
                                  '/org/freedesktop/systemd1',
                                  'org.freedesktop.systemd1.Manager', None)


def load_unit(unit_name, interface='Unit'):
    """
    :param: The name of the systemd unit. For example apt-daily.timer or
      nginx.service
    :param interface: For example Unit or Timer
    """
    try:
        loaded_unit = dbus.LoadUnit('(s)', unit_name)
    except Exception as e:
        raise e

    return DBusProxy.new_for_bus_sync(BusType.SYSTEM,
                                      0, None, 'org.freedesktop.systemd1',
                                      loaded_unit,
                                      'org.freedesktop.systemd1.' + interface, None)



def get_unit_property(unit, property_name):
    """
    :param unit:
    https://www.freedesktop.org/wiki/Software/systemd/dbus/#unitobjects
    """
    return unit.get_cached_property(property_name).unpack()



def list_properties_of_unit(unit_name):
    unit = load_unit(unit_name)
    for property_name in unit.get_cached_property_names():
        print(property_name)


# print(dbus.get_name())
# org.freedesktop.systemd1

# print(dbus.get_flags())
# <flags 0 of type Gio.DBusProxyFlags>

# print(dbus.get_cached_property_names())
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

# print(dbus.get_cached_property('Version'))
# '245.4-4ubuntu3.2'

# print(dbus.ListUnits())

# https://www.freedesktop.org/software/systemd/man/org.freedesktop.systemd1.html
# ListUnits() returns an array with all currently loaded units. Note that units
# may be known by multiple names at the same name, and hence there might be
# more unit names loaded than actual units behind them. The array consists of
# structures with the following elements:


def print_unit_structure(description, value):
    """Print a value of the structure returned by ListUnits()"""
    print("{}: {}".format(color(description, fg='green'),
                          color(value, fg='yellow')))


def print_unit_property(dbus_unit, property_name):
    """Print a property of the dbus unit object"""
    print("{}: {}".format(color(property_name, fg='blue'),
                          get_unit_property(dbus_unit, property_name)))


def list_all_units():
    # ('time-set.target', 'System Time Set', 'loaded', 'active', 'active', '',
    # '/org/freedesktop/systemd1/unit/time_2dset_2etarget', 0, '', '/')
    for (name, description, load, active, sub_state, followed_unit, object_path,
        job_id, job_type, job_object_path) in dbus.ListUnits():
        print('\n{}\n'.format(color(name, fg='red')))

        # The primary unit name as string
        print_unit_structure("Primary unit name", name)

        # The human readable description string
        print_unit_structure("Human readable description", description)

        # The load state (i.e. whether the unit file has been loaded successfully)
        print_unit_structure("The load state", load)

        # The active state (i.e. whether the unit is currently started or not)
        print_unit_structure("The active state", active)

        # The sub state (a more fine-grained version of the active state that is
        # specific to the unit type, which the active state is not)
        print_unit_structure("The sub state", sub_state)

        # A unit that is being followed in its state by this unit, if there is any,
        # otherwise the empty string.
        print_unit_structure("The followed unit", followed_unit)

        print_unit_structure("The unit object path", object_path)

        # If there is a job queued for the job unit the numeric job id, 0 otherwise
        print_unit_structure("The numeric job id", job_id)

        # The job type as string
        print_unit_structure("The job type", job_type)

        print_unit_structure("The job object path", job_object_path)

        dbus_unit = load_unit(name)

        print_unit_property(dbus_unit, 'ActiveState')


def list_all_timers():
    # timers
    for (name, description, load, active, sub_state, followed_unit, object_path,
        job_id, job_type, job_object_path) in dbus.ListUnits():

        if '.timer' in name:
            print(name)
            dbus_unit = load_unit(name, 'Timer')

            try:
                print_unit_property(dbus_unit, 'TimersMonotonic')
                print_unit_property(dbus_unit, 'NextElapseUSecRealtime')

            except Exception as e:
                pass


list_properties_of_unit('apt-daily.timer')
