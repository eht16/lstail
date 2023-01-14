# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from abc import ABCMeta, abstractmethod
from json import loads
from urllib.error import HTTPError

from lstail.constants import (
    ELASTICSEARCH_DEFAULT_FIELD_TIMESTAMP,
    FILTER_GROUP_MUST,
    FILTER_GROUP_MUST_NOT,
)
from lstail.error import ElasticSearchIndexNotFoundError, UnsupportedFilterTypeError
from lstail.util.http import is_error_http_not_found


########################################################################
class BaseQueryBuilder:

    __metaclass__ = ABCMeta

    _index_time_field_name = '@timestamp'

    # ----------------------------------------------------------------------
    def __init__(
            self,
            config_index_name,
            kibana_index_name,
            saved_search_title,
            custom_search,
            http_handler,
            logger):
        self._config_index_name = config_index_name
        self._kibana_index_name = kibana_index_name
        self._saved_search_title = saved_search_title
        self._custom_search = custom_search
        self._http_handler = http_handler
        self._logger = logger
        self._elasticsearch_version = None
        self._kibana_search = None
        self._search_source = None
        self._base_query = None
        self._index = None
        self._filters = None
        self._filter = None
        self._query = None

    # ----------------------------------------------------------------------
    @abstractmethod
    def build(self):
        pass

    # ----------------------------------------------------------------------
    def _kibana_search_requested(self):
        if not self._kibana_index_name or not self._saved_search_title:
            return False

        return True

    # ----------------------------------------------------------------------
    @abstractmethod
    def _fetch_kibana_search(self):
        pass

    # ----------------------------------------------------------------------
    def _fetch_search_source(self):
        saved_object_metadata = self._kibana_search['kibanaSavedObjectMeta']
        search_source_json = saved_object_metadata['searchSourceJSON']
        self._search_source = loads(search_source_json)

    # ----------------------------------------------------------------------
    def _fetch_base_query(self):
        query = self._get_query_from_search_source()

        # sometimes Kibana saves the main query as simple Lucene search string,
        # sometimes as query object, so if it is string, factor the query manually else use it
        if isinstance(query, (bytes, str)):
            if not query:
                # if there is no query string, search for wildcard to get any results
                query = '*'

            self._base_query = {
                "query_string": {
                    "query": query,
                    "analyze_wildcard": True,
                    "default_field": "*"
                }
            }
        else:
            self._base_query = query

    # ----------------------------------------------------------------------
    @abstractmethod
    def _get_query_from_search_source(self):
        pass

    # ----------------------------------------------------------------------
    def _set_custom_search_on_query(self):
        if not self._custom_search:
            return  # no custom search set

        query = self._base_query
        # between Kibana/ES versions, the exact structure differs, so try to find the correct one
        if 'query_string' in query and 'query' in query['query_string']:
            query['query_string']['query'] = self._custom_search
        else:
            del self._base_query[:]  # clear existing queries
            search_query = {
                'query_string':
                {
                    'analyze_wildcard': True,
                    'query': self._custom_search
                }
            }
            self._base_query.append(search_query)

    # ----------------------------------------------------------------------
    def _factor_filters(self):
        self._setup_filter_mapping()
        for self._filter in self._search_source['filter']:
            self._factor_filter()

    # ----------------------------------------------------------------------
    def _setup_filter_mapping(self):
        self._filters = {FILTER_GROUP_MUST: [], FILTER_GROUP_MUST_NOT: []}

    # ----------------------------------------------------------------------
    def _factor_filter(self):
        if not self._filter or self._filter['meta']['disabled']:
            return

        try:
            filter_query = self._factor_filter_query_by_type()
        except UnsupportedFilterTypeError:
            return

        if self._filter['meta']['negate']:
            filter_group = FILTER_GROUP_MUST_NOT
        else:
            filter_group = FILTER_GROUP_MUST

        self._filters[filter_group].append(filter_query)

    # ----------------------------------------------------------------------
    @abstractmethod
    def _factor_filter_query_by_type(self):
        pass

    # ----------------------------------------------------------------------
    @abstractmethod
    def _fetch_index(self):
        pass

    # ----------------------------------------------------------------------
    def _assert_index_exists(self):
        if not self._test_index_exists(self._index):
            raise ElasticSearchIndexNotFoundError(self._index)

    # ----------------------------------------------------------------------
    def _test_index_exists(self, index_name):
        try:
            self._http_handler.request(index_name, http_method='HEAD')
        except HTTPError as exc:
            if is_error_http_not_found(exc):
                return False
            else:
                raise
        else:
            return True

    # ----------------------------------------------------------------------
    def _fetch_index_from_config(self):
        self._index = self._config_index_name

    # ----------------------------------------------------------------------
    @abstractmethod
    def _factor_query(self):
        pass

    # ----------------------------------------------------------------------
    @abstractmethod
    def build_query_for_time_range(self, query, timestamp_from):
        pass

    # ----------------------------------------------------------------------
    def _build_query_for_time_range(self, query, must_filters, timestamp_from):
        time_range__filter = {self._index_time_field_name: {'gt': timestamp_from}}
        for must_filter in must_filters:
            if 'range' in must_filter:
                if self._index_time_field_name in must_filter['range']:
                    must_filter['range'] = time_range__filter
                    break
        else:
            must_filters.append({'range': time_range__filter})

        return query

    # ----------------------------------------------------------------------
    def _replace_timestamp_field_name_in_query(self, query):
        if self._index_time_field_name:
            if self._index_time_field_name != ELASTICSEARCH_DEFAULT_FIELD_TIMESTAMP:
                sort = query['sort'][0][ELASTICSEARCH_DEFAULT_FIELD_TIMESTAMP]
                query['sort'][0][self._index_time_field_name] = sort
                del query['sort'][0][ELASTICSEARCH_DEFAULT_FIELD_TIMESTAMP]
