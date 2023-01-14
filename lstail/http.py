# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from datetime import datetime
from json import loads
from time import sleep
from urllib.error import URLError
from urllib.request import (
    BaseHandler,
    build_opener,
    HTTPHandler,
    HTTPPasswordMgrWithDefaultRealm,
    HTTPSHandler,
    Request,
)
import base64
import ssl
import sys

from lstail.constants import HTTP_RETRYING_PAUSE, LOG_ENCODING, NON_RETRYING_STATUS_CODES, VERSION
from lstail.error import HttpRetryError
from lstail.util.debug import get_memory_usage


########################################################################
class PreemptiveBasicAuthHandler(BaseHandler):

    # ----------------------------------------------------------------------
    def __init__(self, password_mgr):
        self.passwd = password_mgr

    # ----------------------------------------------------------------------
    def http_request(self, req):
        uri = req.get_full_url()
        user, password = self.passwd.find_user_password(None, uri)
        if password is None:
            return req

        raw = f'{user}:{password}'
        raw_bytes = raw.encode('utf-8')
        auth = base64.b64encode(raw_bytes)
        auth = auth.decode()
        auth_header = f'Basic {auth}'
        auth_header = auth_header.strip()
        req.add_unredirected_header('Authorization', auth_header)
        return req

    https_request = http_request


########################################################################
class ElasticsearchRequestController:

    # ----------------------------------------------------------------------
    def __init__(self, servers, timeout, verify_ssl_certificates, debug, logger):
        self._servers = servers
        self._timeout = timeout
        self._verify_ssl_certificates = verify_ssl_certificates
        self._debug = debug
        self._logger = logger
        self._user_agent = None
        self._url_opener = None

    # ----------------------------------------------------------------------
    def request(self, path, data=None, http_method='GET'):
        self._setup_user_agent_if_necessary()
        self._setup_url_opener_if_necessary()

        if data:
            data = data.encode()
        # go for it
        while True:
            try:
                result = self._request_inner(path, data, http_method=http_method)
            except HttpRetryError:
                # wait a moment and advance to the next server in the list
                sleep(HTTP_RETRYING_PAUSE)
                self._servers.rotate(1)
            else:
                break  # stop the loop

        return result

    # ----------------------------------------------------------------------
    def _setup_user_agent_if_necessary(self):
        if self._user_agent is not None:
            return

        self._user_agent = f'lstail/{VERSION} Python/{sys.version[:3]}'

    # ----------------------------------------------------------------------
    def _setup_url_opener_if_necessary(self):
        if self._url_opener is not None:
            return

        kwargs = {}

        # disable SSL verification if requested
        if not self._verify_ssl_certificates:
            ssl_hosts = [server for server in self._servers if server.url.startswith('https')]
            if ssl_hosts:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                kwargs['context'] = context

        # setup URL openers - add pre-emptive basic authentication
        http_handler = HTTPHandler()
        https_handler = HTTPSHandler(**kwargs)
        password_manager = HTTPPasswordMgrWithDefaultRealm()
        auth_handlers = []
        # setup auth handler if we have any servers requiring authentication
        for server in self._servers:
            if server.username:
                password_manager.add_password(
                    None,
                    server.url,
                    server.username,
                    server.password)

        if password_manager.passwd:
            auth_handler = PreemptiveBasicAuthHandler(password_manager)
            auth_handlers.append(auth_handler)

        self._url_opener = build_opener(http_handler, https_handler, *auth_handlers)

    # ----------------------------------------------------------------------
    def _request_inner(self, path, data, content_type=None, http_method='GET'):
        # yes, we could use the Elasticsearch Python API here but our queries are so simple,
        # we can do it manually
        server = self._servers[0]  # pull the next server
        url = self._factor_url(server, path)

        request = self._factor_request(url, data, http_method)
        self._setup_request_headers(request, data, content_type, server)

        begin_date = datetime.now()
        try:
            response_raw = self._url_opener.open(request, timeout=self._timeout)
            response = self._parse_response(response_raw)
            response_raw.close()
            self._assert_response_not_timed_out(response)
        except URLError as exc:
            # log
            self._log_request_error(url, server, exc)
            # check if we should give up directly without retrying
            status_code = getattr(exc, 'code', None)
            if status_code in NON_RETRYING_STATUS_CODES:
                raise  # propagate the error to the caller if we don't retry
            # retry with next server from config for any other errors
            raise HttpRetryError() from exc
        finally:
            call_duration = self._calculate_call_duration(begin_date)
            http_method = 'POST' if data else http_method
            memory_usage = f' - {get_memory_usage():0.2f} MB' if self._debug else ''
            self._logger.debug(
                'Querying server "{}" took {:0.3f} seconds ({} {}){memory_usage}',
                server.name,
                call_duration,
                http_method,
                path,
                memory_usage=memory_usage)

        return response

    # ----------------------------------------------------------------------
    def _factor_url(self, server, path):
        base_url = server.url
        base_url = base_url.rstrip('/')  # cut trailing slashes
        path = path.lstrip('/')  # cut leading slashes
        return f'{base_url}/{path}'

    # ----------------------------------------------------------------------
    def _factor_request(self, url, data, http_method):
        if http_method == 'HEAD' and data:
            raise ValueError('HTTP method "HEAD" with body is not supported!')

        if http_method == 'GET' and data:
            http_method = 'POST'  # override method if data is given

        return Request(url, data, method=http_method)

    # ----------------------------------------------------------------------
    def _setup_request_headers(self, request, data, content_type, server):
        request.add_header('User-agent', self._user_agent)
        # ES 6 requires Content-Type header for requests with body
        if data or content_type is not None:
            content_type_value = content_type if content_type is not None else 'application/json'
            request.add_header('Content-Type', content_type_value)
        # add further headers from config
        for name, value in server.headers:
            request.add_header(name, value)

    # ----------------------------------------------------------------------
    def _parse_response(self, response_raw, decode_as_json=True):
        result_encoded = response_raw.read()
        if result_encoded and hasattr(result_encoded, 'decode'):
            encoding = self._get_encoding_from_response(response_raw)
            result = result_encoded.decode(encoding)
        else:
            result = result_encoded

        if decode_as_json and result:
            return loads(result)

        return result

    # ----------------------------------------------------------------------
    def _get_encoding_from_response(self, response):
        headers = response.headers
        encoding = headers.get_charset()
        if not encoding:
            encoding = headers.get_content_charset()
        if not encoding:
            encoding = LOG_ENCODING

        return encoding

    # ----------------------------------------------------------------------
    def _assert_response_not_timed_out(self, response):
        if isinstance(response, dict) and response.get('timed_out', False):
            server = self._servers[0]
            self._logger.warning(
                f'Server "{server.name}" failed: timeout, trying next server')
            raise HttpRetryError()

    # ----------------------------------------------------------------------
    def _log_request_error(self, url, server, exc):
        self._logger.warning(f'Server "{server.name}" failed: {exc}, trying next server')
        # check for HTTPError and read body
        if hasattr(exc, 'read'):  # probably a HTTPError containing a response body to read
            response = self._parse_response(exc, decode_as_json=False)
            if response:
                self._logger.debug(
                    'Detailed server response for above error for URL "{}": {}',
                    url,
                    response)

    # ----------------------------------------------------------------------
    def _calculate_call_duration(self, begin_date):
        now = datetime.now()
        duration = now - begin_date
        duration_in_seconds = \
            float(duration.days) * 86400 + duration.seconds + float(duration.microseconds) / 1000000
        return duration_in_seconds
