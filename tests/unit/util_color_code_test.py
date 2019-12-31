# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from ddt import data, ddt, unpack

from lstail.util.color import get_column_color_key
from tests.base import BaseTestCase


TEST_DATA_POSITIVE = (
    ('blue', '_c_blue'),
    ('green', '_c_green'),
    ('cyan', '_c_cyan'),
    ('red', '_c_red'),
    ('magenta', '_c_magenta'),
    ('gray', '_c_gray'),
    ('yellow', '_c_yellow'),
    ('dark_gray', '_c_dark_gray'),
    ('light_yellow', '_c_light_yellow'),
    ('light_blue', '_c_light_blue'),
    ('light_green', '_c_light_green'),
    ('light_cyan', '_c_light_cyan'),
    ('light_red', '_c_light_red'),
    ('light_magenta', '_c_light_magenta'),

    ('white', '_c_white'),
    ('black', '_c_black'),
    ('default', '_c_default'),
    ('reset', '_c_reset'),
)


@ddt
class ColumnColorKeyTest(BaseTestCase):

    # ----------------------------------------------------------------------
    def test_color_name_none(self):
        result = get_column_color_key(None)
        self.assertEqual(result, '_c_default')

    # ----------------------------------------------------------------------
    def test_color_name_empty_string(self):
        result = get_column_color_key('')
        self.assertEqual(result, '_c_default')

    # ----------------------------------------------------------------------
    @data(*TEST_DATA_POSITIVE)
    @unpack
    def test_positive(self, color_name, expected_color_key):
        result = get_column_color_key(color_name)
        self.assertEqual(result, expected_color_key)

    # ----------------------------------------------------------------------
    def test_negative(self):
        with self.assertRaises(KeyError):
            get_column_color_key('non-existent-color-name')
