# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from collections import OrderedDict
from configparser import ConfigParser, NoOptionError, NoSectionError

from lstail.config import LstailConfigParser
from lstail.dto.column import Column
from lstail.util.color import get_column_color_key
from tests.base import BaseTestCase, mock


# pylint: disable=protected-access

CONFIG_FILE_GENERAL_FALSE = '''
[general]
initial_query_size = 1
initial_time_range =
no_header = false
refresh_interval = 1
timeout = 1
verbose = false
verify_ssl_certificates = false
[kibana]
default_saved_search =
'''
CONFIG_FILE_GENERAL_UNSET = '''
[general]
initial_query_size = 1
initial_time_range =
no_header =
refresh_interval = 5
timeout = 1
verbose =
verify_ssl_certificates = true
[kibana]
default_saved_search =
'''
CONFIG_FILE_GENERAL_SET = '''
[general]
initial_query_size = 99
initial_time_range = 48h
no_header = true
header_color = red
refresh_interval = 1.4
timeout = 5.1
verbose = true
verify_ssl_certificates = true
[kibana]
default_saved_search = Test Search
'''
CONFIG_FILE_GENERAL_INVALID_FORMAT = '''
[general]
initial_query_size = maybe
initial_time_range = 48h
no_header = maybe
refresh_interval = 99.4
timeout = maybe
verbose = maybe
verify_ssl_certificates = maybe
[kibana]
default_saved_search = Test Search
'''


# ----------------------------------------------------------------------
def read_config_false(self):
    _read_config(self, CONFIG_FILE_GENERAL_FALSE)


# ----------------------------------------------------------------------
def read_config_unset(self):
    _read_config(self, CONFIG_FILE_GENERAL_UNSET)


# ----------------------------------------------------------------------
def read_config_invalid_format(self):
    _read_config(self, CONFIG_FILE_GENERAL_INVALID_FORMAT)


# ----------------------------------------------------------------------
def read_config_set(self):
    _read_config(self, CONFIG_FILE_GENERAL_SET)


# ----------------------------------------------------------------------
def read_config_missing_section(self):
    _read_config(self, '')


# ----------------------------------------------------------------------
def read_config_missing_value(self):
    _read_config(self, '[general]')


# ----------------------------------------------------------------------
def _read_config(self, config_file_content):
    self._config_parser = ConfigParser()
    self._config_parser.read_string(config_file_content)


class ConfigTest(BaseTestCase):

    # ----------------------------------------------------------------------
    def setUp(self):
        super().setUp()

        # full config read
        test_args = mock.Mock(
            config_file_path='tests/test_data/lstail_test.conf',
            custom_search='_exists_: message',
            kibana_saved_search=None,
            no_header=None,
            debug=None,
            csv_output=None,
            verbose=None,
            initial_query_size=None,
            initial_time_range=None)
        parser = LstailConfigParser(test_args)
        self._config = parser.parse()

    # ----------------------------------------------------------------------
    def test_config_general(self):
        self.assertEqual(self._config.timeout, 3.5)
        self.assertEqual(self._config.refresh_interval, 5.0)
        self.assertEqual(self._config.initial_query_size, 42)
        self.assertEqual(self._config.initial_time_range, '5m')
        self.assertEqual(self._config.default_index, 'filebeat*')
        self.assertEqual(self._config.header_color, get_column_color_key('blue'))
        self.assertFalse(self._config.no_header)
        self.assertFalse(self._config.verbose)
        self.assertTrue(self._config.verify_ssl_certificates)

    # ----------------------------------------------------------------------
    def test_config_server(self):
        self.assertEqual(len(self._config.servers), 2)
        index = 0
        for server in self._config.servers:
            index += 1
            self.assertEqual(server.name, f'test_server{index}')
            self.assertEqual(server.url, f'http://127.0.0.{index}:9200')
            self.assertEqual(server.username, f'logstash{index}')
            self.assertEqual(server.password, f'secret{index}')
            found_header_key1 = False
            found_header_key2 = False
            for key, value in server.headers:
                value = value.strip()
                if key == 'key1':
                    self.assertEqual(value, str(index))
                    found_header_key1 = True
                elif key == 'key2':
                    self.assertEqual(value, f'dhjshkjhd{index}')
                    found_header_key2 = True
                else:
                    self.fail(msg=f'Unknown header "{key}" found for server "{server.name}"')

            self.assertTrue(
                found_header_key1,
                msg=f'Header key1 not found in headers {server.headers}')
            self.assertTrue(
                found_header_key2,
                msg=f'Header key2 not found in headers {server.headers}')

        # test for missing server which has enabled=False in config
        for server in self._config.servers:
            self.assertNotEqual(server.name, 'test_server3_disabled')

    # ----------------------------------------------------------------------
    def test_config_kibana(self):
        self.assertEqual(self._config.kibana.index_name, '.kibana')
        self.assertEqual(self._config.kibana.saved_search, 'Apache2 access logs')
        default_columns = ['timestamp', 'hostname', 'program', 'message']
        self.assertEqual(self._config.kibana.default_columns, default_columns)
        self.assertEqual(self._config.kibana.custom_search, '_exists_: message')

    # ----------------------------------------------------------------------
    def test_config_parser(self):
        log_level_names_warning = ['warn', 'warning']
        log_level_names_error = ['fatal', 'emerg', 'alert', 'critical', 'error', 'err']

        self.assertEqual(self._config.parser.log_level_names_warning, log_level_names_warning)
        self.assertEqual(self._config.parser.log_level_names_error, log_level_names_error)

    # ----------------------------------------------------------------------
    def test_config_format(self):
        self.assertEqual(self._config.format.timestamp, '%Y-%m-%dT%H:%M:%S.%f')

    # ----------------------------------------------------------------------
    def test_config_display(self):
        column_timestamp = Column(
            names=['timestamp', '@timestamp', 'request_time'],
            display=True,
            color=get_column_color_key('green'),
            padding='23')

        column_log_level = Column(
            names=['syslog_severity', 'level', 'log_level', 'fail2ban_level', 'dj_level'],
            display=False,
            color=get_column_color_key(None),
            padding='>10')

        column_geoip_as_org = Column(
            names=['geoip.as_org'],
            display=True,
            color=get_column_color_key(None),
            padding='25')

        expected_columns = OrderedDict()
        expected_columns['timestamp'] = column_timestamp
        expected_columns['log_level'] = column_log_level
        expected_columns['geoip.as_org'] = column_geoip_as_org

        # check the column dict keys, compare available columns
        self.assertEqual(self._config.display.columns.keys(), expected_columns.keys())
        # compare each column in detail
        for column_name in self._config.display.columns:
            test_column = self._config.display.columns.get(column_name)
            expected_column = expected_columns.get(column_name, None)
            self.assertEqual(test_column, expected_column)

    # ----------------------------------------------------------------------
    def test_config_general_missing(self):
        test_args = mock.Mock()

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_missing_section):
            parser = self._setup_test_parser(test_args)
            with self.assertRaises(NoSectionError):
                parser._parse_general_settings('general')

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_missing_value):
            parser = self._setup_test_parser(test_args)
            with self.assertRaises(NoOptionError):
                parser._parse_general_settings('general')

    # ----------------------------------------------------------------------
    def _setup_test_parser(self, test_args=None):
        if test_args is None:
            test_args = mock.Mock()

        parser = LstailConfigParser(test_args)
        parser._init_config()
        parser._read_config()
        return parser

    # ----------------------------------------------------------------------
    def test_config_verbose(self):   # pylint: disable=too-many-statements
        test_args = mock.Mock(debug=False, verbose=False)
        section = 'general'

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_unset):
            parser = self._setup_test_parser(test_args)
            with self.assertRaises(ValueError):  # not a boolean
                parser._parse_general_settings(section)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_invalid_format):
            parser = self._setup_test_parser(test_args)
            with self.assertRaises(ValueError):  # not a boolean
                parser._parse_general_settings(section)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_false):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertFalse(parser._config.verbose)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertTrue(parser._config.verbose)

        # emulate --verbose command line flag
        test_args = mock.Mock(debug=False, verbose=True)
        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_false):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertTrue(parser._config.verbose)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertTrue(parser._config.verbose)

        # emulate --verbose and --debug command line flags
        test_args = mock.Mock(debug=True, verbose=True)
        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_false):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertTrue(parser._config.verbose)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertTrue(parser._config.verbose)

        # emulate --debug command line flag
        test_args = mock.Mock(debug=True, verbose=False)
        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_false):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertTrue(parser._config.verbose)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertTrue(parser._config.verbose)

    # ----------------------------------------------------------------------
    def test_config_no_header(self):
        test_args = mock.Mock(no_header=False)
        section = 'general'

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_unset):
            parser = self._setup_test_parser(test_args)
            with self.assertRaises(ValueError):  # not a boolean
                parser._parse_general_settings(section)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_invalid_format):
            parser = self._setup_test_parser(test_args)
            with self.assertRaises(ValueError):  # not a boolean
                parser._parse_general_settings(section)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_false):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            self.assertFalse(parser._config.no_header)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            self.assertTrue(parser._config.no_header)

        # emulate --no-header command line flag
        test_args = mock.Mock(no_header=True)
        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_false):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertTrue(parser._config.no_header)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertTrue(parser._config.no_header)

    # ----------------------------------------------------------------------
    def test_config_csv_output(self):
        test_args = mock.Mock(csv_output=False)
        section = 'general'

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_false):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            self.assertFalse(parser._config.csv_output)

        # emulate --csv command line flag
        test_args = mock.Mock(csv_output=True)
        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_false):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertTrue(parser._config.csv_output)

    # ----------------------------------------------------------------------
    def test_config_verify_ssl_certificates(self):
        test_args = mock.Mock(no_header=False)
        section = 'general'

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_false):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            self.assertFalse(parser._config.verify_ssl_certificates)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            self.assertTrue(parser._config.verify_ssl_certificates)

    # ----------------------------------------------------------------------
    def test_config_timeout(self):
        test_args = mock.Mock()
        section = 'general'

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_invalid_format):
            parser = self._setup_test_parser(test_args)
            with self.assertRaises(ValueError):
                parser._parse_general_settings(section)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            self.assertEqual(parser._config.timeout, 5.1)

    # ----------------------------------------------------------------------
    def test_config_refresh_interval(self):
        test_args = mock.Mock()
        section = 'general'

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_invalid_format):
            parser = self._setup_test_parser(test_args)
            with self.assertRaises(ValueError):  # not a boolean
                parser._parse_general_settings(section)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            self.assertEqual(parser._config.refresh_interval, 1.4)

    # ----------------------------------------------------------------------
    def test_config_initial_query_size(self):
        test_args = mock.Mock(initial_query_size=None)
        section = 'general'

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_invalid_format):
            parser = self._setup_test_parser(test_args)
            with self.assertRaises(ValueError):  # not a boolean
                parser._parse_general_settings(section)

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            self.assertEqual(parser._config.initial_query_size, 99)

        # emulate --lines command line flag
        test_args = mock.Mock(initial_query_size=56)
        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertEqual(parser._config.initial_query_size, 56)

    # ----------------------------------------------------------------------
    def test_config_initial_time_range(self):
        test_args = mock.Mock(initial_time_range=None)
        section = 'general'

        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertEqual(parser._config.initial_time_range, '48h')

        # emulate --range command line flag
        test_args = mock.Mock(initial_time_range='2d')
        with mock.patch.object(LstailConfigParser, '_read_config', new=read_config_set):
            parser = self._setup_test_parser(test_args)
            parser._parse_general_settings(section)
            parser._override_config_options_from_command_line()
            self.assertEqual(parser._config.initial_time_range, '2d')
