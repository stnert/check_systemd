#! /usr/bin/python3

"""
A little script to explore the D-Bus API of systemd using dbus-python.
"""

import utils

# https://dbus.freedesktop.org/doc/dbus-python/

import dbus

unit_name = 'apt-daily.timer'

bus = dbus.SystemBus()
systemd = bus.get_object(
    'org.freedesktop.systemd1',
    '/org/freedesktop/systemd1'
)

manager = dbus.Interface(
    systemd,
    'org.freedesktop.systemd1.Manager'
)


def print_all_properties_of_object(object_path: str, interface_name='org.freedesktop.systemd1.Unit') -> str:
    """
    :param object_path: for example /org/freedesktop/systemd1/unit/apt_2ddaily_2eservice
    :param interface_name: for example org.freedesktop.systemd1.Service
    """

    print(utils.format_colorized_heading(interface_name))
    proxy = bus.get_object('org.freedesktop.systemd1',
                           object_path,)

    interface = dbus.Interface(
        proxy, dbus_interface="org.freedesktop.DBus.Properties")

    # https://dbus.freedesktop.org/doc/dbus-specification.html#standard-interfaces-properties
    properties = interface.GetAll(
        interface_name)
    for key, value in properties.items():
        print(utils.colorize_key_value(key, value))


for (name, description, load, active, sub_state, followed_unit, object_path,
        job_id, job_type, job_object_path) in manager.ListUnits():
    print()
    print(name)
    print(object_path)

    proxy = bus.get_object('org.freedesktop.systemd1',
                           object_path,)

    print_all_properties_of_object(object_path)
    print_all_properties_of_object(
        object_path, utils.get_interface_name_from_object_path(object_path))
