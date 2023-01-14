# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from io import StringIO
from socket import getfqdn
from uuid import uuid4
import sys

from freezegun import freeze_time

from lstail.constants import (
    LSTAIL_DEFAULT_FIELD_DOCUMENT_ID,
    LSTAIL_DEFAULT_FIELD_TIMESTAMP,
    LSTAIL_INTERNAL_DOCUMENT_ID,
    TERM_COLOR_DEFAULT,
)
from lstail.dto.column import Column
from lstail.error import DocumentIdAlreadyProcessedError
from lstail.logger import LstailLogger
from lstail.util.color import factor_color_code
from lstail.util.safe_munch import safe_munchify
from tests.base import BaseTestCase, mock


# pylint: disable=protected-access,too-many-public-methods

COLUMN_TIMESTAMP_NAMES = ['timestamp', '@timestamp', 'request_time']
LOG_DOCUMENT_COLUMN_NAMES = ['host', 'message']
LOG_DOCUMENT_COLUMN_HOST_PADDING = 12
LOG_DOCUMENT_COLUMNS = OrderedDict({
    LSTAIL_DEFAULT_FIELD_TIMESTAMP: Column(
        names=COLUMN_TIMESTAMP_NAMES,
        color=None,
        display=True,
        padding=26),
    'level': Column(names=[], display=False),
    'host': Column(
        names=['fqdn'],
        color='_c_yellow',
        display=True,
        padding=LOG_DOCUMENT_COLUMN_HOST_PADDING),
    'message': Column(names=[], color='_c_magenta', display=True, padding='15'),
    'nested.test.column': Column(names=['nested.alias']),
})
LOG_DOCUMENT_CONFIG = mock.Mock(
    debug=False,
    verbose=False,
    csv_output=False,
    kibana=mock.Mock(default_columns=LOG_DOCUMENT_COLUMN_NAMES),
    format=mock.Mock(timestamp='%Y-%m-%dT%H:%M:%S.%f'),
    display=mock.Mock(columns=LOG_DOCUMENT_COLUMNS))
LOG_DOCUMENT_TIMESTAMP = '2018-02-22T07:10:38.123'
LOG_DOCUMENT_TEST_DOCUMENT = {
    '_id': 'ruEw7GIBPn74Z3EHvdt-',
    '_index': 'logstash-2018.02.22',
    '_score': None,
    '_source': {
        LSTAIL_DEFAULT_FIELD_TIMESTAMP: LOG_DOCUMENT_TIMESTAMP,
        '@version': '1',
        'level': 'info',
        'host': 'localhost',
        'message': 'message content',
        'type': 'test-document'
    }
}


class LoggerTest(BaseTestCase):

    # ----------------------------------------------------------------------
    def test_get_column_color_no_use_colors(self):
        config = mock.Mock()
        logger = LstailLogger(config, output=sys.stdout, verbose=False)
        logger._setup_terminal_colors(force=False)
        column = Column(color='_c_green')

        color_code = logger._get_column_color(column, force_color=None)
        self.assertEqual(color_code, '_c_reset')
        # force color
        color_code = logger._get_column_color(column, force_color='_c_yellow')
        self.assertEqual(color_code, '_c_reset')

    # ----------------------------------------------------------------------
    def test_get_column_color_no_use_colors_no_column_color(self):
        config = mock.Mock()
        logger = LstailLogger(config, output=sys.stdout, verbose=False)
        logger._setup_terminal_colors(force=False)
        column = Column(color=None)

        color_code = logger._get_column_color(column, force_color=None)
        self.assertEqual(color_code, '_c_reset')
        # force color
        color_code = logger._get_column_color(column, force_color='_c_yellow')
        self.assertEqual(color_code, '_c_reset')

    # ----------------------------------------------------------------------
    def test_get_column_color_use_colors(self):
        config = mock.Mock()
        logger = LstailLogger(config, output=sys.stdout, verbose=False)
        logger._setup_terminal_colors(force=True)
        column = Column(color='_c_green')

        color_code = logger._get_column_color(column, force_color=None)
        self.assertEqual(color_code, '_c_green')
        # force color
        color_code = logger._get_column_color(column, force_color='_c_yellow')
        self.assertEqual(color_code, '_c_yellow')

    # ----------------------------------------------------------------------
    def test_get_column_color_use_colors_no_column_color(self):
        config = mock.Mock()
        logger = LstailLogger(config, output=sys.stdout, verbose=False)
        logger._setup_terminal_colors(force=True)
        column = Column(color=None)

        color_code = logger._get_column_color(column, force_color=None)
        self.assertEqual(color_code, '_c_reset')
        # force color
        color_code = logger._get_column_color(column, force_color='_c_yellow')
        self.assertEqual(color_code, '_c_yellow')

    # ----------------------------------------------------------------------
    def test_update_display_columns(self):
        default_column_names = ['column1', 'column2']
        config = mock.Mock(kibana=mock.Mock(default_columns=default_column_names))
        logger = LstailLogger(config, output=sys.stdout, verbose=False)

        # columns = None
        logger.update_display_columns(columns=None)
        expected_columns = ['document_id', 'timestamp'] + default_column_names
        self.assertEqual(logger._display_columns, expected_columns)

        # columns = custom
        test_columns = ['test_col1', 'test_col2', 'test_col3']
        logger.update_display_columns(columns=test_columns)
        expected_columns = ['document_id', 'timestamp'] + test_columns
        self.assertEqual(logger._display_columns, expected_columns)

    # ----------------------------------------------------------------------
    def test_log_document_positive(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)
        logger.update_display_columns()

        # positive test
        logger.log_document(LOG_DOCUMENT_TEST_DOCUMENT)
        # check
        expected_output = f'{LOG_DOCUMENT_TIMESTAMP}    localhost    message content'
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, expected_output)

    # ----------------------------------------------------------------------
    def test_log_document_negative_parse_exception(self):

        def fake_print_document(self, document, *args, **kwargs):
            if document['_source'][LSTAIL_DEFAULT_FIELD_TIMESTAMP] == LOG_DOCUMENT_TIMESTAMP:
                # this is our test document, raise exception
                raise ValueError(fake_exc_msg)
            # otherwise call the original method
            return real_print_document(self, document, *args, **kwargs)

        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        real_print_document = LstailLogger._print_document
        test_datetime = datetime.now()
        fake_exc_msg = 'fake exception ABCDEFG'

        # negative test - fake an internal exception
        with freeze_time(test_datetime):
            with mock.patch.object(LstailLogger, '_print_document', new=fake_print_document):
                logger.log_document(LOG_DOCUMENT_TEST_DOCUMENT)

                expected_dt = test_datetime.strftime(LOG_DOCUMENT_CONFIG.format.timestamp)[:-3]
                fqdn = getfqdn()
                padding = LOG_DOCUMENT_COLUMN_HOST_PADDING
                expected_output = f'{expected_dt}    {fqdn:{padding}} Unparseable document: ' \
                                  f'ValueError: {fake_exc_msg}:'
                output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
                self.assertTrue(output.startswith(expected_output))

    # ----------------------------------------------------------------------
    def test_log_document_negative_parse_exception_no_recover(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        # negative test - fake an internal exception
        with freeze_time(datetime.now()):
            with mock.patch.object(LstailLogger, '_print_document') as mock_print:
                mock_print.side_effect = ValueError('fake exception ABCDEFG')
                logger.log_document(LOG_DOCUMENT_TEST_DOCUMENT)

                expected_output = 'Unparseable document: ValueError: fake exception ABCDEFG:'
                output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
                self.assertTrue(output.startswith(expected_output))

    # ----------------------------------------------------------------------
    def test_assert_document_already_processed_positive(self):
        config = mock.Mock()
        config.display.columns = {LSTAIL_DEFAULT_FIELD_DOCUMENT_ID: None}
        logger = LstailLogger(config, output=sys.stdout, verbose=False)
        logger._setup_processed_ids_queue()

        # positive test - uuid
        _id = str(uuid4())
        document_values = {LSTAIL_DEFAULT_FIELD_DOCUMENT_ID: _id}
        logger._assert_document_already_processed(document_values)
        # check
        self.assertIn(_id, logger._processed_ids)

        # positive test - internal dummy id
        _id = LSTAIL_INTERNAL_DOCUMENT_ID
        document_values = {LSTAIL_DEFAULT_FIELD_DOCUMENT_ID: _id}
        logger._assert_document_already_processed(document_values)
        # check - nothing to do, no exception is good

    # ----------------------------------------------------------------------
    def test_assert_document_already_processed_negative(self):
        config = mock.Mock()
        config.display.columns = {LSTAIL_DEFAULT_FIELD_DOCUMENT_ID: None}

        logger = LstailLogger(config, output=sys.stdout, verbose=False)
        logger._setup_processed_ids_queue()

        _id = str(uuid4())
        document_values = {LSTAIL_DEFAULT_FIELD_DOCUMENT_ID: _id}
        # this is OK, the passed ID is first seen
        logger._assert_document_already_processed(document_values)
        # this one should raise an exception
        with self.assertRaises(DocumentIdAlreadyProcessedError):
            logger._assert_document_already_processed(document_values)

    # ----------------------------------------------------------------------
    def test_get_display_columns_for_document(self):
        internal_display_columns = [1, 2, 3]
        display_columns = [4, 5, 6]

        config = mock.Mock()
        logger = LstailLogger(config, output=sys.stdout, verbose=False)
        logger._internal_display_columns = list(internal_display_columns)
        logger._display_columns = list(display_columns)

        # default - receive document display columns
        test_document = None
        columns = logger._get_display_columns_for_document(test_document)
        self.assertEqual(columns, display_columns)

        # default - receive document display columns
        test_document = dict(something='else')
        columns = logger._get_display_columns_for_document(test_document)
        self.assertEqual(columns, display_columns)

        # test internal flag set
        test_document = dict(internal=True)
        columns = logger._get_display_columns_for_document(test_document)
        self.assertEqual(columns, internal_display_columns)

        # test display_columns unset
        test_document = dict(internal=True)
        logger._display_columns = None
        columns = logger._get_display_columns_for_document(test_document)
        self.assertEqual(columns, internal_display_columns)

    # ----------------------------------------------------------------------
    def test_get_column_by_name_positive_direct(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        # positive test - matching direct column name
        test_column_name = 'level'
        expected_column = LOG_DOCUMENT_COLUMNS[test_column_name]
        # check
        column = logger._get_column_by_name(test_column_name)
        self.assertEqual(column, expected_column)

    # ----------------------------------------------------------------------
    def test_get_column_by_name_positive_alias(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        # positive test - matching via Column.names
        # ("fqdn" is set as alias for "host" in LOG_DOCUMENT_COLUMNS)
        test_column_name = 'fqdn'
        expected_column = LOG_DOCUMENT_COLUMNS['host']
        # check
        column = logger._get_column_by_name(test_column_name)
        self.assertEqual(column, expected_column)

    # ----------------------------------------------------------------------
    def test_get_column_by_name_positive_default(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        # positive test - matching via Column.names
        # ("fqdn" is set as alias for "host" in LOG_DOCUMENT_COLUMNS)
        test_column_name = 'non-existent-column-name-ABCDEFG'
        expected_column = Column(
            names=[test_column_name],
            color=factor_color_code(TERM_COLOR_DEFAULT),
            display=True,
            padding=None)
        # test
        column = logger._get_column_by_name(test_column_name)
        self.assertEqual(column, expected_column)

    # ----------------------------------------------------------------------
    def test_update_column_name_from_document_positive_direct(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        # direct match via column name
        document_values = safe_munchify({'host': 'localhost'})
        test_column_name = 'host'
        test_column = LOG_DOCUMENT_COLUMNS['host']
        # test
        column_name = logger._update_column_name_from_document(
            test_column_name, test_column, document_values)
        # check
        self.assertEqual(column_name, test_column_name)

    # ----------------------------------------------------------------------
    def test_update_column_name_from_document_positive_alias(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        # alias match
        document_values = safe_munchify({'fqdn': 'localhost'})
        test_column_name = 'host'
        test_column = LOG_DOCUMENT_COLUMNS['host']
        # test
        column_name = logger._update_column_name_from_document(
            test_column_name, test_column, document_values)
        # check
        self.assertEqual(column_name, 'fqdn')

    # ----------------------------------------------------------------------
    def test_update_column_name_from_document_positive_nested_direct(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        # direct match via column name
        document_values = safe_munchify({'nested.test.column': 'localhost'})
        test_column_name = 'nested.test.column'
        test_column = LOG_DOCUMENT_COLUMNS['host']
        # test
        column_name = logger._update_column_name_from_document(
            test_column_name, test_column, document_values)
        # check
        self.assertEqual(column_name, test_column_name)

    # ----------------------------------------------------------------------
    def test_update_column_name_from_document_positive_nested_alias(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        # alias match
        document_values = safe_munchify({'nested.alias': 'localhost'})
        test_column_name = 'nested.test.column'
        test_column = LOG_DOCUMENT_COLUMNS['nested.test.column']
        # test
        column_name = logger._update_column_name_from_document(
            test_column_name, test_column, document_values)
        # check
        self.assertEqual(column_name, 'nested.alias')

    # ----------------------------------------------------------------------
    def test_update_column_name_from_document_negative(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        # alias match
        document_values = safe_munchify({'foo': 'blah'})
        test_column_name = 'host'
        test_column = LOG_DOCUMENT_COLUMNS['host']
        # test
        column_name = logger._update_column_name_from_document(
            test_column_name, test_column, document_values)
        # check - we get the passed column name
        # but the initially missing column name was added to document_values
        self.assertEqual(column_name, test_column_name)
        self.assertIn(test_column_name, document_values)

    # ----------------------------------------------------------------------
    def test_update_column_name_from_document_negative_nested(self):
        logger = LstailLogger(LOG_DOCUMENT_CONFIG, output=sys.stdout, verbose=False)

        # alias match
        document_values = safe_munchify({'nested.foo': 'blah'})
        test_column_name = 'nested.bar'
        test_column = LOG_DOCUMENT_COLUMNS['host']
        # test
        column_name = logger._update_column_name_from_document(
            test_column_name, test_column, document_values)
        # check - we get the passed column name
        # but the initially missing column name was added to document_values
        self.assertEqual(column_name, test_column_name)
        self.assertIn(test_column_name, document_values)

    # ----------------------------------------------------------------------
    def test_log_document_csv_output(self):
        config = deepcopy(LOG_DOCUMENT_CONFIG)
        config.csv_output = True
        config.kibana = mock.Mock(default_columns=['host', 'level', 'program', 'message'])

        test_program = 'python3 -m unittest'
        test_string = 'csv "output" message, and more'
        document = deepcopy(LOG_DOCUMENT_TEST_DOCUMENT)
        document['_source']['message'] = test_string
        document['_source']['program'] = test_program

        custom_output = StringIO()
        expected_output = f'{LOG_DOCUMENT_TIMESTAMP},localhost,info,{test_program},' \
                          '"csv ""output"" message, and more"'

        with freeze_time(LOG_DOCUMENT_TIMESTAMP):
            logger = LstailLogger(config, output=custom_output, verbose=False)
            logger.log_document(document)

        # check for output in custom output
        output = custom_output.getvalue().strip()
        self.assertEqual(output, expected_output)

        # check there is no output on default sys.stdout
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, '')

    # ----------------------------------------------------------------------
    def test_get_document_id_from_document(self):
        # setup
        column = Column(names=['test-id-col'], display=True)
        config = deepcopy(LOG_DOCUMENT_CONFIG)
        config.display.columns[LSTAIL_DEFAULT_FIELD_DOCUMENT_ID] = column
        logger = LstailLogger(config, output=sys.stdout)

        # pass empty document
        document = {}
        document_values = {}
        result = logger._get_document_id_from_document(document_values, document)
        # check
        expected = None
        self.assertEqual(result, expected)

        # pass document with id
        test_id = 'test-id-42-test-73-test'
        document = {'_id': test_id}
        document_values = {}
        result = logger._get_document_id_from_document(document_values, document)
        # check
        expected = test_id
        self.assertEqual(result, expected)

        # pass document_values with id
        test_id = 'test-id-42-test-73-test'
        document = None
        document_values = {LSTAIL_DEFAULT_FIELD_DOCUMENT_ID: test_id}
        result = logger._get_document_id_from_document(document_values, document)
        # check
        expected = test_id
        self.assertEqual(result, expected)

        # pass document_values without id
        test_id = None
        document = None
        document_values = {LSTAIL_DEFAULT_FIELD_DOCUMENT_ID: test_id}
        result = logger._get_document_id_from_document(document_values, document)
        # check
        expected = test_id
        self.assertEqual(result, expected)

        # pass document_values with custom id field
        test_id = 'test-id-42-test-73-test'
        document = None
        document_values = {'test-id-col': test_id}
        result = logger._get_document_id_from_document(document_values, document)
        # check
        expected = test_id
        self.assertEqual(result, expected)
