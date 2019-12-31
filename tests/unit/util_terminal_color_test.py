# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

import os

from ddt import data, ddt, unpack

from lstail.util.color import detect_terminal_color_support
from tests.base import BaseTestCase, mock


TEST_VARIATIONS = (
    # isatty, ANSI_COLORS_DISABLED, force, expected result
    (True, None, None, True),  # isatty True, ANSI_COLORS_DISABLED unset, should be True
    (False, None, None, False),  # isatty False, ANSI_COLORS_DISABLED unset, should be False

    (True, False, None, True),  # isatty True, ANSI_COLORS_DISABLED False, should be True
    (False, False, None, False),  # isatty False, ANSI_COLORS_DISABLED False, should be False

    (True, True, None, False),  # isatty True, ANSI_COLORS_DISABLED True, should be False
    (False, True, None, False),  # isatty False, ANSI_COLORS_DISABLED True, should be False

    # force=False
    (True, None, False, False),  # isatty True, ANSI_COLORS_DISABLED unset, forced, should be False
    (False, None, False, False),  # isatty False, ANSI_COLORS_DISABLED unset, forced,should be False

    (True, False, False, False),  # isatty True, ANSI_COLORS_DISABLED False, forced, should be False
    (False, False, False, False),  # isatty False, ANSI_COLORS_DISABLED False,forced,should be False

    (True, True, False, False),  # isatty True, ANSI_COLORS_DISABLED True, forced, should be False
    (False, True, False, False),  # isatty False, ANSI_COLORS_DISABLED True, forced, should be False

    # force=True
    (True, None, True, True),  # isatty True, ANSI_COLORS_DISABLED unset, forced, should be True
    (False, None, True, True),  # isatty False, ANSI_COLORS_DISABLED unset, forced, should be True

    (True, False, True, True),  # isatty True, ANSI_COLORS_DISABLED False, forced, should be True
    (False, False, True, True),  # isatty False, ANSI_COLORS_DISABLED False, forced, should be True

    (True, True, True, True),  # isatty True, ANSI_COLORS_DISABLED True, forced, should be True
    (False, True, True, True),  # isatty False, ANSI_COLORS_DISABLED True, forced, should be True
)


@ddt
class ColumnColorKeyTest(BaseTestCase):

    # ----------------------------------------------------------------------
    @data(*TEST_VARIATIONS)
    @unpack
    def test_terminal_color_detection(self, isatty, ansi_colors_disabled, force, expected_result):

        def fake_getenv(_):
            if ansi_colors_disabled is None:
                return None
            elif ansi_colors_disabled is False:  # pylint: disable=compare-to-zero
                return ''
            return ansi_colors_disabled

        mock_output = mock.Mock()
        mock_output.isatty.return_value = isatty
        with mock.patch.object(os, 'getenv', new=fake_getenv):
            # test
            result = detect_terminal_color_support(output=mock_output, force=force)
            # check
            if expected_result or force:
                self.assertTrue(result)
            else:
                self.assertFalse(result)

    # ----------------------------------------------------------------------
    def test_terminal_color_detection_with_non_file_object(self):
        # use something as output which does not support the isatty() method, in this case
        # the result should False
        mock_output = object()
        with mock.patch.object(os, 'getenv') as fake_env:
            fake_env.return_value = None
            # test
            result = detect_terminal_color_support(output=mock_output, force=None)
            # check
            self.assertFalse(result)
