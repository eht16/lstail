# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from datetime import datetime, timedelta

from ddt import data, ddt, unpack
from freezegun import freeze_time

from lstail.error import InvalidTimeRangeFormatError
from lstail.util.timestamp import parse_and_convert_time_range_to_start_date_time
from tests.base import BaseTestCase


TEST_DATETIME = datetime(2018, 2, 15, 10, 10, 0)

TEST_DATA_POSITIVE = (
    ('180', 180),
    ('3m', 180),

    ('2d', 172800),
    ('48h', 172800),
    ('2880m', 172800),
    ('172800', 172800),

    ('347d', 29980800),
    ('8328h', 29980800),
    ('499680m', 29980800),
    ('29980800', 29980800),

    (300, 300),
    (300.0, 300),

    (0, 0),
)


@ddt
class ParseTimeRangeTest(BaseTestCase):

    # ----------------------------------------------------------------------
    @data(*TEST_DATA_POSITIVE)
    @unpack
    def test_parse_time_range_positive(self, test_time_range, expected_time_range_seconds):
        with freeze_time(TEST_DATETIME):
            result = parse_and_convert_time_range_to_start_date_time(test_time_range)

        expected_datetime = TEST_DATETIME - timedelta(seconds=expected_time_range_seconds)
        self.assertEqual(result, expected_datetime)

    # ----------------------------------------------------------------------
    def test_parse_time_range_negative(self):

        # None
        with self.assertRaises(InvalidTimeRangeFormatError):
            parse_and_convert_time_range_to_start_date_time(None)

        # empty string
        with self.assertRaises(InvalidTimeRangeFormatError):
            parse_and_convert_time_range_to_start_date_time('')

        # unknown suffix
        with self.assertRaises(InvalidTimeRangeFormatError):
            parse_and_convert_time_range_to_start_date_time('55v')

        # negative range
        with self.assertRaises(InvalidTimeRangeFormatError):
            parse_and_convert_time_range_to_start_date_time(-55)
        with self.assertRaises(InvalidTimeRangeFormatError):
            parse_and_convert_time_range_to_start_date_time('-6d')

        # float range
        with self.assertRaises(InvalidTimeRangeFormatError):
            parse_and_convert_time_range_to_start_date_time('3.14')
