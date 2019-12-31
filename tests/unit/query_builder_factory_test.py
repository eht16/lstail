# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from lstail.constants import (
    ELASTICSEARCH_MAJOR_VERSION_2,
    ELASTICSEARCH_MAJOR_VERSION_6,
    ELASTICSEARCH_MAJOR_VERSION_7,
)
from lstail.query.elasticsearch_2 import ElasticSearch2QueryBuilder
from lstail.query.elasticsearch_6 import ElasticSearch6QueryBuilder
from lstail.query.elasticsearch_7 import ElasticSearch7QueryBuilder
from lstail.query.factory import QueryBuilderFactory
from tests.base import BaseTestCase, mock


class QueryBuilderFactoryTest(BaseTestCase):

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_detect_elasticsearch_version_v2(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_2
        http_handler = mock.MagicMock()

        factory = QueryBuilderFactory(http_handler, self._mocked_logger)
        query_builder = factory.factor(
            'foo', 'bar', 'foo', 'foobar', http_handler, self._mocked_logger)

        self.assertTrue(isinstance(query_builder, ElasticSearch2QueryBuilder))

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_detect_elasticsearch_version_v6(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_6
        http_handler = mock.MagicMock()

        factory = QueryBuilderFactory(http_handler, self._mocked_logger)
        query_builder = factory.factor(
            'foo', 'bar', 'foo', 'foobar', http_handler, self._mocked_logger)

        self.assertTrue(isinstance(query_builder, ElasticSearch6QueryBuilder))

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.factory.detect_elasticsearch_version')
    def test_detect_elasticsearch_version_v7(self, mock_es_detection):
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_7
        http_handler = mock.MagicMock()

        factory = QueryBuilderFactory(http_handler, self._mocked_logger)
        query_builder = factory.factor(
            'foo', 'bar', 'foo', 'foobar', http_handler, self._mocked_logger)

        self.assertTrue(isinstance(query_builder, ElasticSearch7QueryBuilder))
