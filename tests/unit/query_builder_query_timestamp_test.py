# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from copy import deepcopy
from datetime import datetime

from lstail.constants import (
    BASE_QUERY_ES2,
    BASE_QUERY_ES6,
    ELASTICSEARCH_MAJOR_VERSION_2,
    ELASTICSEARCH_MAJOR_VERSION_6,
    ELASTICSEARCH_MAJOR_VERSION_7,
)
from lstail.dto.query import Query
from lstail.query.factory import QueryBuilderFactory
from tests.base import BaseTestCase, mock


class QueryBuilderTimestampTest(BaseTestCase):

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_timestamp_query_v6(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_6
        http_handler = mock.MagicMock()

        factory = QueryBuilderFactory(http_handler, self._mocked_logger)
        query_builder = factory.factor(
            'foo', 'bar', 'foo', 'foobar', http_handler, self._mocked_logger)

        timestamp_from = datetime.now()
        # fake filter and query
        base_query = deepcopy(BASE_QUERY_ES6)
        base_query['query']['bool']['must'].append({'something': 'else'})
        query = Query('foo-index', base_query, time_field_name='@timestamp')

        # test with timestamp added
        query_timestamp_added = query_builder.build_query_for_time_range(query, timestamp_from)
        self._evaluate_timestamped_query(
            query_timestamp_added.query['query']['bool']['must'],
            timestamp_from)

        # test with timestamp replaced
        query_timestamp_replaced = query_builder.build_query_for_time_range(
            query_timestamp_added,
            timestamp_from)
        self._evaluate_timestamped_query(
            query_timestamp_replaced.query['query']['bool']['must'],
            timestamp_from)

    # ----------------------------------------------------------------------
    def _evaluate_timestamped_query(self, new_query_filters, timestamp_from):
        range_element_count = 0
        range_filter = None
        for must_filter in new_query_filters:
            if 'range' in must_filter:
                range_element_count += 1
                range_filter = must_filter

        self.assertEqual(range_element_count, 1)
        self.assertEqual(range_filter, {'range': {'@timestamp': {'gt': timestamp_from}}})

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_timestamp_query_v7(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_7
        http_handler = mock.MagicMock()

        factory = QueryBuilderFactory(http_handler, self._mocked_logger)
        query_builder = factory.factor(
            'foo', 'bar', 'foo', 'foobar', http_handler, self._mocked_logger)

        timestamp_from = datetime.now()
        # fake filter and query
        base_query = deepcopy(BASE_QUERY_ES6)
        base_query['query']['bool']['must'].append({'something': 'else'})
        query = Query('foo-index', base_query, time_field_name='@timestamp')

        # test with timestamp added
        query_timestamp_added = query_builder.build_query_for_time_range(query, timestamp_from)
        self._evaluate_timestamped_query(
            query_timestamp_added.query['query']['bool']['must'],
            timestamp_from)

        # test with timestamp replaced
        query_timestamp_replaced = query_builder.build_query_for_time_range(
            query_timestamp_added,
            timestamp_from)
        self._evaluate_timestamped_query(
            query_timestamp_replaced.query['query']['bool']['must'],
            timestamp_from)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_timestamp_query_v2(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_2
        http_handler = mock.MagicMock()

        factory = QueryBuilderFactory(http_handler, self._mocked_logger)
        query_builder = factory.factor(
            'foo', 'bar', 'foo', 'foobar', http_handler, self._mocked_logger)

        timestamp_from = datetime.now()
        # fake filter and query
        base_query = deepcopy(BASE_QUERY_ES2)
        base_query['query']['filtered']['filter']['bool']['must'].append({'something': 'else'})
        query = Query('foo-index', base_query, time_field_name='@timestamp')

        # test with timestamp added
        query_timestamp_added = query_builder.build_query_for_time_range(query, timestamp_from)
        self._evaluate_timestamped_query(
            query_timestamp_added.query['query']['filtered']['filter']['bool']['must'],
            timestamp_from)

        # test with timestamp replaced
        query_timestamp_replaced = query_builder.build_query_for_time_range(
            query_timestamp_added,
            timestamp_from)
        self._evaluate_timestamped_query(
            query_timestamp_replaced.query['query']['filtered']['filter']['bool']['must'],
            timestamp_from)
