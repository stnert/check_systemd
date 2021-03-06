"""Tests related to data acquisition of systemd units."""

import unittest
from check_systemd import Unit, UnitCache


unit_modem_manager = Unit(name='ModemManager.service',
                          active_state='active', sub_state='sub',
                          load_state='load')
unit_mongod = Unit(name='mongod.service', active_state='active',
                   sub_state='sub', load_state='load')
unit_mysql = Unit(name='mysql.service', active_state='active',
                  sub_state='sub', load_state='load')
unit_named = Unit(name='named.service', active_state='active',
                  sub_state='sub', load_state='load')
unit_networking = Unit(name='networking.service',
                       active_state='active', sub_state='sub',
                       load_state='load')
unit_nginx = Unit(name='nginx.service', active_state='active',
                  sub_state='sub', load_state='load')
unit_nmdb = Unit(name='nmbd.service', active_state='active',
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

    def test_method_get(self):
        unit = self.unit_cache.get(name='ModemManager.service')
        self.assertEqual('ModemManager.service', unit.name)

    def test_method_list(self):
        units = []
        for unit in self.unit_cache.list():
            units.append(unit)

        self.assertEqual(8, len(units))


if __name__ == '__main__':
    unittest.main()
