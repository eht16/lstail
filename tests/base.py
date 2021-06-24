# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from json import load
import logging
import unittest

from prompt_toolkit.completion import Completion

from lstail.dto.column import Column
from lstail.dto.server import Server


# mock imported here for use by other tests
try:
    from unittest import mock  # noqa pylint: disable=unused-import
except ImportError:
    import mock  # noqa pylint: disable=unused-import


class BaseTestCase(unittest.TestCase):

    # ----------------------------------------------------------------------
    def setUp(self):
        super().setUp()

        # compare Column objects
        self.addTypeEqualityFunc(Column, self._compare_column_object)

        # compare Server objects
        self.addTypeEqualityFunc(Server, self._compare_server_object)

        # compare prompt_toolkit.completion.Completion objects
        self.addTypeEqualityFunc(Completion, self._compare_completion_object)

        # provide a mocked logger for easy use
        self._mocked_logger = mock.MagicMock(spec=logging)

    # ----------------------------------------------------------------------
    def _compare_column_object(self, first, second, msg=None):
        self.assertEqual(first.names, second.names, msg=msg)
        self.assertEqual(first.color, second.color, msg=msg)
        self.assertEqual(first.display, second.display, msg=msg)
        self.assertEqual(first.padding, second.padding, msg=msg)

    # ----------------------------------------------------------------------
    def _compare_server_object(self, first, second, msg=None):
        self.assertEqual(first.name, second.name, msg=msg)
        self.assertEqual(first.url, second.url, msg=msg)
        self.assertEqual(first.username, second.username, msg=msg)
        self.assertEqual(first.password, second.password, msg=msg)
        self.assertEqual(first.headers, second.headers, msg=msg)

    # ----------------------------------------------------------------------
    def _compare_completion_object(self, first, second, msg=None):
        self.assertIsInstance(first, Completion, msg=msg)
        self.assertIsInstance(second, Completion, msg=msg)

        self.assertEqual(first.text, second.text, msg=msg)
        self.assertEqual(first.start_position, second.start_position, msg=msg)
        self.assertEqual(first.display_text, second.display_text, msg=msg)
        self.assertEqual(first.display_meta_text, second.display_meta_text, msg=msg)

    # ----------------------------------------------------------------------
    def _get_test_data(self, name):
        filename = 'tests/test_data/{}.json'.format(name)
        with open(filename) as responses_f:
            return load(responses_f)
