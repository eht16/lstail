# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from configparser import ConfigParser
import os

from lstail.constants import LSTAIL_DEFAULT_FIELD_DOCUMENT_ID
from lstail.dto.column import Column
from lstail.dto.configuration import Configuration
from lstail.dto.server import Server
from lstail.util.color import get_column_color_key


########################################################################
class LstailConfigParser:

    # ----------------------------------------------------------------------
    def __init__(self, options):
        self._options = options
        self._config = None
        self._config_parser = None
        self._config_file_paths = None

    # ----------------------------------------------------------------------
    def parse(self):
        self._fetch_config_file_paths()
        self._init_config()
        self._read_config()
        self._parse_config()
        self._override_config_options_from_command_line()
        self._add_debug_columns()
        return self._config

    # ----------------------------------------------------------------------
    def _fetch_config_file_paths(self):
        self._config_file_paths = (
            '/etc/lstail.conf',
            os.path.expanduser('~/.config/lstail.conf'),
            'lstail.conf')

    # ----------------------------------------------------------------------
    def _init_config(self):
        self._config = Configuration()

    # ----------------------------------------------------------------------
    def _read_config(self):
        self._config_parser = ConfigParser()
        # read config file from location as specified via command line but fail it if doesn't exist
        if self._options.config_file_path:
            with open(self._options.config_file_path, encoding='utf-8') as config_file_h:
                self._config_parser.read_file(config_file_h)
                return
        # otherwise try pre-defined config file locations
        elif self._config_parser.read(self._config_file_paths):
            return
        # if we still didn't read any configuration file, bail out
        raise RuntimeError('No config file found')

    # ----------------------------------------------------------------------
    def _parse_config(self):
        for section_name in self._config_parser.sections():
            if section_name == 'general':
                self._parse_general_settings(section_name)
            elif section_name == 'kibana':
                self._parse_kibana_settings(section_name)
            elif section_name == 'parser':
                self._parse_parser_settings(section_name)
            elif section_name == 'format':
                self._parse_format_settings(section_name)
            elif section_name.startswith('display_column_'):
                self._parse_column_settings(section_name)
            elif section_name.startswith('server_'):
                self._parse_server_settings(section_name)

    # ----------------------------------------------------------------------
    def _parse_general_settings(self, section_name):
        parser = self._config_parser
        self._config.timeout = parser.getfloat(section_name, 'timeout')
        self._config.refresh_interval = parser.getfloat(section_name, 'refresh_interval')
        self._config.initial_query_size = parser.getint(section_name, 'initial_query_size')
        self._config.initial_time_range = parser.get(section_name, 'initial_time_range')
        self._config.verify_ssl_certificates = parser.getboolean(
            section_name, 'verify_ssl_certificates')
        self._config.default_index = self._config_option_get_default(section_name, 'default_index')
        self._config.verbose = parser.getboolean(section_name, 'verbose')
        self._config.no_header = parser.getboolean(section_name, 'no_header')
        header_color = self._config_option_get_default(section_name, 'header_color', 'light_yellow')
        if header_color:
            self._config.header_color = self._parse_column_color(header_color, section_name)

    # ----------------------------------------------------------------------
    def _parse_kibana_settings(self, section_name):
        self._config.kibana.index_name = self._config_option_get_default(
            section_name,
            'kibana_index_name',
            '.kibana')
        self._config.kibana.saved_search = self._config_option_get_default(
            section_name,
            'default_saved_search')
        default_columns = self._config_option_get_default(
            section_name,
            'default_columns',
            'timestamp, hostname, program, message')
        self._config.kibana.default_columns = default_columns.split(', ')

    # ----------------------------------------------------------------------
    def _parse_parser_settings(self, section_name):
        log_level_names_warning = self._config_option_get_default(
            section_name,
            'log_level_names_warning',
            'warn, warning')
        self._config.parser.log_level_names_warning = log_level_names_warning.split(', ')
        log_level_names_error = self._config_option_get_default(
            section_name,
            'log_level_names_error',
            'fatal, emerg, alert, crit, critical, error, err')
        self._config.parser.log_level_names_error = log_level_names_error.split(', ')

    # ----------------------------------------------------------------------
    def _parse_format_settings(self, section_name):
        self._config.format.timestamp = self._config_option_get_default(
            section_name,
            'timestamp',
            '%Y-%m-%dT%H:%M:%S.%f',
            raw=True)

    # ----------------------------------------------------------------------
    def _parse_column_settings(self, section_name):
        column_name = section_name[15:]
        names_raw = self._config_parser.get(section_name, 'names')
        display_raw = self._config_option_get_default(section_name, 'display', True)
        padding_raw = self._config_option_get_default(section_name, 'padding')
        column_color_name = self._config_option_get_default(section_name, 'color')
        column_color = self._parse_column_color(column_color_name, section_name)

        column = Column()
        column.names = names_raw.split(', ')
        column.color = column_color
        column.padding = padding_raw
        column.display = bool(display_raw in (True, '1', 'true', 'True', 'TRUE'))
        self._config.display.columns[column_name] = column

    # ----------------------------------------------------------------------
    def _parse_column_color(self, column_color_name, section_name):
        try:
            return get_column_color_key(column_color_name)
        except KeyError as exc:
            msg = f'Invalid terminal color specification: "{column_color_name}" ' \
                  f'in section "{section_name}"'
            raise RuntimeError(msg) from exc

    # ----------------------------------------------------------------------
    def _parse_server_settings(self, section_name):
        server = Server()
        server_enable = self._config_parser.getboolean(section_name, 'enable')
        if not server_enable:
            return  # skip complete server section if not enabled

        server.name = section_name[7:]
        server.url = self._config_parser.get(section_name, 'url')
        server.username = self._config_option_get_default(section_name, 'username')
        server.password = self._config_option_get_default(section_name, 'password')
        headers_raw = self._config_option_get_default(section_name, 'headers', default='')
        server.headers = [
            self._parse_server_http_header(header)
            for header
            in headers_raw.splitlines()]
        self._config.servers.append(server)

    # ----------------------------------------------------------------------
    def _parse_server_http_header(self, header_raw):
        return header_raw.strip().split(':', maxsplit=1)

    # ----------------------------------------------------------------------
    def _config_option_get_default(self, section, option, default=None, raw=False, getter=None):
        if self._config_parser.has_option(section, option):
            if getter is None:
                getter = self._config_parser.get
            return getter(section, option, raw=raw)
        else:
            return default

    # ----------------------------------------------------------------------
    def _override_config_options_from_command_line(self):
        self._config.follow = self._options.follow
        self._config.select_kibana_saved_search = self._options.select_kibana_saved_search
        self._config.debug = self._options.debug
        self._config.verbose = self._config.verbose or self._options.verbose or self._config.debug
        self._config.no_header = self._config.no_header or self._options.no_header
        self._config.csv_output = self._options.csv_output
        if self._options.initial_time_range:
            self._config.initial_time_range = self._options.initial_time_range
        if self._options.initial_query_size:
            self._config.initial_query_size = self._options.initial_query_size
        if self._options.kibana_saved_search:
            self._config.kibana.saved_search = self._options.kibana_saved_search
        if self._options.custom_search:
            self._config.kibana.custom_search = self._options.custom_search

    # ----------------------------------------------------------------------
    def _add_debug_columns(self):
        if self._config.debug:
            # add column for document_id in debug mode
            document_id_column_name = LSTAIL_DEFAULT_FIELD_DOCUMENT_ID
            document_id_column = Column(
                names=[document_id_column_name, 'documentid', 'docid', 'id_', '_id'],
                color=self._parse_column_color('cyan', '<code>'),
                display=True,
                padding=24)
            self._config.display.columns[document_id_column_name] = document_id_column
