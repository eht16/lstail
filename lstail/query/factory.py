# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from lstail.constants import ELASTICSEARCH_MAJOR_VERSION_2, ELASTICSEARCH_MAJOR_VERSION_6
from lstail.query.elasticsearch_2 import ElasticSearch2QueryBuilder
from lstail.query.elasticsearch_6 import ElasticSearch6QueryBuilder
from lstail.query.elasticsearch_7 import ElasticSearch7QueryBuilder
from lstail.util.http import detect_elasticsearch_version


########################################################################
class QueryBuilderFactory:

    # ----------------------------------------------------------------------
    def __init__(self, http_handler, logger):
        self._http_handler = http_handler
        self._logger = logger
        self._elasticsearch_version = None
        self._query_builder_class = None

    # ----------------------------------------------------------------------
    def factor(self, *args, **kwargs):
        self._detect_elasticsearch_version()
        self._fetch_query_builder_class()

        return self._query_builder_class(*args, **kwargs)

    # ----------------------------------------------------------------------
    def _detect_elasticsearch_version(self):
        self._elasticsearch_version = detect_elasticsearch_version(self._http_handler, self._logger)

    # ----------------------------------------------------------------------
    def _fetch_query_builder_class(self):
        if self._elasticsearch_version == ELASTICSEARCH_MAJOR_VERSION_2:
            self._query_builder_class = ElasticSearch2QueryBuilder
        elif self._elasticsearch_version == ELASTICSEARCH_MAJOR_VERSION_6:
            self._query_builder_class = ElasticSearch6QueryBuilder
        else:
            self._query_builder_class = ElasticSearch7QueryBuilder
