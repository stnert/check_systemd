#! /usr/bin/python3

"""
A little script to explore the D-Bus API of systemd using dbus-python.
"""

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

unit_state = manager.GetUnitFileState(unit_name)
print(unit_state)


unit = manager.LoadUnit(unit_name)
print(unit)


proxy = bus.get_object('org.freedesktop.systemd1',
                      '/org/freedesktop/systemd1/unit/apt_2ddaily_2etimer',)

interface = dbus.Interface(
    proxy, dbus_interface="org.freedesktop.DBus.Properties")
# name = interface.Get("org.freedesktop.systemd1.Unit", 'Id')


properties = interface.GetAll(
    "org.freedesktop.systemd1.Unit")
for key, value in properties.items():
    print('{}: {}'.format(key, value))
