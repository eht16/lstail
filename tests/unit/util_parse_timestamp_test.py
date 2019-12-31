# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from datetime import datetime

from ddt import data, ddt, unpack

from lstail.error import InvalidTimestampFormatError
from lstail.util.timestamp import parse_timestamp_from_elasticsearch
from tests.base import BaseTestCase


TEST_DATA_POSITIVE = (
    # format %Y-%m-%dT%H:%M:%S.%fZ
    ('2018-01-01T01:02:03.0Z', datetime(2018, 1, 1, 1, 2, 3, 0)),
    ('2018-01-01T01:02:03.123Z', datetime(2018, 1, 1, 1, 2, 3, 123000)),
    ('2018-03-31T23:42:17.123456Z', datetime(2018, 3, 31, 23, 42, 17, 123456)),
    ('2018-03-31t23:42:17.123456Z', datetime(2018, 3, 31, 23, 42, 17, 123456)),
    ('2018-03-31t23:42:17.123456z', datetime(2018, 3, 31, 23, 42, 17, 123456)),
    ('2018-03-31T23:42:17.123456z', datetime(2018, 3, 31, 23, 42, 17, 123456)),

    # format %Y-%m-%dT%H:%M:%S.%f
    ('2018-01-01T01:02:03.0', datetime(2018, 1, 1, 1, 2, 3, 0)),
    ('2018-01-01T01:02:03.123', datetime(2018, 1, 1, 1, 2, 3, 123000)),
    ('2018-03-31T23:42:17.123456', datetime(2018, 3, 31, 23, 42, 17, 123456)),
    ('2018-03-31t23:42:17.123456', datetime(2018, 3, 31, 23, 42, 17, 123456)),

    # format %Y-%m-%dT%H:%M:%S.%f+00:00
    ('2018-01-01T01:02:03.0+00:00', datetime(2018, 1, 1, 1, 2, 3, 0)),
    ('2018-01-01T01:02:03.123+00:00', datetime(2018, 1, 1, 1, 2, 3, 123000)),
    ('2018-03-31T23:42:17.123456+00:00', datetime(2018, 3, 31, 23, 42, 17, 123456)),
    ('2018-03-31t23:42:17.123456+00:00', datetime(2018, 3, 31, 23, 42, 17, 123456)),

    # format %Y-%m-%dT%H:%M:%S+00:00
    ('2018-01-01T01:02:03+00:00', datetime(2018, 1, 1, 1, 2, 3, 0)),
    ('2018-03-31T23:42:17+00:00', datetime(2018, 3, 31, 23, 42, 17, 0)),
    ('2018-03-31t23:42:17+00:00', datetime(2018, 3, 31, 23, 42, 17, 0)),
)


TEST_DATA_NEGATIVE = (
    # format %Y-%m-%dT%H:%M:%S.%fZ - invalid format
    '2018',
    '2018-01',
    '2018-01-',
    '2018-01-01',
    '2018-01-01T',
    '2018-01-01T01',
    '2018-01-01T01:02',
    '2018-01-01T01:02:03',
    '2018-01-01T01:02:03,123Z',
    '2018-01-01T01-02-03.123Z',
    '2016-02-29T01-02-03.123Z',

    # format %Y-%m-%dT%H:%M:%S.%f - invalid format
    '2018',
    '2018-01',
    '2018-01-',
    '2018-01-01',
    '2018-01-01T',
    '2018-01-01T01',
    '2018-01-01T01:02',
    '2018-01-01T01:02:03',
    '2018-01-01T01:02:03,123',
    '2018-01-01T01-02-03.123Z',

    # format %Y-%m-%dT%H:%M:%S+00:00 - invalid format
    '2018',
    '2018-01',
    '2018-01-',
    '2018-01-01',
    '2018-01-01T',
    '2018-01-01T01',
    '2018-01-01T01:02',
    '2018-01-01T01:02:03',
    '2018-01-01T01:02:03,123+00:00',
    '2018-01-01T01-02-03.123+00:00',

    # format %Y-%m-%dT%H:%M:%S.%fZ - valid format but invalid date/time data
    '2018-02-29T23:42:17.123456Z',  # 2018-02-29 didn't exist
    '2016-02-30T23:42:17.123456Z',  # 2016-02-29 did exist but not 2016-02-30
    '2018-04-31T23:42:17.123456Z',  # April 31st never exists
    # invalid time variants
    '2018-04-30T25:42:17.123456Z',
    '2018-04-30T24:42:17.123456Z',
    '2018-04-30T23:60:17.123456Z',
    '2018-04-30T23:61:17.123456Z',
    '2018-04-30T23:42:60.123456Z',
    '2018-04-30T23:42:61.123456Z',
)


@ddt
class ParseTimestampTest(BaseTestCase):

    # ----------------------------------------------------------------------
    @data(*TEST_DATA_POSITIVE)
    @unpack
    def test_positive(self, test_timestamp, expected_datetime):
        result = parse_timestamp_from_elasticsearch(test_timestamp)
        self.assertEqual(result, expected_datetime)

    # ----------------------------------------------------------------------
    @data(*TEST_DATA_NEGATIVE)
    def test_negative(self, test_timestamp):
        with self.assertRaises(InvalidTimestampFormatError):
            parse_timestamp_from_elasticsearch(test_timestamp)

    # ----------------------------------------------------------------------
    def test_empty_input(self):
        with self.assertRaises(TypeError):
            parse_timestamp_from_elasticsearch(None)

        with self.assertRaises(InvalidTimestampFormatError):
            parse_timestamp_from_elasticsearch('')
