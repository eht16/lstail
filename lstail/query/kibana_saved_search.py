# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from json import dumps

from lstail.constants import (
    ELASTICSEARCH_MAJOR_VERSION_2,
    ELASTICSEARCH_MAJOR_VERSION_6,
    ELASTICSEARCH_MAJOR_VERSION_7,
    KIBANA6_SAVED_SEARCH_LIST_QUERY,
)
from lstail.dto.kibana_saved_search import KibanaSavedSearch
from lstail.util.http import detect_elasticsearch_version


########################################################################
class ListKibanaSavedSearchesController:

    # ----------------------------------------------------------------------
    def __init__(self, config, http_handler, logger):
        self._config = config
        self._http_handler = http_handler
        self._logger = logger
        self._elasticsearch_version = ELASTICSEARCH_MAJOR_VERSION_6
        self._kibana_search_response = None
        self._kibana_saved_searches = None

    # ----------------------------------------------------------------------
    def list(self):
        self._detect_elasticsearch_version()
        self._fetch_kibana_saved_searches()

        if self._kibana_response_empty():  # if still emoty, give up
            return []

        self._parse_response()
        return self._kibana_saved_searches

    # ----------------------------------------------------------------------
    def _detect_elasticsearch_version(self):
        self._elasticsearch_version = detect_elasticsearch_version(self._http_handler, self._logger)

    # ----------------------------------------------------------------------
    def _fetch_kibana_saved_searches(self):
        if self._elasticsearch_version == ELASTICSEARCH_MAJOR_VERSION_2:
            self._fetch_kibana_saved_searches_v4()
        else:
            self._fetch_kibana_saved_searches_v6()

    # ----------------------------------------------------------------------
    def _fetch_kibana_saved_searches_v4(self):
        url = f'{self._config.kibana.index_name}/search/_search?size=1000'
        self._kibana_search_response = self._request_kibana_saved_searches(url)

    # ----------------------------------------------------------------------
    def _request_kibana_saved_searches(self, url, data=None):
        data_json = dumps(data) if data else None
        return self._http_handler.request(url, data_json)

    # ----------------------------------------------------------------------
    def _fetch_kibana_saved_searches_v6(self):
        url = f'{self._config.kibana.index_name}/_search'
        self._kibana_search_response = self._request_kibana_saved_searches(
            url,
            KIBANA6_SAVED_SEARCH_LIST_QUERY)

    # ----------------------------------------------------------------------
    def _kibana_response_empty(self):
        if self._elasticsearch_version >= ELASTICSEARCH_MAJOR_VERSION_7:
            return not self._kibana_search_response or \
                not self._kibana_search_response['hits']['total']['value']
        else:
            return not self._kibana_search_response or \
                not self._kibana_search_response['hits']['total']

    # ----------------------------------------------------------------------
    def _parse_response(self):
        self._kibana_saved_searches = []
        response_hits = self._kibana_search_response['hits']['hits']

        saved_searches = sorted(
            response_hits,
            key=lambda hit: self._get_item_from_saved_search(hit, 'title'))

        for saved_search in saved_searches:
            columns = ', '.join(self._get_item_from_saved_search(saved_search, 'columns'))
            title = self._get_item_from_saved_search(saved_search, 'title')
            saved_search = KibanaSavedSearch(title, columns)
            self._kibana_saved_searches.append(saved_search)

    # ----------------------------------------------------------------------
    def _get_item_from_saved_search(self, saved_search, key):
        if self._elasticsearch_version == ELASTICSEARCH_MAJOR_VERSION_2:
            return saved_search['_source'][key]

        # Kibana 6 is the default
        return saved_search['_source']['search'][key]
