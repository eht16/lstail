# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from collections import deque
from datetime import datetime
from http.client import HTTPResponse
from urllib.error import URLError

from freezegun import freeze_time

from lstail.dto.server import Server
from lstail.error import HttpRetryError
from lstail.http import ElasticsearchRequestController
from tests.base import BaseTestCase, mock


# pylint: disable=protected-access

TEST_SERVER_1 = Server()
TEST_SERVER_1.name = 'server1'
TEST_SERVER_1.url = 'http://127.0.0.1:9200'
TEST_SERVER_1.username = 'dummy-user'
TEST_SERVER_1.password = 'secret'
TEST_SERVER_1.headers = [('key1_1', 'value1_1'), ('key1_2', 'value1_2')]
TEST_SERVER_2 = Server()
TEST_SERVER_2.name = 'server2'
TEST_SERVER_2.url = 'http://127.0.0.2:9200'
TEST_SERVER_2.username = None
TEST_SERVER_2.password = None
TEST_SERVER_2.headers = [('key2', 'value2')]
TEST_SERVERS = [TEST_SERVER_1, TEST_SERVER_2]
TEST_TIMEOUT = 1.0


class HttpTest(BaseTestCase):

    # ----------------------------------------------------------------------
    def test_setup_request_headers_type(self):

        def mocked_add_header(key, value):
            headers[key] = value

        http_client = ElasticsearchRequestController(None, None, None, None)
        http_client._user_agent = 'Dummy User-Agent for testing'

        # simple GET request
        request = mock.Mock()
        request.add_header = mocked_add_header
        data = None
        content_type = None
        server = TEST_SERVER_1
        headers = dict()

        http_client._setup_request_headers(request, data, content_type, server)
        expected_headers = {
            'User-agent': 'Dummy User-Agent for testing',
            'key1_1': 'value1_1',
            'key1_2': 'value1_2',
        }
        self.assertEqual(headers, expected_headers)

        # simple GET request with content-type
        request = mock.Mock()
        request.add_header = mocked_add_header
        data = None
        content_type = 'text/css'
        server = TEST_SERVER_1
        headers = dict()

        http_client._setup_request_headers(request, data, content_type, server)
        expected_headers = {
            'User-agent': 'Dummy User-Agent for testing',
            'key1_1': 'value1_1',
            'key1_2': 'value1_2',
            'Content-Type': 'text/css',
        }
        self.assertEqual(headers, expected_headers)

        # request with data and content-type
        request = mock.Mock()
        request.add_header = mocked_add_header
        data = 'dummy data'
        content_type = 'text/css'
        server = TEST_SERVER_1
        headers = dict()

        http_client._setup_request_headers(request, data, content_type, server)
        expected_headers = {
            'User-agent': 'Dummy User-Agent for testing',
            'key1_1': 'value1_1',
            'key1_2': 'value1_2',
            'Content-Type': 'text/css',
        }
        self.assertEqual(headers, expected_headers)

        # request with data, without content-type
        request = mock.Mock()
        request.add_header = mocked_add_header
        data = 'dummy data'
        content_type = None
        server = TEST_SERVER_1
        headers = dict()

        http_client._setup_request_headers(request, data, content_type, server)
        expected_headers = {
            'User-agent': 'Dummy User-Agent for testing',
            'key1_1': 'value1_1',
            'key1_2': 'value1_2',
            'Content-Type': 'application/json',
        }
        self.assertEqual(headers, expected_headers)

    # ----------------------------------------------------------------------
    def test_parse_response(self):
        http_client = ElasticsearchRequestController(None, None, None, None)

        # simple text
        response_bytes_raw = mock.Mock()
        response_bytes_raw.read.return_value = b'test'
        # disable charset in response to force use of lstail.http.LOG_ENCODING
        response_bytes_raw.headers.get_charset.return_value = None
        response_bytes_raw.headers.get_content_charset.return_value = None
        decode_as_json = False
        result = http_client._parse_response(response_bytes_raw, decode_as_json)
        self.assertEqual(result, 'test')

        response_raw = mock.Mock()
        response_raw.headers.get_charset.return_value = None
        response_raw.headers.get_content_charset.return_value = None
        # None response
        with mock.patch('lstail.http.LOG_ENCODING', 'utf-8'):
            response_raw.read.return_value = None
            decode_as_json = True
            result = http_client._parse_response(response_raw, decode_as_json)
            self.assertEqual(result, None)

        # empty string response
        with mock.patch('lstail.http.LOG_ENCODING', 'utf-8'):
            response_raw.read.return_value = ''
            decode_as_json = True
            result = http_client._parse_response(response_raw, decode_as_json)
            self.assertEqual(result, '')

        # JSON, ISO encoding
        with mock.patch('lstail.http.LOG_ENCODING', 'iso-8859-15'):
            response_raw.read.return_value = '{ "foo": "bär" }'.encode('iso-8859-15')
            decode_as_json = True
            result = http_client._parse_response(response_raw, decode_as_json)
            self.assertEqual(result, dict(foo='bär'))

    # ----------------------------------------------------------------------
    def test_get_encoding_from_response(self):
        http_client = ElasticsearchRequestController(None, None, None, None)

        response_raw = mock.Mock()
        # headers.get_charset() returns something, so we expect something
        response_raw.headers.get_charset.return_value = 'foo-enc'
        result = http_client._get_encoding_from_response(response_raw)
        self.assertEqual(result, 'foo-enc')

        # headers.get_charset() returns None, so we fall back to headers.get_content_charset()
        response_raw.headers.get_charset.return_value = None
        response_raw.headers.get_content_charset.return_value = 'foo-content-enc'
        result = http_client._get_encoding_from_response(response_raw)
        self.assertEqual(result, 'foo-content-enc')

        # headers.get_charset() returns None and headers.get_content_charset() returns None,
        # so we expect LOG_ENCODING as fallback
        with mock.patch('lstail.http.LOG_ENCODING', 'some-fallback-enc'):
            response_raw.headers.get_charset.return_value = None
            response_raw.headers.get_content_charset.return_value = None
            result = http_client._get_encoding_from_response(response_raw)
            self.assertEqual(result, 'some-fallback-enc')

        # headers.get_charset() returns something and headers.get_content_charset() returns
        # something else so we expect something
        response_raw.headers.get_charset.return_value = 'some-enc'
        response_raw.headers.get_content_charset.return_value = 'some-content-enc'
        result = http_client._get_encoding_from_response(response_raw)
        self.assertEqual(result, 'some-enc')

        # headers.get_charset() returns None and headers.get_content_charset() returns
        # something so we expect something but not LOG_ENCODING
        with mock.patch('lstail.http.LOG_ENCODING', 'some-fallback-enc'):
            response_raw.headers.get_charset.return_value = None
            response_raw.headers.get_content_charset.return_value = 'some-content-enc'
            result = http_client._get_encoding_from_response(response_raw)
            self.assertEqual(result, 'some-content-enc')

    # ----------------------------------------------------------------------
    def test_request_http_error(self):
        test_servers = deque(TEST_SERVERS)
        http_client = ElasticsearchRequestController(
            test_servers, TEST_TIMEOUT, None, self._mocked_logger)

        # expect HttpRetryError on URLError
        with mock.patch.object(http_client, '_url_opener') as mock_url_opener:
            mock_url_opener.open.side_effect = URLError('test error')
            with self.assertRaises(HttpRetryError):
                http_client._request_inner('/', data=None)

        # expect real error on non-URLError
        with mock.patch.object(http_client, '_url_opener') as mock_url_opener2:
            mock_url_opener2.open.side_effect = KeyboardInterrupt('test error')
            with self.assertRaises(KeyboardInterrupt):
                http_client._request_inner('/', data=None)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.http.HTTP_RETRYING_PAUSE', 0.2)
    def test_request_http_error_retry(self):
        mocked_response = mock.MagicMock(status=200, spec=HTTPResponse)
        mocked_response.read.return_value = b'{ "foo": "bar" }'
        mocked_response.headers = mock.Mock()
        mocked_response.headers.get_charset.return_value = 'utf-8'
        # raise error on first call, then a valid response
        mock_side_effect = [URLError('test error'), mocked_response]

        test_servers = deque(TEST_SERVERS)
        http_client = ElasticsearchRequestController(
            test_servers, TEST_TIMEOUT, None, self._mocked_logger)
        # pre-flight check, basically cannot fail but won't hurt
        self.assertEqual(http_client._servers[0], TEST_SERVER_1)

        # test
        with mock.patch.object(http_client, '_url_opener') as mock_url_opener:
            mock_url_opener.open.side_effect = mock_side_effect
            result = http_client.request('/', data=None)

            # http_client._servers[0] is a deque and has been rotated after the first error,
            # so now we expect the second server item to be at the first index
            self.assertEqual(http_client._servers[0], TEST_SERVER_2)
            # the response should match in any way, so check it
            self.assertEqual(result, dict(foo='bar'))

    # ----------------------------------------------------------------------
    def test_valid_server_url(self):
        http_client = ElasticsearchRequestController(
            TEST_SERVERS, TEST_TIMEOUT,
            verify_ssl_certificates=True,
            logger=self._mocked_logger)

        # normal
        server = mock.Mock(url='http://127.0.0.1:9200')
        path = 'foo/bar'
        url = http_client._factor_url(server, path)
        self.assertEqual(url, 'http://127.0.0.1:9200/foo/bar')

        # trailing slashes on host
        for i in range(1, 5):
            server = mock.Mock(url='http://127.0.0.1:9200{}'.format('/' * i))
            path = 'foo/bar'
            url = http_client._factor_url(server, path)
            self.assertEqual(url, 'http://127.0.0.1:9200/foo/bar')

        # trailing slashes on host
        for i in range(1, 5):
            server = mock.Mock(url='http://127.0.0.1:9200')
            path = '{}foo/bar'.format('/' * i)
            url = http_client._factor_url(server, path)
            self.assertEqual(url, 'http://127.0.0.1:9200/foo/bar')

        # both
        for i in range(1, 5):
            server = mock.Mock(url='http://127.0.0.1:9200{}'.format('/' * i))
            path = '{}foo/bar'.format('/' * i)
            url = http_client._factor_url(server, path)
            self.assertEqual(url, 'http://127.0.0.1:9200/foo/bar')

    # ----------------------------------------------------------------------
    def test_factor_request(self):
        http_client = ElasticsearchRequestController(
            TEST_SERVERS, TEST_TIMEOUT,
            verify_ssl_certificates=True,
            logger=self._mocked_logger)

        # GET
        request = http_client._factor_request('http://127.0.0.1:9200/foo', None, 'GET')
        self.assertEqual(request.get_method(), 'GET')

        # POST (even if the argument says GET)
        request = http_client._factor_request('http://127.0.0.1:9200/foo', 'data', 'GET')
        self.assertEqual(request.get_method(), 'POST')

        # HEAD
        request = http_client._factor_request('http://127.0.0.1:9200/foo', None, 'HEAD')
        self.assertEqual(request.get_method(), 'HEAD')

        # HEAD with data => exception
        with self.assertRaises(ValueError):
            http_client._factor_request('http://127.0.0.1:9200/foo', 'data', 'HEAD')

    # ----------------------------------------------------------------------
    def test_assert_response_not_timed_out(self):
        http_client = ElasticsearchRequestController(
            TEST_SERVERS, TEST_TIMEOUT,
            verify_ssl_certificates=True,
            logger=self._mocked_logger)

        # simulate timeout
        self._mocked_logger.reset_mock()
        response = dict(timed_out=True)
        with self.assertRaises(HttpRetryError):
            http_client._assert_response_not_timed_out(response)
            self._mocked_logger.warning.assert_called_once()

        # response is not a dict
        response = None
        http_client._assert_response_not_timed_out(response)

        # response is dict but without timedout key
        response = dict(foo='bar')
        http_client._assert_response_not_timed_out(response)

    # ----------------------------------------------------------------------
    def test_log_request_error(self):
        http_client = ElasticsearchRequestController(
            TEST_SERVERS, TEST_TIMEOUT,
            verify_ssl_certificates=True,
            logger=self._mocked_logger)

        # simple exception
        self._mocked_logger.reset_mock()
        http_client._log_request_error('/foo', TEST_SERVER_1, ValueError('foobar exc'))
        expected_log_message = 'Server "{}" failed: {}, trying next server'.format(
            TEST_SERVER_1.name, 'foobar exc')
        self._mocked_logger.warning.assert_called_once_with(expected_log_message)

        # HTTPError exception
        self._mocked_logger.reset_mock()
        exc_text = 'foobar exc read'
        exc = mock.MagicMock()
        exc.__str__.return_value = exc_text
        exc.read.return_value = exc_text
        http_client._log_request_error('/foo', TEST_SERVER_1, exc)
        expected_log_message = 'Server "{}" failed: {}, trying next server'.format(
            TEST_SERVER_1.name, exc_text)
        self._mocked_logger.warning.assert_called_once_with(expected_log_message)
        self._mocked_logger.debug.assert_called_once()

    # ----------------------------------------------------------------------
    def test_calculate_call_duration(self):
        http_client = ElasticsearchRequestController(
            TEST_SERVERS, TEST_TIMEOUT,
            verify_ssl_certificates=True,
            logger=self._mocked_logger)

        begin_date_time = datetime(2018, 2, 22, 22, 22, 22)

        end_date_time = datetime(2018, 2, 22, 22, 22, 42)
        with freeze_time(end_date_time):
            duration = http_client._calculate_call_duration(begin_date_time)
            self.assertEqual(duration, 20)

        end_date_time = begin_date_time
        with freeze_time(end_date_time):
            duration = http_client._calculate_call_duration(begin_date_time)
            self.assertEqual(duration, 0)
