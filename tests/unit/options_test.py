# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from lstail.options import LstailArgumentParser
from tests.base import BaseTestCase


class OptionsTest(BaseTestCase):

    # ----------------------------------------------------------------------
    def test_option_unknown(self):
        parser = LstailArgumentParser(['--unknown-option-which-will-never-exist-abcdefgh'])
        with self.assertRaises(SystemExit):
            parser.parse()

    # ----------------------------------------------------------------------
    def test_flag_verbose(self):
        self._test_flag('v', 'verbose', 'verbose')

    # ----------------------------------------------------------------------
    def _test_flag(self, option_short_name, option_long_name, name):
        # short name
        if option_short_name is not None:
            parser = LstailArgumentParser(['-{}'.format(option_short_name)])
            arguments = parser.parse()
            self.assertTrue(getattr(arguments, name))

        # long name
        parser = LstailArgumentParser(['--{}'.format(option_long_name)])
        arguments = parser.parse()
        self.assertTrue(getattr(arguments, name))

        # not set
        parser = LstailArgumentParser([])
        arguments = parser.parse()
        self.assertFalse(getattr(arguments, name))

    # ----------------------------------------------------------------------
    def test_flag_debug(self):
        self._test_flag('d', 'debug', 'debug')

    # ----------------------------------------------------------------------
    def test_flag_follow(self):
        self._test_flag('f', 'follow', 'follow')

    # ----------------------------------------------------------------------
    def test_flag_no_header(self):
        self._test_flag('H', 'no-header', 'no_header')

    # ----------------------------------------------------------------------
    def test_flag_csv(self):
        self._test_flag(None, 'csv', 'csv_output')

    # ----------------------------------------------------------------------
    def test_flag_version(self):
        self._test_flag('V', 'version', 'version')

    # ----------------------------------------------------------------------
    def test_flag_list_searches(self):
        self._test_flag('l', 'list-saved-searches', 'kibana_list_saved_searches')

    # ----------------------------------------------------------------------
    def test_flag_select_saved_search(self):
        self._test_flag(None, 'select-saved-search', 'select_kibana_saved_search')

    # ----------------------------------------------------------------------
    def test_option_config_file(self):
        self._test_option('c', 'config', 'config_file_path', 'test config file path')

    # ----------------------------------------------------------------------
    def _test_option(self, option_short_name, option_long_name, name, value):
        # short name
        parser = LstailArgumentParser(['-{}'.format(option_short_name), str(value)])
        arguments = parser.parse()
        short_name_value = getattr(arguments, name)
        self.assertEqual(short_name_value, value)

        # long name
        parser = LstailArgumentParser(['--{}'.format(option_long_name), str(value)])
        arguments = parser.parse()
        long_name_value = getattr(arguments, name)
        self.assertEqual(long_name_value, value)

    # ----------------------------------------------------------------------
    def test_option_query(self):
        self._test_option('q', 'query', 'custom_search', 'test query')

    # ----------------------------------------------------------------------
    def test_option_range(self):
        self._test_option('r', 'range', 'initial_time_range', 'test range')

    # ----------------------------------------------------------------------
    def test_option_lines(self):
        self._test_option('n', 'lines', 'initial_query_size', 42)

    # ----------------------------------------------------------------------
    def test_option_saved_search(self):
        self._test_option('s', 'saved-search', 'kibana_saved_search', 'test saved search')

    # ----------------------------------------------------------------------
    def test_option_exclusive_group_initial_query(self):
        parser = LstailArgumentParser(['--lines', '5', '--range', '4d'])
        with self.assertRaises(SystemExit):
            parser.parse()

        parser = LstailArgumentParser(['-n', '5', '-r', '4d'])
        with self.assertRaises(SystemExit):
            parser.parse()

    # ----------------------------------------------------------------------
    def test_option_exclusive_group_actions(self):
        parser = LstailArgumentParser(['--list-saved-searches', '--version'])
        with self.assertRaises(SystemExit):
            parser.parse()

        parser = LstailArgumentParser(['-l', '-V'])
        with self.assertRaises(SystemExit):
            parser.parse()
