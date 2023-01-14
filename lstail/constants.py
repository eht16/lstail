# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

import os
import sys

from lstail import __version__ as VERSION  # noqa


PROGRAM_NAME = os.path.basename(sys.argv[0])

LSTAIL_INTERNAL_DOCUMENT_ID = 'ls-internal-document-id'
LSTAIL_FALLBACK_FIELD_VALUE = '<unset>'
LSTAIL_DEFAULT_FIELD_TIMESTAMP = 'timestamp'
LSTAIL_DEFAULT_FIELD_DOCUMENT_ID = 'document_id'
LSTAIL_DEFAULT_FIELD_MESSAGE = 'message'

# fallback encoding to be used for log events (tried to be read from the response headers first)
LOG_ENCODING = 'utf-8'

NON_RETRYING_STATUS_CODES = (400, 401, 404, 406)
# number of seconds to wait between retrying HTTP calls
HTTP_RETRYING_PAUSE = 1.0

ELASTICSEARCH_DEFAULT_FIELD_TIMESTAMP = '@timestamp'

# default format
ELASTICSEARCH_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
# supported formats
ELASTICSEARCH_TIMESTAMP_FORMATS = (
    ELASTICSEARCH_TIMESTAMP_FORMAT,
    '%Y-%m-%dT%H:%M:%S.%f',
    '%Y-%m-%dT%H:%M:%S.%f+00:00',
    '%Y-%m-%dT%H:%M:%S+00:00',
    '%d/%b/%Y:%H:%M:%S %z',
)

FILTER_GROUP_MUST = 'must'
FILTER_GROUP_MUST_NOT = 'must_not'

# ES / Kibana version 6 or newer
BASE_QUERY_ES6 = {
    'query': {
        'bool': {
            'must': [],  # here comes the main query and filters
            'must_not': []  # inversed filters
        },
    },
    'size': 10000,
    'sort': [
        {
            # time field name will be replaced by the fime field name found in the index pattern
            ELASTICSEARCH_DEFAULT_FIELD_TIMESTAMP: {
                'order': 'desc',
                'unmapped_type': 'boolean'
            }
        }
    ]
}

BASE_QUERY_ES2 = {
    'query': {
        'filtered': {
            'filter': {
                'bool': {
                    'must': [],  # filters
                    'must_not': []  # inversed filters
                }
            },
            'query': {
                'language': 'lucene',
                'query': {
                    'query_string': {
                        'analyze_wildcard': True,
                        'query': '*'  # will be replaced by a custom search if necessary
                    }
                }
            }
        }
    },
    'size': 10000,
    'sort': [
        {
            # time field name will be replaced by the fime field name found in the index pattern
            ELASTICSEARCH_DEFAULT_FIELD_TIMESTAMP: {
                'order': 'desc',
                'unmapped_type': 'boolean'
            }
        }
    ]
}

ELASTICSEARCH_MAJOR_VERSION_2 = 2
ELASTICSEARCH_MAJOR_VERSION_6 = 6
ELASTICSEARCH_MAJOR_VERSION_7 = 7

DEFAULT_ELASTICSEARCH_MAJOR_VERSION = ELASTICSEARCH_MAJOR_VERSION_7


# ES / Kibana version 6 or newer
KIBANA6_SEARCH_QUERY = {
    'query': {
        'bool': {
            'must': [
                {
                    'match': {
                        'search.title': None  # will be replaced by real title before execution
                    }
                },
                {
                    'match': {
                        'type': 'search',
                    }
                }
            ]
        }
    },
    'sort': [
        {
            '_score': {
                'order': 'desc'
            }
        }
    ]
}


KIBANA4_SEARCH_QUERY = {
    'query': {
        'bool': {
            'must': [
                {
                    'match': {
                        'title': None  # will be replaced by real title before execution
                    }
                },
                {
                    'term': {
                        '_type': 'search'
                    }
                }
            ]
        }
    },
    'sort': [
        {
            '_score': {
                'order': 'desc'
            }
        }
    ]
}


# ES / Kibana version 6 or newer
KIBANA6_SAVED_SEARCH_LIST_QUERY = {
    'query': {
        'match': {
            'type': 'search'  # Kibana 6.x
        }
    },
    'size': 1000
}

# ES / Kibana version 6 or newer
KIBANA6_INDEX_PATTERN_SEARCH_QUERY = {
    "query": {
        "match": {
            "_id": None  # will be replaced by real id before execution
        }
    }
}

TERM_COLOR_WARNING = 'yellow'
TERM_COLOR_ERROR = 'red'
TERM_COLOR_DEFAULT = 'default'
TERM_COLOR_RESET = 'reset'

TERM_COLORS = {
    '_c_blue': '\033[34m',
    '_c_green': '\033[32m',
    '_c_cyan': '\033[36m',
    '_c_red': '\033[31m',
    '_c_magenta': '\033[35m',
    '_c_gray': '\033[37m',
    '_c_yellow': '\033[33m',
    '_c_dark_gray': '\033[90m',
    '_c_light_yellow': '\033[93m',
    '_c_light_blue': '\033[94m',
    '_c_light_green': '\033[92m',
    '_c_light_cyan': '\033[96m',
    '_c_light_red': '\033[91m',
    '_c_light_magenta': '\033[95m',

    '_c_white': '\033[97m',
    '_c_black': '\033[30m',
    '_c_default': '\033[39m',
    '_c_reset': '\033[0m',
}
