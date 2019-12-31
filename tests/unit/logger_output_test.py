# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from io import StringIO
import logging
import sys

from ddt import data, ddt
from freezegun import freeze_time

from lstail.constants import PROGRAM_NAME
from lstail.dto.column import Column
from lstail.dto.configuration import Configuration
from lstail.logger import LstailLogger
from tests.base import BaseTestCase


CONFIG = Configuration()
CONFIG.debug = False
CONFIG.no_header = True
CONFIG.parser.log_level_names_warning = ['warn', 'warning']
CONFIG.parser.log_level_names_error = ['emerg', 'alert', 'crit', 'critical', 'error', 'err']
CONFIG.format.timestamp = '%Y-%m-%dT%H:%M:%S.%f'
CONFIG.kibana.default_columns = ['timestamp', 'level', 'hostname', 'program', 'message']
CONFIG.display.columns = OrderedDict({
    'timestamp': Column(names=['timestamp', '@timestamp'], color=None, display=True, padding=24),
    'log_level': Column(names=['level', 'log_level'], color='yellow', display=True, padding=8),
    'hostname': Column(names=['hostname', 'logsource'], color='magenta', display=True, padding=10),
    'program': Column(names=['program', 'programname'], color='green', display=True, padding=22),
    'message': Column(names=['message'], color=None, display=True),
})

CONFIG_COLUMN_NESTED_NAME = 'nested.column.test'
CONFIG_COLUMN_NESTED = Column(names=[], color=None, display=True, padding=24)
CONFIG_DEFAULT_COLUMNS_NESTED = ['level', CONFIG_COLUMN_NESTED_NAME, 'message']

LOG_DATETIME = datetime.now()
LOG_TIMESTAMP = LOG_DATETIME.strftime(CONFIG.format.timestamp)
LOG_TIMESTAMP = LOG_TIMESTAMP[:-3]  # LstailLogger cuts the last three digits, so do as well


@ddt
class LoggerOutputTest(BaseTestCase):

    # ----------------------------------------------------------------------
    def test_print_header(self):
        config = deepcopy(CONFIG)
        config.no_header = False

        expected_header = 'timestamp{}level    hostname   program{}message'.format(
            ' ' * 16, ' ' * 16)
        # test
        logger = LstailLogger(config, output=sys.stdout, verbose=False)
        logger.print_header()
        # check
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, expected_header)

    # ----------------------------------------------------------------------
    def test_print_header_with_header_disabled(self):
        config = deepcopy(CONFIG)
        config.no_header = True

        expected_header = ''
        # test
        logger = LstailLogger(config, output=sys.stdout, verbose=False)
        logger.print_header()
        # check
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, expected_header)

    # ----------------------------------------------------------------------
    def test_print_header_nested_column(self):
        config = deepcopy(CONFIG)
        config.no_header = False
        config.kibana.default_columns = CONFIG_DEFAULT_COLUMNS_NESTED
        config.display.columns[CONFIG_COLUMN_NESTED_NAME] = CONFIG_COLUMN_NESTED

        expected_header = 'timestamp                level    {}       message'.format(
            CONFIG_COLUMN_NESTED_NAME)
        # test
        logger = LstailLogger(config, output=sys.stdout, verbose=False)
        logger.print_header()
        # check
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, expected_header)

    # ----------------------------------------------------------------------
    @data(True, False)
    def test_log_log(self, verbose):
        test_string = 'log message'
        expected_output = self._factor_log_output(test_string, verbose, level='DEBUG')
        # test
        with freeze_time(LOG_DATETIME):
            logger = LstailLogger(CONFIG, output=sys.stdout, verbose=verbose)
            logger.log(logging.DEBUG, test_string)

        # check
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, expected_output)

    # ----------------------------------------------------------------------
    @data(True, False)
    def test_log_debug(self, verbose):
        test_string = 'debug message'
        expected_output = self._factor_log_output(test_string, verbose, level='DEBUG')
        self._test_log('debug', test_string, expected_output, verbose)

    # ----------------------------------------------------------------------
    def _test_log(self, callable_name, test_string, expected_output, verbose):
        # test
        with freeze_time(LOG_DATETIME):
            logger = LstailLogger(CONFIG, output=sys.stdout, verbose=verbose)
            callable_ = getattr(logger, callable_name)
            callable_(test_string)

        # check
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, expected_output)

    # ----------------------------------------------------------------------
    def _factor_log_output(self, test_string, verbose, level):
        # verbose is only relevant for info and debug log levels, always True otherwise
        if verbose or level.lower() != 'debug':
            return '{}  {:8}            {:22} {}'.format(
                LOG_TIMESTAMP,
                level,
                PROGRAM_NAME,
                test_string)

        return ''

    # ----------------------------------------------------------------------
    @data(True, False)
    def test_log_info(self, verbose):
        test_string = 'info message'
        expected_output = self._factor_log_output(test_string, verbose=verbose, level='INFO')
        self._test_log('info', test_string, expected_output, verbose)

    # ----------------------------------------------------------------------
    def test_log_info_nested_column(self):
        config = deepcopy(CONFIG)
        config.no_header = False
        config.kibana.default_columns = CONFIG_DEFAULT_COLUMNS_NESTED
        config.display.columns[CONFIG_COLUMN_NESTED_NAME] = CONFIG_COLUMN_NESTED

        test_string = 'info nested test message'
        test_nested = dict(nested=dict(column=dict(test='nested')))
        expected_output = '{}  INFO     nested                   {}'.format(
            LOG_TIMESTAMP, test_string)

        with freeze_time(LOG_DATETIME):
            logger = LstailLogger(config, output=sys.stdout, verbose=False)
            logger.info(test_string, extra=test_nested)

        # check
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, expected_output)

    # ----------------------------------------------------------------------
    @data(True, False)
    def test_log_warning(self, verbose):
        test_string = 'warning message'
        expected_output = self._factor_log_output(test_string, verbose=verbose, level='WARNING')
        self._test_log('warning', test_string, expected_output, verbose)

    # ----------------------------------------------------------------------
    @data(True, False)
    def test_log_error(self, verbose):
        test_string = 'error message'
        expected_output = self._factor_log_output(test_string, verbose=verbose, level='ERROR')
        self._test_log('error', test_string, expected_output, verbose)

    # ----------------------------------------------------------------------
    @data(True, False)
    def test_log_exception(self, verbose):
        test_string = 'exception message'
        expected_output = self._factor_log_output(test_string, verbose=verbose, level='ERROR')
        self._test_log('exception', test_string, expected_output, verbose)

    # ----------------------------------------------------------------------
    @data(True, False)
    def test_log_exception_with_exc_info(self, verbose):
        test_string = 'exception message'
        expected_output = self._factor_log_output(test_string, verbose=verbose, level='ERROR')
        # provoke exception to test with
        try:
            1 / 0
        except ZeroDivisionError as exc:
            with freeze_time(LOG_DATETIME):
                logger = LstailLogger(CONFIG, output=sys.stdout, verbose=verbose)
                logger.exception(test_string, exc_info=exc)

        # check
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertTrue(output.startswith(expected_output))
        self.assertIn('Traceback (most recent call last):', output)
        self.assertIn('1 / 0', output)
        self.assertTrue(output.endswith('ZeroDivisionError: division by zero'))

    # ----------------------------------------------------------------------
    @data(True, False)
    def test_log_critical(self, verbose):
        test_string = 'critical message'
        expected_output = self._factor_log_output(test_string, verbose=verbose, level='CRITICAL')
        self._test_log('critical', test_string, expected_output, verbose)

    # ----------------------------------------------------------------------
    def test_log_custom_output(self):
        test_string = 'custom output message'
        custom_output = StringIO()
        expected_output = self._factor_log_output(test_string, verbose=True, level='INFO')

        with freeze_time(LOG_DATETIME):
            logger = LstailLogger(CONFIG, output=custom_output, verbose=True)
            logger.info(test_string)

        # check for output in custom output
        output = custom_output.getvalue().strip()
        self.assertEqual(output, expected_output)

        # check there is no output on default sys.stdout
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, '')

    # ----------------------------------------------------------------------
    def test_log_internal_csv_output(self):
        config = deepcopy(CONFIG)
        config.csv_output = True
        verbose = True

        test_string = 'csv "output" message, and more'
        custom_output = StringIO()
        with freeze_time(LOG_DATETIME):
            logger = LstailLogger(config, output=custom_output, verbose=verbose)
            logger.debug(test_string)

        # here we expect actually normal log format but not CSV because we used logger.debug()
        # which used for internal log messages and so do not use CSV format
        expected_output = self._factor_log_output(test_string, verbose=verbose, level='DEBUG')
        # check for output in custom output
        output = custom_output.getvalue().strip()
        self.assertEqual(output, expected_output)

        # check there is no output on default sys.stdout
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, '')
