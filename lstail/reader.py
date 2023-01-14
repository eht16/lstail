# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from datetime import datetime
from json import dumps
from os import environ
from time import sleep, tzset
from traceback import format_exc
import sys

from lstail.constants import ELASTICSEARCH_TIMESTAMP_FORMAT, VERSION
from lstail.error import StopReaderLoop
from lstail.http import ElasticsearchRequestController
from lstail.logger import LstailLogger
from lstail.prompt import KibanaSavedSearchSelectPrompt
from lstail.query.factory import QueryBuilderFactory
from lstail.query.kibana_saved_search import ListKibanaSavedSearchesController
from lstail.util.timestamp import (
    parse_and_convert_time_range_to_start_date_time,
    parse_timestamp_from_elasticsearch,
)


########################################################################
class LogstashReader:

    # ----------------------------------------------------------------------
    def __init__(self, config):
        self._config = config
        self._user_agent = None
        self._http_handler = None
        self._query_builder = None
        self._kibana_search = None
        self._base_query = None
        self._documents = None
        self._last_timestamp = None
        self._logger = None
        self._output = sys.stdout

    # ----------------------------------------------------------------------
    def show_version(self):
        print(f'Lstail {VERSION}', file=self._output)

    # ----------------------------------------------------------------------
    def list_kibana_saved_searches(self):
        self._setup_logger()
        self._setup_http_handler()

        saved_searches = self._get_kibana_saved_searches()
        if not saved_searches:
            print('No saved searches found in Kibana', file=self._output)
        else:
            for saved_search in saved_searches:
                print(f'{saved_search.title} ({saved_search.columns})', file=self._output)

    # ----------------------------------------------------------------------
    def _get_kibana_saved_searches(self):
        controller = ListKibanaSavedSearchesController(
            self._config,
            self._http_handler,
            self._logger)
        return controller.list()

    # ----------------------------------------------------------------------
    def read(self):
        self._setup_logger()
        self._setup_http_handler()
        self._setup_timezone()
        self._setup_initial_time_range()
        self._prompt_for_kibana_saved_search_selection_if_necessary()
        self._factor_query_builder()
        self._build_base_query()
        self._print_header()

        while True:
            try:
                self._fetch_latest_documents()
                self._fetch_latest_timestamp()
                self._print_latest_documents()
                self._stop_reader_loop_if_necessary()
                self._wait_for_next_refresh_interval()
            except (StopReaderLoop, KeyboardInterrupt):
                return
            except Exception as exc:  # pylint: disable=broad-except
                if self._config.debug:
                    traceback = format_exc()
                    traceback = f'\n{traceback}'
                else:
                    traceback = ''
                self._logger.error('Unexpected error occurred: {}{}', exc, traceback)
                self._wait_for_next_refresh_interval()

    # ----------------------------------------------------------------------
    def _setup_logger(self):
        self._logger = LstailLogger(
            config=self._config,
            output=self._output,
            verbose=self._config.verbose)

    # ----------------------------------------------------------------------
    def _setup_http_handler(self):
        self._http_handler = ElasticsearchRequestController(
            self._config.servers,
            timeout=self._config.timeout,
            verify_ssl_certificates=self._config.verify_ssl_certificates,
            debug=self._config.debug,
            logger=self._logger)

    # ----------------------------------------------------------------------
    def _setup_timezone(self):
        environ['TZ'] = 'UTC'
        tzset()

    # ----------------------------------------------------------------------
    def _setup_initial_time_range(self):
        if not self._config.initial_time_range:
            self._config.initial_time_range = '1d'  # fallback to one day

        self._last_timestamp = parse_and_convert_time_range_to_start_date_time(
            self._config.initial_time_range)

    # ----------------------------------------------------------------------
    def _prompt_for_kibana_saved_search_selection_if_necessary(self):
        if self._config.kibana.saved_search == '-' or self._config.select_kibana_saved_search:
            self._prompt_for_kibana_saved_search_selection()

    # ----------------------------------------------------------------------
    def _prompt_for_kibana_saved_search_selection(self):
        saved_searches = self._get_kibana_saved_searches()

        kibana_saved_search_select_prompt = KibanaSavedSearchSelectPrompt(saved_searches)
        selected_saved_search = kibana_saved_search_select_prompt.prompt()
        # overwrite previously set saved search title
        self._config.kibana.saved_search = selected_saved_search

    # ----------------------------------------------------------------------
    def _factor_query_builder(self):
        query_builder_factory = QueryBuilderFactory(self._http_handler, self._logger)
        self._query_builder = query_builder_factory.factor(
            self._config.default_index,
            self._config.kibana.index_name,
            self._config.kibana.saved_search,
            self._config.kibana.custom_search,
            self._http_handler,
            self._logger)

    # ----------------------------------------------------------------------
    def _build_base_query(self):
        self._base_query = self._query_builder.build()

    # ----------------------------------------------------------------------
    def _print_header(self):
        self._logger.print_header()

    # ----------------------------------------------------------------------
    def _fetch_latest_documents(self):
        path = f'{self._base_query.index}/_search'
        timestamp_from = self._last_timestamp.strftime(ELASTICSEARCH_TIMESTAMP_FORMAT)
        query = self._query_builder.build_query_for_time_range(self._base_query, timestamp_from)
        query.query['size'] = self._config.initial_query_size

        query_json = dumps(query.query)
        response = self._http_handler.request(path, query_json)
        self._documents = response['hits']['hits']
        self._documents.reverse()

    # ----------------------------------------------------------------------
    def _fetch_latest_timestamp(self):
        if self._documents:
            latest_document = self._documents[-1]
            timestamp = latest_document['_source'][self._base_query.time_field_name]
            last_timestamp = parse_timestamp_from_elasticsearch(timestamp)
            self._last_timestamp = min(last_timestamp, datetime.now())

    # ----------------------------------------------------------------------
    def _print_latest_documents(self):
        for document in self._documents:
            self._logger.log_document(document)

    # ----------------------------------------------------------------------
    def _stop_reader_loop_if_necessary(self):
        if not self._config.follow:
            # raise a dedicated exception to break the while(true) loop in self.read()
            # if "--follow" CLI option was not specified
            raise StopReaderLoop()

    # ----------------------------------------------------------------------
    def _wait_for_next_refresh_interval(self):
        sleep(self._config.refresh_interval)
