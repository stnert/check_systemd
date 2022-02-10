from colors import color
import typing
import re


UnitType = typing.Literal['service', 'service', 'socket', 'target', 'device',
                          'mount', 'automount', 'timer', 'swap', 'path',
                          'slice', 'scope']


def colorize_key_value(key: any, value: any) -> str:
    key = str(key)
    value = str(value)

    """Print a value of the structure returned by ListUnits()"""
    return "{}: {}".format(color(key, fg='green'),
                           color(value, fg='yellow'))


def format_colorized_heading(heading: str) -> str:
    return '\n{}'.format(color(heading, fg='red'))


def print_properties(properties: dict, filter: list = None):
    if filter:
        for key in filter:
            print(colorize_key_value(key, properties[key]))
        return

    for key, value in properties.items():
        print(colorize_key_value(key, value))


def get_interface_name_from_unit_name(unit_name: str) -> str:
    """
    :param name: for example apt-daily.service

    :return: org.freedesktop.systemd1.Service
    """
    name_segments = unit_name.split('.')
    interface_name = name_segments[-1]
    return 'org.freedesktop.systemd1.{}'.format(interface_name.title())


def get_interface_name_from_object_path(object_path: str) -> str:
    """
    :param object_path: for example
      /org/freedesktop/systemd1/unit/apt_2ddaily_2eservice

    :return: org.freedesktop.systemd1.Service
    """
    name_segments = object_path.split('_2e')
    interface_name = name_segments[-1]
    return 'org.freedesktop.systemd1.{}'.format(interface_name.title())


def is_unit_type(
        unit_name_or_object_path,
        type_name: UnitType) -> bool:
    return re.match(
        '.*(\\.|_2e)' + type_name + '$', unit_name_or_object_path) is not None
