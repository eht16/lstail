# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from urllib.error import HTTPError

from ddt import data, ddt, unpack

from lstail.constants import (
    DEFAULT_ELASTICSEARCH_MAJOR_VERSION,
    ELASTICSEARCH_MAJOR_VERSION_2,
    ELASTICSEARCH_MAJOR_VERSION_6,
    ELASTICSEARCH_MAJOR_VERSION_7,
)
from lstail.util.http import detect_elasticsearch_version
from tests.base import BaseTestCase, mock


TEST_ELASTICSEARCH_VERSIONS = (
    (ELASTICSEARCH_MAJOR_VERSION_7, 'elasticsearch_cluster_state_es7'),
    (ELASTICSEARCH_MAJOR_VERSION_6, 'elasticsearch_cluster_state_es6'),
    (ELASTICSEARCH_MAJOR_VERSION_2, 'elasticsearch_cluster_state_es2'),
)


@ddt
class DetectElasticSearchVersionTest(BaseTestCase):

    # ----------------------------------------------------------------------
    @data(*TEST_ELASTICSEARCH_VERSIONS)
    @unpack
    def test_detect_elasticsearch_version(self, es_major_version, test_data):
        test_data = self._get_test_data(test_data)

        http_handler = mock.MagicMock()
        http_handler.request.return_value = test_data

        es_major_version = detect_elasticsearch_version(http_handler, self._mocked_logger)

        self.assertEqual(es_major_version, es_major_version)

    # ----------------------------------------------------------------------
    def test_detect_elasticsearch_version_negative_http_error(self):
        http_handler = mock.MagicMock()
        http_handler.request.side_effect = HTTPError(
            url=None, code='666', msg='Faked test case error', hdrs=None, fp=None)

        es_major_version = detect_elasticsearch_version(http_handler, self._mocked_logger)

        self.assertEqual(es_major_version, DEFAULT_ELASTICSEARCH_MAJOR_VERSION)
        # expect a log entry
        self._mocked_logger.info.assert_called_once()
        self._mocked_logger.reset_mock()

    # ----------------------------------------------------------------------
    def test_detect_elasticsearch_version_negative_invalid_data_string(self):
        http_handler = mock.MagicMock()
        # string input
        http_handler.request.return_value = 'invalid cluster state, json expected'
        es_major_version = detect_elasticsearch_version(http_handler, self._mocked_logger)
        self.assertEqual(es_major_version, DEFAULT_ELASTICSEARCH_MAJOR_VERSION)
        self._mocked_logger.info.assert_called_once()  # expect a log entry
        self._mocked_logger.reset_mock()

    # ----------------------------------------------------------------------
    def test_detect_elasticsearch_version_negative_invalid_data_list(self):
        http_handler = mock.MagicMock()
        # list input
        http_handler.request.return_value = ['invalid cluster state, json expected']
        es_major_version = detect_elasticsearch_version(http_handler, self._mocked_logger)
        self.assertEqual(es_major_version, DEFAULT_ELASTICSEARCH_MAJOR_VERSION)
        self._mocked_logger.info.assert_called_once()  # expect a log entry
        self._mocked_logger.reset_mock()

    # ----------------------------------------------------------------------
    def test_detect_elasticsearch_version_negative_invalid_data_no_version(self):
        http_handler = mock.MagicMock()
        # unexpected JSON input - empty version
        http_handler.request.return_value = dict(version=dict())
        es_major_version = detect_elasticsearch_version(http_handler, self._mocked_logger)
        self.assertEqual(es_major_version, DEFAULT_ELASTICSEARCH_MAJOR_VERSION)
        self._mocked_logger.info.assert_called_once()  # expect a log entry
        self._mocked_logger.reset_mock()

    # ----------------------------------------------------------------------
    def test_detect_elasticsearch_version_negative_invalid_data_wrong_version(self):
        http_handler = mock.MagicMock()
        # unexpected JSON input - wrong version (ES 3 has never been existed)
        http_handler.request.return_value = dict(version=dict(number='3.1.2'))
        es_major_version = detect_elasticsearch_version(http_handler, self._mocked_logger)
        self.assertEqual(es_major_version, DEFAULT_ELASTICSEARCH_MAJOR_VERSION)
        self._mocked_logger.reset_mock()
