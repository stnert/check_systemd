#! /usr/bin/python3

"""
A little script to explore the D-Bus API of systemd.
"""

# https://dbus.freedesktop.org/doc/dbus-python/

import dbus

unit_name = 'sshd.service'

bus = dbus.SystemBus()
systemd = bus.get_object(
    'org.freedesktop.systemd1',
    '/org/freedesktop/systemd1'
)

manager = dbus.Interface(
    systemd,
    'org.freedesktop.systemd1.Manager'
)

unit_state = manager.GetUnitFileState(unit_name)
print(unit_state)


unit = manager.LoadUnit(unit_name)
print(unit)
