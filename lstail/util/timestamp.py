# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from datetime import datetime, timedelta

from lstail.constants import ELASTICSEARCH_TIMESTAMP_FORMATS
from lstail.error import InvalidTimeRangeFormatError, InvalidTimestampFormatError


# ----------------------------------------------------------------------
def parse_and_convert_time_range_to_start_date_time(time_range):
    error_message = f'Invalid time range specified: {time_range}. ' \
        'Valid examples are: 60, 5m, 12h, 7d'

    try:
        # try to parse the time range as integer, interpret the value as seconds
        seconds = value = int(time_range)
    except TypeError as exc_type:
        raise InvalidTimeRangeFormatError(error_message) from exc_type
    except ValueError as exc_value:
        try:
            suffix = time_range[-1]
            value = int(time_range[:-1])
        except (ValueError, IndexError):
            raise InvalidTimeRangeFormatError(error_message) from exc_value
        if suffix == 'd':
            seconds = value * 86400
        elif suffix == 'h':
            seconds = value * 3600
        elif suffix == 'm':
            seconds = value * 60
        else:
            raise InvalidTimeRangeFormatError(error_message) from exc_value

    if value < 0:
        raise InvalidTimeRangeFormatError(error_message)

    return datetime.now() - timedelta(seconds=seconds)


# ----------------------------------------------------------------------
def parse_timestamp_from_elasticsearch(timestamp):
    for format_ in ELASTICSEARCH_TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(timestamp, format_)
        except ValueError:
            continue

    # we didn't find any matching format, so cry
    raise InvalidTimestampFormatError(timestamp)
