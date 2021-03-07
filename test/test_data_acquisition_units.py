"""Tests related to data acquisition of systemd units."""

import unittest
from check_systemd import Unit, UnitCache, UnitNameFilter


unit_modem_manager = Unit(name='ModemManager.service',
                          active_state='active', sub_state='sub',
                          load_state='load')
unit_mongod = Unit(name='mongod.service', active_state='active',
                   sub_state='sub', load_state='load')
unit_mysql = Unit(name='mysql.service', active_state='active',
                  sub_state='sub', load_state='load')
unit_named = Unit(name='named.service', active_state='active',
                  sub_state='sub', load_state='load')
unit_networking = Unit(name='networking.mount',
                       active_state='active', sub_state='sub',
                       load_state='load')
unit_nginx = Unit(name='nginx.service', active_state='active',
                  sub_state='sub', load_state='load')
unit_nmdb = Unit(name='nmbd.timer', active_state='active',
                 sub_state='sub', load_state='load')
unit_php = Unit(name='php7.4-fpm.service', active_state='active',
                sub_state='sub', load_state='load')


class TestClassUnit(unittest.TestCase):

    def test_initialization(self):
        unit = Unit(name='test.service', active_state='active',
                    sub_state='sub', load_state='load')
        self.assertEqual('test.service', unit.name)
        self.assertEqual('active', unit.active_state)
        self.assertEqual('sub', unit.sub_state)
        self.assertEqual('load', unit.load_state)
        self.assertEqual('active', unit.active_state)


class TestClassUnitCache(unittest.TestCase):

    def setUp(self):
        self.unit_cache = UnitCache()
        self.unit_cache.add(unit_modem_manager)
        self.unit_cache.add(unit_mongod)
        self.unit_cache.add(unit_mysql)
        self.unit_cache.add(unit_named)
        self.unit_cache.add(unit_networking)
        self.unit_cache.add(unit_nginx)
        self.unit_cache.add(unit_modem_manager)
        self.unit_cache.add(unit_nmdb)
        self.unit_cache.add(unit_php)

    def list(self, include=None, exclude=None):
        units = []
        for unit in self.unit_cache.list(include=include, exclude=exclude):
            units.append(unit.name)
        return units

    def test_method_get(self):
        unit = self.unit_cache.get(name='ModemManager.service')
        self.assertEqual('ModemManager.service', unit.name)

    def test_method_list(self):
        units = self.list()
        self.assertEqual(8, len(units))

    def test_method_list_include(self):
        units = self.list(include='XXX')
        self.assertEqual(0, len(units))

        units = self.list(include='named.service')
        self.assertEqual(1, len(units))

        units = self.list(include='n.*')
        self.assertEqual(4, len(units))

    def test_method_list_include_multiple(self):
        units = self.list(include=('n.*', 'p.*'))
        self.assertEqual(5, len(units))

    def test_method_list_exclude(self):
        units = self.list(exclude='named.service')
        self.assertEqual(7, len(units))

        units = self.list(exclude=r'.*\.(mount|timer)')
        self.assertEqual(6, len(units))

    def test_method_list_exclude_multiple(self):
        units = self.list(exclude=('named.service', 'nmbd.timer'))
        self.assertEqual(6, len(units))


class TestClassUnitNameFilter(unittest.TestCase):

    def setUp(self):
        self.filter = UnitNameFilter()
        self.filter.add('ModemManager.service')
        self.filter.add('mongod.service')
        self.filter.add('mysql.service')
        self.filter.add('named.service')
        self.filter.add('networking.mount')
        self.filter.add('nginx.service')
        self.filter.add('nmbd.timer')
        self.filter.add('php7.4-fpm.service')

    def list(self, include=None, exclude=None):
        unit_names = []
        for unit_name in self.filter.list(include=include, exclude=exclude):
            unit_names.append(unit_name)
        return unit_names

    def test_initialization_with_arg(self):
        filter = UnitNameFilter(['test1.service', 'test2.service'])
        self.assertEqual(2, len(filter.get()))

    def test_method_list(self):
        units = self.list()
        self.assertEqual(8, len(units))

    def test_method_list_include(self):
        units = self.list(include='XXX')
        self.assertEqual(0, len(units))

        units = self.list(include='named.service')
        self.assertEqual(1, len(units))

        units = self.list(include='n.*')
        self.assertEqual(4, len(units))

    def test_method_list_include_multiple(self):
        units = self.list(include=('n.*', 'p.*'))
        self.assertEqual(5, len(units))

    def test_method_list_exclude(self):
        units = self.list(exclude='named.service')
        self.assertEqual(7, len(units))

        units = self.list(exclude=r'.*\.(mount|timer)')
        self.assertEqual(6, len(units))

    def test_method_list_exclude_multiple(self):
        units = self.list(exclude=('named.service', 'nmbd.timer'))
        self.assertEqual(6, len(units))

    def test_method_list_include_exclude_empty_list(self):
        units = self.list(include=[], exclude=[])
        self.assertEqual(8, len(units))


if __name__ == '__main__':
    unittest.main()
