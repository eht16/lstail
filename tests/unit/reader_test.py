# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from copy import deepcopy
from datetime import datetime, timedelta
import sys

from freezegun import freeze_time

from lstail.constants import ELASTICSEARCH_MAJOR_VERSION_2, ELASTICSEARCH_MAJOR_VERSION_6
from lstail.dto.configuration import Configuration
from lstail.query.kibana_saved_search import ListKibanaSavedSearchesController
from lstail.reader import LogstashReader
from tests.base import BaseTestCase, mock


# pylint: disable=protected-access

TEST_CONFIG = Configuration()
TEST_CONFIG.debug = False
TEST_CONFIG.verbose = False
TEST_CONFIG.kibana = mock.Mock(index_name='mocked-index', default_columns=['dummy'])


class LogstashReaderTest(BaseTestCase):

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.kibana_saved_search.detect_elasticsearch_version')
    @mock.patch.object(ListKibanaSavedSearchesController, '_request_kibana_saved_searches')
    def test_list_kibana_saved_searches_positive_v6(self, mock_handler, mock_es_detection):
        # load test data
        test_response_kibana6 = self._get_test_data('saved_searches_kibana6')
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_6
        mock_handler.return_value = test_response_kibana6

        reader = LogstashReader(TEST_CONFIG)
        reader.list_kibana_saved_searches()

        # check
        expected_output = u'Dummy saved search 1 (host, program, log_level, _id, ' + \
            u'log_level_no_orig, message)\nParse Errors (tags, logsource, program, message)\n' + \
            u'Syslog (host, program, message)'
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, expected_output)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.kibana_saved_search.detect_elasticsearch_version')
    @mock.patch.object(ListKibanaSavedSearchesController, '_request_kibana_saved_searches')
    def test_list_kibana_saved_searches_positive_v4(self, mock_handler, mock_es_detection):
        # load test data
        test_response_kibana4 = self._get_test_data('saved_searches_kibana4')
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_2
        mock_handler.return_value = test_response_kibana4

        reader = LogstashReader(TEST_CONFIG)
        reader.list_kibana_saved_searches()

        # check
        expected_output = u'Kibana Saved Search 2 (fromhost, programname)\nKibana saved ' + \
            u'search 1 (fromhost, requestHost, vHostPort, requestUrl)\nSüslogging ' + \
            u'(fromhost, programname, severity, message)'
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, expected_output)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.kibana_saved_search.detect_elasticsearch_version')
    @mock.patch.object(ListKibanaSavedSearchesController, '_request_kibana_saved_searches')
    def test_list_kibana_saved_searches_negative_no_hits(self, mock_handler, mock_es_detection):
        # load test data
        test_response = self._get_test_data('saved_searches_empty')
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_6
        mock_handler.return_value = test_response

        reader = LogstashReader(TEST_CONFIG)
        reader.list_kibana_saved_searches()

        # check
        expected_output = 'No saved searches found in Kibana'
        output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
        self.assertEqual(output, expected_output)

    # ----------------------------------------------------------------------
    def test_setup_initial_time_range(self):
        config = deepcopy(TEST_CONFIG)
        end_date_time = datetime(2018, 2, 22, 22, 22, 42)
        with freeze_time(end_date_time):
            # test with config.initial_time_range being set (42d)
            config.initial_time_range = '42d'
            reader = LogstashReader(config)
            reader._setup_initial_time_range()
            # check
            expected_end_date_time = end_date_time - timedelta(days=42)
            self.assertEqual(reader._last_timestamp, expected_end_date_time)

            # test with config.initial_time_range being set (7m)
            config.initial_time_range = '7m'
            reader = LogstashReader(config)
            reader._setup_initial_time_range()
            # check
            expected_end_date_time = end_date_time - timedelta(seconds=7 * 60)
            self.assertEqual(reader._last_timestamp, expected_end_date_time)

            # test without config.initial_time_range being set
            config.initial_time_range = None
            reader = LogstashReader(config)
            reader._setup_initial_time_range()
            # check
            # days=1 is the default if the config setting is missing
            expected_end_date_time = end_date_time - timedelta(days=1)
            self.assertEqual(reader._last_timestamp, expected_end_date_time)
