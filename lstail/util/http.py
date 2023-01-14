# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from urllib.error import HTTPError

from lstail.constants import (
    DEFAULT_ELASTICSEARCH_MAJOR_VERSION,
    ELASTICSEARCH_MAJOR_VERSION_2,
    ELASTICSEARCH_MAJOR_VERSION_6,
    ELASTICSEARCH_MAJOR_VERSION_7,
)


# ----------------------------------------------------------------------
def is_error_http_not_found(exc):
    if hasattr(exc, 'code') and exc.code == 404:
        return True

    return False


# ----------------------------------------------------------------------
def detect_elasticsearch_version(http_handler, logger):
    def _log_error(exc):
        logger.info(f'Assuming ElasticSearch major version {es_major_version}.x, error: {exc}')

    exact_version = '<not detected>'
    es_major_version = DEFAULT_ELASTICSEARCH_MAJOR_VERSION
    try:
        cluster_state = http_handler.request('/')
    except HTTPError as exc:
        _log_error(exc)
    else:
        try:
            exact_version = cluster_state['version']['number']

            # OpenSearch
            if cluster_state['version'].get('distribution') == "opensearch":
                es_major_version = ELASTICSEARCH_MAJOR_VERSION_7
            # ElasticSearch
            elif exact_version.startswith('2.'):
                es_major_version = ELASTICSEARCH_MAJOR_VERSION_2
            elif exact_version.startswith('5.') or exact_version.startswith('6.'):
                es_major_version = ELASTICSEARCH_MAJOR_VERSION_6
            elif exact_version.startswith('7.'):
                es_major_version = ELASTICSEARCH_MAJOR_VERSION_7
        except (KeyError, TypeError) as exc:
            _log_error(exc)

    logger.debug(f'Using ElasticSearch major version {es_major_version} ({exact_version})')
    return es_major_version
