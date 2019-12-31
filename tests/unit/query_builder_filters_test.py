# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from lstail.constants import FILTER_GROUP_MUST, FILTER_GROUP_MUST_NOT
from lstail.query.elasticsearch_2 import ElasticSearch2QueryBuilder
from lstail.query.elasticsearch_6 import ElasticSearch6QueryBuilder
from tests.base import BaseTestCase, mock


# pylint: disable=protected-access,bad-continuation


class QueryBuilderCustomSearchTest(BaseTestCase):

    # ----------------------------------------------------------------------
    def test_filter_v6_phrase(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_phrase = {'$state': {'store': 'appState'},
            'meta': {'alias': 'filter_is', 'disabled': False, 'index': 'foo', 'key': 'action',
                     'negate': False, 'params': {'query': 'test', 'type': 'phrase'},
                     'type': 'phrase', 'value': 'test'},
            'query': {'match': {'action': {'query': 'test', 'type': 'phrase'}}}}
        expected_result = [{'match_phrase': {'action': {'query': 'test'}}}]
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_phrase):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, expected_result)
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def _factor_query_builder(self, builder_class):
        mocked_handler = mock.MagicMock()
        mocked_logger = mock.MagicMock()
        query_builder = builder_class(
            config_index_name='foo',
            kibana_index_name='bar',
            saved_search_title='foo',
            custom_search='bar',
            http_handler=mocked_handler,
            logger=mocked_logger)
        return query_builder

    # ----------------------------------------------------------------------
    def test_filter_v6_empty(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_phrase = {}
        expected_result = []
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_phrase):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, expected_result)
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_phrase_not(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_phrase = {'$state': {'store': 'appState'},
            'meta': {'alias': 'isnot', 'disabled': False, 'index': 'foo', 'key': 'dns.type',
                     'negate': True, 'params': {'query': 'B', 'type': 'phrase'},
                     'type': 'phrase', 'value': 'bar'},
            'query': {'match': {'dns.type': {'query': 'B', 'type': 'phrase'}}}}
        expected_result = [{'match_phrase': {'dns.type': {'query': 'bar'}}}]
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_phrase):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, expected_result)
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_phrase_disabled(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_phrase = {'$state': {'store': 'appState'},
            'meta': {'alias': 'isnot', 'disabled': True, 'index': 'foo', 'key': 'dns.type',
                     'negate': True, 'params': {'query': 'B', 'type': 'phrase'},
                     'type': 'phrase', 'value': 'bar'},
            'query': {'match': {'dns.type': {'query': 'B', 'type': 'phrase'}}}}
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_phrase):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_phrases(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_phrase = {'$state': {'store': 'appState'},
            'meta': {'alias': None, 'disabled': False, 'index': 'foo', 'key': 'dns.type',
                     'negate': False, 'params': ['A', 'PTR', 'AAAA'], 'type': 'phrases',
                     'value': 'A, PTR, AAAA'}, 'query': {'bool': {}}}
        expected_result = [{'bool': {'minimum_should_match': 1, 'should':
            [{'match_phrase': {'dns.type': 'A'}}, {'match_phrase': {'dns.type': 'PTR'}},
             {'match_phrase': {'dns.type': 'AAAA'}}]}}]
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_phrase):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, expected_result)
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_phrases_not(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_phrase = {'$state': {'store': 'appState'},
            'meta': {'alias': 'isnotoneof', 'disabled': False, 'index': 'foo', 'key': 'dns.type',
                     'negate': True, 'params': ['MX', 'NS'], 'type': 'phrases', 'value': 'MX, NS'},
            'query': {'bool': {}}}
        expected_result = [{'bool': {'minimum_should_match': 1, 'should':
            [{'match_phrase': {'dns.type': 'MX'}}, {'match_phrase': {'dns.type': 'NS'}}]}}]
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_phrase):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, expected_result)
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_phrases_disabled(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_phrase = {'$state': {'store': 'appState'},
            'meta': {'alias': 'isnotoneof', 'disabled': True, 'index': 'foo', 'key': 'dns.type',
                     'negate': True, 'params': ['MX', 'NS'], 'type': 'phrases', 'value': 'MX, NS'},
            'query': {'bool': {}}}
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_phrase):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_exists(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_exists = {'$state': {'store': 'appState'},
            'exists': {'field': 'dns.query'}, 'meta': {'alias': None, 'disabled': False,
            'index': 'foo', 'key': 'dns.query', 'negate': False,
            'type': 'exists', 'value': 'exists'}}
        expected_result = [{'exists': {'field': 'dns.query'}}]
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_exists):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, expected_result)
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_exists_not(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_exists = {'$state': {'store': 'appState'},
            'exists': {'field': 'dns.query'}, 'meta': {'alias': None, 'disabled': False,
            'index': 'foo', 'key': 'dns.query', 'negate': True,
            'type': 'exists', 'value': 'exists'}}
        expected_result = [{'exists': {'field': 'dns.query'}}]
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_exists):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, expected_result)
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_exists_disabled(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_exists = {'$state': {'store': 'appState'},
            'exists': {'field': 'dns.query'}, 'meta': {'alias': None, 'disabled': True,
            'index': 'foo', 'key': 'dns.query', 'negate': True,
            'type': 'exists', 'value': 'exists'}}
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_exists):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_range(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_range = {'$state': {'store': 'appState'}, 'meta': {
            'alias': 'isbetween', 'disabled': False, 'index': 'foo', 'key': 'dns.client_ip',
            'negate': False, 'params': {'gte': '0.0.0.0', 'lt': '255.255.255.255'},
            'type': 'range', 'value': '0.0.0.0 to 255.255.255.255'}, 'range': {
            'dns.client_ip': {'gte': '0.0.0.0', 'lt': '255.255.255.255'}}}
        expected_result = [{'range': {'dns.client_ip':
            {'gte': '0.0.0.0', 'lt': '255.255.255.255'}}}]
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_range):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, expected_result)
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_range_not(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_range = {'$state': {'store': 'appState'}, 'meta': {
            'alias': 'isbetween', 'disabled': False, 'index': 'foo', 'key': 'dns.client_ip',
            'negate': True, 'params': {'gte': '0.0.0.0', 'lt': '255.255.255.255'},
            'type': 'range', 'value': '0.0.0.0 to 255.255.255.255'}, 'range': {
            'dns.client_ip': {'gte': '0.0.0.0', 'lt': '255.255.255.255'}}}
        expected_result = [{'range': {'dns.client_ip':
            {'gte': '0.0.0.0', 'lt': '255.255.255.255'}}}]
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_range):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, expected_result)
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v6_range_disabled(self):
        query_builder = self._factor_query_builder(ElasticSearch6QueryBuilder)

        kibana_saved_search_filter_range = {'$state': {'store': 'appState'}, 'meta': {
            'alias': 'isbetween', 'disabled': True, 'index': 'foo', 'key': 'dns.client_ip',
            'negate': False, 'params': {'gte': '0.0.0.0', 'lt': '255.255.255.255'},
            'type': 'range', 'value': '0.0.0.0 to 255.255.255.255'}, 'range': {
            'dns.client_ip': {'gte': '0.0.0.0', 'lt': '255.255.255.255'}}}
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana_saved_search_filter_range):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v4_empty(self):
        query_builder = self._factor_query_builder(ElasticSearch2QueryBuilder)
        kibana4_filter = {}
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana4_filter):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v4(self):
        query_builder = self._factor_query_builder(ElasticSearch2QueryBuilder)
        kibana4_filter = {'$state': {'store': 'appState'}, 'meta': {
            'alias': None, 'disabled': False, 'index': 'logstash-*', 'key': 'applicationName',
            'negate': False, 'value': 'Webserver'},
            'query': {'match': {'applicationName': {'query': 'Webserver', 'type': 'phrase'}}}}
        expected_result = [{'query': kibana4_filter['query']}]
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana4_filter):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, expected_result)

    # ----------------------------------------------------------------------
    def test_filter_v4_not(self):
        query_builder = self._factor_query_builder(ElasticSearch2QueryBuilder)
        kibana4_filter = {'$state': {'store': 'appState'}, 'meta': {
            'alias': None, 'disabled': False, 'index': 'logstash-*', 'key': 'applicationName',
            'negate': True, 'value': 'Webserver'},
            'query': {'match': {'applicationName': {'query': 'Webserver', 'type': 'phrase'}}}}
        expected_result = [{'query': kibana4_filter['query']}]
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana4_filter):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, expected_result)
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])

    # ----------------------------------------------------------------------
    def test_filter_v4_disabled(self):
        query_builder = self._factor_query_builder(ElasticSearch2QueryBuilder)
        kibana4_filter = {'$state': {'store': 'appState'}, 'meta': {
            'alias': None, 'disabled': True, 'index': 'logstash-*', 'key': 'applicationName',
            'negate': True, 'value': 'Webserver'},
            'query': {'match': {'applicationName': {'query': 'Webserver', 'type': 'phrase'}}}}
        # test
        with mock.patch.object(query_builder, '_filter', new=kibana4_filter):
            query_builder._setup_filter_mapping()
            query_builder._factor_filter()
            result = query_builder._filters[FILTER_GROUP_MUST_NOT]
            self.assertEqual(result, [])
            result = query_builder._filters[FILTER_GROUP_MUST]
            self.assertEqual(result, [])
