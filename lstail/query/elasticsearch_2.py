# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from copy import deepcopy
from json import dumps

from lstail.constants import (
    BASE_QUERY_ES2,
    FILTER_GROUP_MUST,
    FILTER_GROUP_MUST_NOT,
    KIBANA4_SEARCH_QUERY,
)
from lstail.dto.query import Query
from lstail.error import KibanaSavedSearchNotFoundError
from lstail.query.base import BaseQueryBuilder


########################################################################
class ElasticSearch2QueryBuilder(BaseQueryBuilder):

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

        self._assert_index_exists()
        self._factor_query()
        return self._query

    # ----------------------------------------------------------------------
    def _fetch_kibana_search(self):
        # set search title
        query = deepcopy(KIBANA4_SEARCH_QUERY)
        query['query']['bool']['must'][0]['match']['title'] = self._saved_search_title
        query_json = dumps(query)

        # request
        url = f'{self._kibana_index_name}/_search'
        response = self._http_handler.request(url, data=query_json)

        # did we find it?
        if not response['hits']['total']:
            message = f'Kibana saved search "{self._saved_search_title}" not found!'
            raise KibanaSavedSearchNotFoundError(message)

        # take the first hit, as we sorted by _score DESC, this should be the best match
        best_match = response['hits']['hits'][0]
        self._kibana_search = best_match['_source']
        # tell the logger which columns to use
        self._logger.update_display_columns(self._kibana_search['columns'])
        self._logger.debug('Using Kibana saved search "%s"', self._kibana_search['title'])

    # ----------------------------------------------------------------------
    def _get_query_from_search_source(self):
        return self._search_source['query']

    # ----------------------------------------------------------------------
    def _factor_filter_query_by_type(self):
        return dict(query=self._filter['query'])

    # ----------------------------------------------------------------------
    def _fetch_index(self):
        self._index = self._search_source['index']

    # ----------------------------------------------------------------------
    def _factor_base_query(self):
        self._base_query = {
            'query_string': {
                'query': '*'
            }
        }

    # ----------------------------------------------------------------------
    def _factor_query(self):
        query = deepcopy(BASE_QUERY_ES2)
        if self._base_query:
            query['query']['filtered']['query'] = self._base_query

        if self._filters:
            for filter_group in (FILTER_GROUP_MUST, FILTER_GROUP_MUST_NOT):
                for filter_query in self._filters[filter_group]:
                    query['query']['filtered']['filter']['bool'][filter_group].append(filter_query)

        self._replace_timestamp_field_name_in_query(query)

        self._query = Query(
            index=self._index,
            query=query,
            time_field_name=self._index_time_field_name)

    # ----------------------------------------------------------------------
    def build_query_for_time_range(self, query, timestamp_from):
        new_query = query.clone()
        must_filters = new_query.query['query']['filtered']['filter']['bool']['must']
        return self._build_query_for_time_range(new_query, must_filters, timestamp_from)
