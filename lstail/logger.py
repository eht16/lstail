# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from collections import deque
from datetime import datetime
from io import StringIO
from operator import attrgetter
from socket import getfqdn
import csv
import logging
import sys
import traceback

from lstail.constants import (
    LSTAIL_DEFAULT_FIELD_DOCUMENT_ID,
    LSTAIL_DEFAULT_FIELD_MESSAGE,
    LSTAIL_DEFAULT_FIELD_TIMESTAMP,
    LSTAIL_FALLBACK_FIELD_VALUE,
    LSTAIL_INTERNAL_DOCUMENT_ID,
    PROGRAM_NAME,
    TERM_COLOR_DEFAULT,
    TERM_COLOR_ERROR,
    TERM_COLOR_RESET,
    TERM_COLOR_WARNING,
    TERM_COLORS,
)
from lstail.dto.column import Column
from lstail.error import ColumnNotFoundError, DocumentIdAlreadyProcessedError
from lstail.util.color import detect_terminal_color_support, factor_color_code
from lstail.util.formatter import AutoFillFormatter
from lstail.util.safe_munch import DefaultSafeMunch, safe_munchify
from lstail.util.timestamp import parse_timestamp_from_elasticsearch


########################################################################
class LstailLogger:

    _color_code_reset = factor_color_code(TERM_COLOR_RESET)

    # ----------------------------------------------------------------------
    def __init__(self, config, output, verbose=False):
        self._config = config
        self._verbose = verbose
        self._my_hostname = None
        self._processed_ids = None
        self._use_colors = None
        self._term_colors = None
        self._term_reset_string = None
        self._display_columns = None
        self._default_document_values = None
        self._internal_display_columns = None
        self._output = output

    # ----------------------------------------------------------------------
    def _init_if_necessary(self):
        if self._my_hostname is not None:
            return
        self._setup_hostname()
        self._setup_processed_ids_queue()
        self._setup_terminal_colors()
        self._update_internal_display_columns()
        self._factor_default_document_values()

    # ----------------------------------------------------------------------
    def _setup_hostname(self):
        self._my_hostname = getfqdn()

    # ----------------------------------------------------------------------
    def _setup_processed_ids_queue(self):
        # Remember the last 100 processed document IDs to check if we are to show already
        # processed ones. If the queue is full, just discard old items.
        self._processed_ids = deque(maxlen=100)

    # ----------------------------------------------------------------------
    def _setup_terminal_colors(self, force=None):
        self._use_colors = detect_terminal_color_support(self._output, force=force)

        self._term_colors = TERM_COLORS
        color_reset = self._term_colors['_c_reset']
        self._term_reset_string = f'{color_reset}\r'
        if not self._use_colors:
            # clear any color values
            for color_name in self._term_colors:
                self._term_colors[color_name] = ''
                self._term_reset_string = ''

    # ----------------------------------------------------------------------
    def _update_internal_display_columns(self):
        self._internal_display_columns = self._config.kibana.default_columns
        self._add_timestamp_column_if_necessary(self._internal_display_columns)
        self._add_document_id_column_if_necessary(self._internal_display_columns)

    # ----------------------------------------------------------------------
    def _add_timestamp_column_if_necessary(self, columns):
        if LSTAIL_DEFAULT_FIELD_TIMESTAMP not in columns:
            # hard-coded timestamp column as Kibana saved searches don't include it
            columns.insert(0, LSTAIL_DEFAULT_FIELD_TIMESTAMP)

    # ----------------------------------------------------------------------
    def _add_document_id_column_if_necessary(self, columns):
        # add "document_id" column in debug mode
        if self._config.debug and LSTAIL_DEFAULT_FIELD_DOCUMENT_ID not in columns:
            columns.insert(0, LSTAIL_DEFAULT_FIELD_DOCUMENT_ID)

    # ----------------------------------------------------------------------
    def _factor_default_document_values(self):
        default_doc_values = {}
        default_doc_values[LSTAIL_DEFAULT_FIELD_DOCUMENT_ID] = LSTAIL_DEFAULT_FIELD_DOCUMENT_ID
        default_doc_values[LSTAIL_DEFAULT_FIELD_TIMESTAMP] = LSTAIL_DEFAULT_FIELD_TIMESTAMP
        self._default_document_values = default_doc_values
        display_columns = self._get_display_columns_for_document(None)
        for column_name in display_columns:
            self._add_column_to_document_values(column_name)

    # ----------------------------------------------------------------------
    def _add_column_to_document_values(self, column_name):
        if '.' in column_name:  # nested column
            self._add_nested_column_to_document_values(column_name)
        else:
            self._default_document_values[column_name] = column_name

    # ----------------------------------------------------------------------
    def _add_nested_column_to_document_values(self, column_name):
        """
        Add the column to the document_values dictionary. If the column contains a nested
        field, map the nested structure into document_values as it is expected by _print_document().
        """
        column_name_elements = column_name.split('.')
        current_level_values = self._default_document_values
        for column_name_element in column_name_elements:
            if column_name_element not in current_level_values:
                if column_name_element == column_name_elements[-1]:
                    # it's the final element, just add it
                    current_level_values[column_name_element] = column_name
                else:
                    # we are in somewhere on the road and there are more nested levels to come,
                    # so add another level
                    current_level_values[column_name_element] = {}
            # dive one level deeper
            current_level_values = current_level_values[column_name_element]

    # ----------------------------------------------------------------------
    def update_display_columns(self, columns=None):
        if columns:
            self._display_columns = list(columns)  # copy column list as we modify it later
        else:
            self._display_columns = list(self._config.kibana.default_columns)

        self._add_timestamp_column_if_necessary(self._display_columns)
        self._add_document_id_column_if_necessary(self._display_columns)
        self._factor_default_document_values()

    # ----------------------------------------------------------------------
    def log(self, level, format_, *args, **kwargs):
        if level <= logging.DEBUG and not self._verbose:
            return  # quiet ourselves when not in verbose mode and level is DEBUG

        self._init_if_necessary()

        message = format_.format(*args, **kwargs)
        # handle exception information
        exc_info = kwargs.get('exc_info', None)
        if exc_info is not None:
            message = f'{message}{self._format_exception(exc_info)}'
        # fake Logstash document
        extra = kwargs.get('extra', None)
        document = self._factor_logstash_document(message, level, extra=extra)
        self._print_document(document)

    # ----------------------------------------------------------------------
    def _format_exception(self, exc_info):
        if isinstance(exc_info, BaseException):
            exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
        elif not isinstance(exc_info, tuple):
            exc_info = sys.exc_info()

        if exc_info[0] is None:
            return ''

        # from Python's logging.Formatter.formatException()
        text = StringIO()
        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], None, text)
        stack_trace = text.getvalue()
        text.close()
        if stack_trace[-1:] == "\n":
            stack_trace = stack_trace[:-1]
        return stack_trace

    # ----------------------------------------------------------------------
    def _factor_logstash_document(self, message, level, extra=None):
        source = {
            'level': logging.getLevelName(level),
            'host': self._my_hostname,
            'program': PROGRAM_NAME,
            LSTAIL_DEFAULT_FIELD_DOCUMENT_ID: LSTAIL_INTERNAL_DOCUMENT_ID,
            LSTAIL_DEFAULT_FIELD_TIMESTAMP: datetime.now(),
            LSTAIL_DEFAULT_FIELD_MESSAGE: message}
        if extra:
            source.update(**extra)

        document = dict(
            _source=source,
            internal=True)
        return document

    # ----------------------------------------------------------------------
    def log_document(self, document):
        self._init_if_necessary()

        try:
            self._print_document(document)
        except Exception as exc:  # pylint: disable=broad-except
            try:
                error_message = self._factor_error_message_from_exception(exc, document)
                error_document = self._factor_logstash_document(error_message, logging.ERROR)
                self._print_document(error_document)
            except Exception as fallback_exc:  # pylint: disable=broad-except
                # as a last resort, print directly
                message = self._factor_error_message_from_exception(fallback_exc, document)
                print(message, file=self._output)
                self._reset_terminal_color()

    # ----------------------------------------------------------------------
    def _factor_error_message_from_exception(self, exc, document):
        exc_type = exc.__class__.__name__
        message = repr(document)
        _c_red = self._term_colors['_c_red']
        return f'{_c_red}Unparseable document: {exc_type}: {exc}: {message}'

    # ----------------------------------------------------------------------
    def _get_document_values(self, document):
        source = dict(**document['_source'])

        values = dict(**source)
        # timestamp
        timestamp = self._get_timestamp_from_document(source)
        timestamp = self._parse_timestamp(timestamp)
        timestamp = self._format_timestamp(timestamp)
        values[LSTAIL_DEFAULT_FIELD_TIMESTAMP] = timestamp

        # document_id
        document_id = self._get_document_id_from_document(source, document)
        values[LSTAIL_DEFAULT_FIELD_DOCUMENT_ID] = document_id

        # message
        message = self._format_message(document) or source.get(LSTAIL_DEFAULT_FIELD_MESSAGE, None)
        values[LSTAIL_DEFAULT_FIELD_MESSAGE] = message

        return values

    # ----------------------------------------------------------------------
    def _get_timestamp_from_document(self, document_values):
        timestamp_column = self._config.display.columns[LSTAIL_DEFAULT_FIELD_TIMESTAMP]
        for column_name in timestamp_column.names:
            if column_name in document_values:
                return document_values[column_name]

        raise ColumnNotFoundError(LSTAIL_DEFAULT_FIELD_TIMESTAMP)

    # ----------------------------------------------------------------------
    def _get_document_id_from_document(self, document_values, document=None):
        # lookup in the root document for ES documents
        if document is not None and '_id' in document:
            return document['_id']

        # document_id column only exists in debug mode, so check first
        document_id_column = self._config.display.columns.get(LSTAIL_DEFAULT_FIELD_DOCUMENT_ID)
        if document_id_column is not None:
            for column_name in document_id_column.names:
                if column_name in document_values:
                    return document_values[column_name]

        # lookup the document_id directly from document_values as a last resort
        return document_values.get(LSTAIL_DEFAULT_FIELD_DOCUMENT_ID)

    # ----------------------------------------------------------------------
    def _format_message(self, document):
        if not self._use_colors:
            return None  # if we don't use colors, then here is nothing to do

        source = document['_source']
        # try to find a log level field
        log_level_column = self._config.display.columns.get('log_level', None)
        if log_level_column is None:
            return None

        for field_name in log_level_column.names:
            log_level = source.get(field_name, None)
            if log_level is not None:
                break
        else:
            return None  # bail out if we didn't find anything similar to a log level

        message = source.get(LSTAIL_DEFAULT_FIELD_MESSAGE, None)
        if message is None:
            return None

        color_code = self._factor_log_level_color_code(log_level)
        message = f'{self._term_colors[color_code]}{message}'
        return message

    # ----------------------------------------------------------------------
    def _factor_log_level_color_code(self, log_level):
        log_level_lower = log_level.lower()
        if log_level_lower in self._config.parser.log_level_names_warning:
            return factor_color_code(TERM_COLOR_WARNING)
        elif log_level_lower in self._config.parser.log_level_names_error:
            return factor_color_code(TERM_COLOR_ERROR)
        else:
            return factor_color_code(TERM_COLOR_RESET)

    # ----------------------------------------------------------------------
    def _parse_timestamp(self, timestamp):
        if isinstance(timestamp, datetime):
            return timestamp

        return parse_timestamp_from_elasticsearch(timestamp)

    # ----------------------------------------------------------------------
    def _format_timestamp(self, timestamp):
        return timestamp.strftime(self._config.format.timestamp)[:-3]

    # ----------------------------------------------------------------------
    def _reset_terminal_color(self):
        if self._use_colors:
            # reset term color
            print(self._term_reset_string, end='', file=self._output)

    # ----------------------------------------------------------------------
    def _print_document(self, document, document_values=None, force_color=None):
        document_values_initial = document_values or self._get_document_values(document)
        # sanity check for duplicate documents
        self._assert_document_already_processed(document_values_initial)

        # support attribute-style access to dict; necessary if the columns contains dots
        # (e.g. for nested documents) which are interpreted as attributes by format() below
        document_values = safe_munchify(
            document_values_initial,
            factory=DefaultSafeMunch,
            default=LSTAIL_FALLBACK_FIELD_VALUE)

        # output
        if self._config.csv_output and not self._is_internal_document(document_values_initial):
            self._print_document_as_csv(document, document_values)
        else:
            self._print_document_as_text(document, document_values, force_color)

    # ----------------------------------------------------------------------
    def _assert_document_already_processed(self, document_values):
        document_id = self._get_document_id_from_document(document_values)
        if document_id is not None:
            if self._is_internal_document(document_values):
                return  # ignore internal dummy id, it is expected to repeat
            if document_id in self._processed_ids:
                raise DocumentIdAlreadyProcessedError(document_id, document_values)

        self._processed_ids.append(document_id)

    # ----------------------------------------------------------------------
    def _is_internal_document(self, document_values):
        document_id = self._get_document_id_from_document(document_values)
        return bool(document_id == LSTAIL_INTERNAL_DOCUMENT_ID)

    # ----------------------------------------------------------------------
    def _print_document_as_csv(self, document, document_values):
        values = {}
        columns = self._get_display_columns_for_document(document)
        for column in columns:
            get_value_from_document = attrgetter(column)
            values[column] = get_value_from_document(document_values)

        writer = csv.DictWriter(self._output, fieldnames=columns, extrasaction='ignore')
        writer.writerow(values)

    # ----------------------------------------------------------------------
    def _print_document_as_text(self, document, document_values, force_color):
        # add color codes to document values
        document_values.sm_dict_update(self._term_colors)
        # factor column specs and build message format string
        column_specs = self._prepare_column_specs(document, document_values, force_color)

        # format message
        message_format = ' '.join(column_specs)
        formatted_message = self._auto_fill_format_message(message_format, document_values)
        # finally print the message
        print(formatted_message, file=self._output)
        self._reset_terminal_color()

    # ----------------------------------------------------------------------
    def _prepare_column_specs(self, document, document_values, force_color):
        message_format_parts = []
        display_columns = self._get_display_columns_for_document(document)

        for column_name in display_columns:
            column = self._get_column_by_name(column_name)
            # skip hidden columns
            if not column.display:
                continue

            column_name = self._update_column_name_from_document(
                column_name,
                column,
                document_values)
            column_color = self._get_column_color(column, force_color=force_color)
            column_padding = column.padding if column.padding else ''

            column_spec = self._factor_column_spec(column_name, column_color, column_padding)
            message_format_parts.append(column_spec)

        return message_format_parts

    # ----------------------------------------------------------------------
    def _get_display_columns_for_document(self, document):
        if document and document.get('internal', False):
            # for internal log messages, use the default column set from config
            return self._internal_display_columns

        if self._display_columns is None:
            # if for some reason we didn't get any specific column set, use the internal one
            return self._internal_display_columns

        return self._display_columns

    # ----------------------------------------------------------------------
    def _get_column_by_name(self, column_name):
        column = self._config.display.columns.get(column_name, None)
        if column:
            return column
        # fallback to searching for all column names:
        # if the column we need is not matched directly, try all configured column alias names
        # and take the first match, else return None to indicate there is no such column configured
        for column in self._config.display.columns.values():
            if column_name in column.names:
                return column

        # fallback to default column
        return self._factor_default_column(column_name)

    # ----------------------------------------------------------------------
    def _factor_default_column(self, name):
        color_code = factor_color_code(TERM_COLOR_DEFAULT)
        return Column(
            names=[name],
            color=color_code,
            display=True,
            padding=None)

    # ----------------------------------------------------------------------
    def _update_column_name_from_document(self, column_name, column, document_values):
        # try exact match of column_name in document_values,
        # fall back to alias column names if no match is found
        document_values_keys_flattened = document_values.sm_dict_keys_flattened(separator='.')
        if column_name in document_values_keys_flattened:
            return column_name

        # match column_name against the name in the log event, i.e. find the real column name
        # used in the received log event by the configured column name aliases
        for name in column.names:
            if name in document_values_keys_flattened:
                return name

        # if we are here, we didn't find an appropriate column in the configuration, so
        # set it to empty (or to the column name for debugging)
        if self._config.debug:
            document_values[column_name] = f'<{column_name}>'
        else:
            document_values[column_name] = ''

        return column_name

    # ----------------------------------------------------------------------
    def _get_column_color(self, column, force_color=None):
        if self._use_colors:
            if force_color:
                return force_color
            if column.color:
                return column.color

        return self._color_code_reset  # default fallback

    # ----------------------------------------------------------------------
    def _factor_column_spec(self, column_name, color_code, column_padding):
        return f'{{{color_code}}}{{{column_name}:{column_padding}}}{{{self._color_code_reset}}}'

    # ----------------------------------------------------------------------
    def _auto_fill_format_message(self, message_format, document_values):
        formatter = AutoFillFormatter(autofill=LSTAIL_FALLBACK_FIELD_VALUE)
        formatted_message = formatter.vformat(
            format_string=message_format,
            args=(),
            kwargs=document_values)
        return formatted_message

    # ----------------------------------------------------------------------
    def print_header(self):
        if self._config.no_header:
            return

        self._init_if_necessary()

        self._print_document(
            document=None,
            document_values=self._default_document_values,
            force_color=self._config.header_color)

    # ----------------------------------------------------------------------
    def debug(self, msg, *args, **kwargs):
        self.log(logging.DEBUG, msg, *args, **kwargs)

    # ----------------------------------------------------------------------
    def info(self, msg, *args, **kwargs):
        self.log(logging.INFO, msg, *args, **kwargs)

    # ----------------------------------------------------------------------
    def warning(self, msg, *args, **kwargs):
        self.log(logging.WARNING, msg, *args, **kwargs)

    # ----------------------------------------------------------------------
    def error(self, msg, *args, **kwargs):
        self.log(logging.ERROR, msg, *args, **kwargs)

    # ----------------------------------------------------------------------
    def exception(self, msg, *args, exc_info=True, **kwargs):
        self.error(msg, *args, exc_info=exc_info, **kwargs)

    # ----------------------------------------------------------------------
    def critical(self, msg, *args, **kwargs):
        self.log(logging.CRITICAL, msg, *args, **kwargs)
