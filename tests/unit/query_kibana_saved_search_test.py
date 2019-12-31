# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from lstail.constants import (
    ELASTICSEARCH_MAJOR_VERSION_2,
    ELASTICSEARCH_MAJOR_VERSION_6,
    ELASTICSEARCH_MAJOR_VERSION_7,
)
from lstail.dto.configuration import Configuration
from lstail.dto.kibana_saved_search import KibanaSavedSearch
from lstail.query.kibana_saved_search import ListKibanaSavedSearchesController
from tests.base import BaseTestCase, mock


TEST_CONFIG = Configuration()
TEST_CONFIG.debug = False
TEST_CONFIG.verbose = False
TEST_CONFIG.kibana = mock.Mock(index_name='mocked-index', default_columns=['dummy'])


class ListKibanaSavedSearchesTest(BaseTestCase):

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.kibana_saved_search.detect_elasticsearch_version')
    def test_list_kibana_saved_searches_positive_v7(self, mock_es_detection):
        test_response_kibana6 = self._get_test_data('saved_searches_kibana7')
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_7
        mock_handler = mock.MagicMock()
        mock_handler.request.return_value = test_response_kibana6

        lister = ListKibanaSavedSearchesController(TEST_CONFIG, mock_handler, self._mocked_logger)
        result = lister.list()

        # check
        expected_output = [
            KibanaSavedSearch('Parse Failures', 'tags, logsource, program, message'),
            KibanaSavedSearch(
                'Webserver',
                'http_host, http_clientip, http_verb, message, http_code'),
            KibanaSavedSearch('Webserver 404', 'http_clientip, http_verb, message, http_code')]
        self.assertCountEqual(result, expected_output)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.kibana_saved_search.detect_elasticsearch_version')
    def test_list_kibana_saved_searches_positive_v6(self, mock_es_detection):
        test_response_kibana6 = self._get_test_data('saved_searches_kibana6')
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_6
        mock_handler = mock.MagicMock()
        mock_handler.request.return_value = test_response_kibana6

        lister = ListKibanaSavedSearchesController(TEST_CONFIG, mock_handler, self._mocked_logger)
        result = lister.list()

        # check
        expected_output = [
            KibanaSavedSearch(
                'Dummy saved search 1',
                'host, program, log_level, _id, log_level_no_orig, message'),
            KibanaSavedSearch('Parse Errors', 'tags, logsource, program, message'),
            KibanaSavedSearch('Syslog', 'host, program, message')]
        self.assertCountEqual(result, expected_output)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.kibana_saved_search.detect_elasticsearch_version')
    def test_list_kibana_saved_searches_positive_v4(self, mock_es_detection):
        test_response_kibana4 = self._get_test_data('saved_searches_kibana4')
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_2
        mock_handler = mock.MagicMock()
        mock_handler.request.return_value = test_response_kibana4

        lister = ListKibanaSavedSearchesController(TEST_CONFIG, mock_handler, self._mocked_logger)
        result = lister.list()

        # check
        expected_output = [
            KibanaSavedSearch('Kibana Saved Search 2', 'fromhost, programname'),
            KibanaSavedSearch(
                'Kibana saved search 1',
                'fromhost, requestHost, vHostPort, requestUrl'),
            KibanaSavedSearch('Süslogging', 'fromhost, programname, severity, message')]
        self.assertCountEqual(result, expected_output)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.kibana_saved_search.detect_elasticsearch_version')
    def test_list_kibana_saved_searches_negative_no_hits(self, mock_es_detection):
        test_response = self._get_test_data('saved_searches_empty')
        # empty search response is the same for ES 2.x and 6.x, so this test should suffice
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_6
        mock_handler = mock.MagicMock()
        mock_handler.request.return_value = test_response

        lister = ListKibanaSavedSearchesController(TEST_CONFIG, mock_handler, self._mocked_logger)
        result = lister.list()

        # check
        self.assertEqual(result, [])
