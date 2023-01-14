# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from copy import deepcopy
from json import dumps

from lstail.constants import (
    BASE_QUERY_ES6,
    FILTER_GROUP_MUST,
    FILTER_GROUP_MUST_NOT,
    KIBANA6_INDEX_PATTERN_SEARCH_QUERY,
    KIBANA6_SEARCH_QUERY,
)
from lstail.dto.query import Query
from lstail.error import KibanaSavedSearchNotFoundError, UnsupportedFilterTypeError
from lstail.query.base import BaseQueryBuilder


########################################################################
class ElasticSearch6QueryBuilder(BaseQueryBuilder):

    # ----------------------------------------------------------------------
    def build(self):
        if self._kibana_search_requested():
            self._fetch_kibana_search()
            self._fetch_search_source()
            self._fetch_base_query()
            self._set_custom_search_on_query()
            self._factor_filters()
            self._fetch_index()
        else:
            self._factor_base_query()
            self._set_custom_search_on_query()
            self._fetch_index_from_config()

        self._factor_query()
        return self._query

    # ----------------------------------------------------------------------
    def _fetch_kibana_search(self):
        # set search title
        query = deepcopy(KIBANA6_SEARCH_QUERY)
        query['query']['bool']['must'][0]['match']['search.title'] = self._saved_search_title
        query_json = dumps(query)

        # request
        url = f'{self._kibana_index_name}/_search'
        response = self._http_handler.request(url, data=query_json)

        # did we find it?
        self._assert_saved_search_found(response)

        # take the first hit, as we sorted by _score DESC, this should be the best match
        best_match = response['hits']['hits'][0]
        self._kibana_search = best_match['_source']['search']
        # tell the logger which columns to use
        self._logger.update_display_columns(self._kibana_search['columns'])
        self._logger.debug(f'Using Kibana saved search "{self._kibana_search["title"]}"')

    # ----------------------------------------------------------------------
    def _assert_saved_search_found(self, response):
        if not response['hits']['total']:
            message = f'Kibana saved search "{self._saved_search_title}" not found!'
            raise KibanaSavedSearchNotFoundError(message)

    # ----------------------------------------------------------------------
    def _get_query_from_search_source(self):
        return self._search_source['query']['query']

    # ----------------------------------------------------------------------
    def _factor_filter_query_by_type(self):
        filter_type = self._filter['meta'].get('type')
        # simple match based on x == y, also 'x != y', handled via 'negate' flag
        if filter_type == 'phrase':
            return self._factor_filter_query_for_type_phrase()
        # "one of", also 'not one of', handled via 'negate' flag
        elif filter_type == 'phrases':  #
            return self._factor_filter_query_for_type_phrases()
        # 'exists' check, also 'not exists', handled via 'negate' flag
        elif filter_type == 'exists':
            return self._factor_filter_query_for_type_exists()
        # 'between' check, also 'not between', handled via 'negate' flag
        elif filter_type == 'range':
            return self._factor_filter_query_for_type_range()

        self._logger.info(f'Unknown filter type "{filter_type}", skipping!')
        raise UnsupportedFilterTypeError()

    # ----------------------------------------------------------------------
    def _factor_filter_query_for_type_phrase(self):
        return {
            "match_phrase": {
                self._filter['meta']['key']: {
                    "query": self._filter['meta']['value']
                }
            }
        }

    # ----------------------------------------------------------------------
    def _factor_filter_query_for_type_phrases(self):
        phrases = []
        for param in self._filter['meta']['params']:
            phrase = {
                "match_phrase": {
                    self._filter['meta']['key']: param
                }
            }
            phrases.append(phrase)
        return {
            "bool": {
                "should": phrases,
                "minimum_should_match": 1
            }
        }

    # ----------------------------------------------------------------------
    def _factor_filter_query_for_type_exists(self):
        return {
            "exists": {
                "field": self._filter['meta']['key']
            }
        }

    # ----------------------------------------------------------------------
    def _factor_filter_query_for_type_range(self):
        return {
            "range": {
                self._filter['meta']['key']: {
                    "gte": self._filter['meta']['params']['gte'],
                    "lt": self._filter['meta']['params']['lt']
                }
            }
        }

    # ----------------------------------------------------------------------
    def _fetch_index(self):
        index_pattern_id = self._search_source['index']
        if self._test_index_exists(index_pattern_id):
            self._index = index_pattern_id
        else:
            index = self._get_index_by_id(index_pattern_id)
            self._index = index['title']
            self._index_time_field_name = index['timeFieldName']

    # ----------------------------------------------------------------------
    def _get_index_by_id(self, index_pattern_id):
        query = deepcopy(KIBANA6_INDEX_PATTERN_SEARCH_QUERY)
        # replace index ID in query
        query['query']['match']['_id'] = f'index-pattern:{index_pattern_id}'
        query_json = dumps(query)
        url = f'{self._kibana_index_name}/_search'
        # search index by its ID
        response = self._http_handler.request(url, data=query_json)
        # not found?
        if not response['hits']['total']:
            message = f'Index reference "{self._kibana_search["title"]}" as found in saved ' \
                      f'search "{index_pattern_id}" not found!'
            raise RuntimeError(message)

        return response['hits']['hits'][0]['_source']['index-pattern']

    # ----------------------------------------------------------------------
    def _factor_base_query(self):
        self._base_query = {
            "query_string": {
                "analyze_wildcard": True,
                "default_field": "*",
                "query": "*"
            }
        }

    # ----------------------------------------------------------------------
    def _factor_query(self):
        query = deepcopy(BASE_QUERY_ES6)
        if self._base_query:
            query['query']['bool']['must'].append(self._base_query)

        if self._filters:
            for filter_group in (FILTER_GROUP_MUST, FILTER_GROUP_MUST_NOT):
                for filter_query in self._filters[filter_group]:
                    query['query']['bool'][filter_group].append(filter_query)

        self._replace_timestamp_field_name_in_query(query)

        self._query = Query(
            index=self._index,
            query=query,
            time_field_name=self._index_time_field_name)

    # ----------------------------------------------------------------------
    def build_query_for_time_range(self, query, timestamp_from):
        new_query = query.clone()
        must_filters = new_query.query['query']['bool']['must']
        return self._build_query_for_time_range(new_query, must_filters, timestamp_from)
