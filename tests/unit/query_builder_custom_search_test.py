# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from lstail.constants import ELASTICSEARCH_MAJOR_VERSION_2, ELASTICSEARCH_MAJOR_VERSION_6
from lstail.query.factory import QueryBuilderFactory
from tests.base import BaseTestCase, mock


class QueryBuilderCustomSearchTest(BaseTestCase):

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_custom_search_v6_with_saved_search_and_search_query(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_6

        test_response_kibana6 = self._get_test_data('saved_searches_kibana6')
        mocked_handler = mock.MagicMock()
        mocked_handler.request.return_value = test_response_kibana6
        mocked_logger = mock.MagicMock()

        custom_search = 'host: foobar'
        saved_search = 'Parse Errors'
        # test
        test_query = self._factor_query(mocked_handler, mocked_logger, saved_search, custom_search)
        self._evaluate_custom_search_query_6(test_query, custom_search)

    # ----------------------------------------------------------------------
    def _factor_query(self, mocked_handler, mocked_logger, saved_search, custom_search):
        factory = QueryBuilderFactory(mocked_handler, self._mocked_logger)
        query_builder = factory.factor(
            config_index_name='foo',
            kibana_index_name='bar',
            saved_search_title=saved_search,
            custom_search=custom_search,
            http_handler=mocked_handler,
            logger=mocked_logger)
        return query_builder.build()

    # ----------------------------------------------------------------------
    def _evaluate_custom_search_query_6(self, query, custom_search):
        query_filters = query.query['query']['bool']['must']
        query_element_count = 0
        query_filter = None
        for must_filter in query_filters:
            if 'query_string' in must_filter:
                query_element_count += 1
                query_filter = must_filter

        self.assertEqual(query_element_count, 1)
        self.assertEqual(query_filter['query_string']['query'], custom_search)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_custom_search_v6_without_saved_search_and_search_query(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_6
        mocked_handler = mock.MagicMock()
        mocked_logger = mock.MagicMock()

        custom_search = 'host: foobar'
        saved_search = None
        # test
        test_query = self._factor_query(mocked_handler, mocked_logger, saved_search, custom_search)
        self._evaluate_custom_search_query_6(test_query, custom_search)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_custom_search_v6_without_saved_search_and_no_search_query(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_6
        mocked_handler = mock.MagicMock()
        mocked_logger = mock.MagicMock()

        custom_search = None
        saved_search = None
        # test
        test_query = self._factor_query(mocked_handler, mocked_logger, saved_search, custom_search)
        self._evaluate_custom_search_query_6(test_query, '*')

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_custom_search_v4_with_saved_search_and_search_query(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_2
        test_response_kibana4 = self._get_test_data('saved_searches_kibana4')
        mocked_handler = mock.MagicMock()
        mocked_handler.request.return_value = test_response_kibana4
        mocked_logger = mock.MagicMock()

        custom_search = 'host: foobar'
        saved_search = 'Parse Errors'
        # test
        test_query = self._factor_query(mocked_handler, mocked_logger, saved_search, custom_search)
        self._evaluate_custom_search_query_4(test_query, custom_search)

    # ----------------------------------------------------------------------
    def _evaluate_custom_search_query_4(self, query, custom_search):
        query_filter = query.query['query']['filtered']['query']['query_string']['query']
        self.assertEqual(query_filter, custom_search)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_custom_search_v4_without_saved_search_and_search_query(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_2
        mocked_handler = mock.MagicMock()
        mocked_logger = mock.MagicMock()

        custom_search = 'host: foobar'
        saved_search = None
        # test
        test_query = self._factor_query(mocked_handler, mocked_logger, saved_search, custom_search)
        self._evaluate_custom_search_query_4(test_query, custom_search)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_custom_search_v4_without_saved_search_and_no_search_query(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_2
        mocked_handler = mock.MagicMock()
        mocked_logger = mock.MagicMock()

        custom_search = None
        saved_search = None
        # test
        test_query = self._factor_query(mocked_handler, mocked_logger, saved_search, custom_search)
        self._evaluate_custom_search_query_4(test_query, '*')
