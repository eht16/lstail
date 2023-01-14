# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from prompt_toolkit.completion import CompleteEvent, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText, HTML

from lstail.constants import ELASTICSEARCH_MAJOR_VERSION_7
from lstail.dto.configuration import Configuration
from lstail.prompt import KibanaSavedSearchSelectPrompt
from lstail.query.kibana_saved_search import ListKibanaSavedSearchesController
from tests.base import BaseTestCase, mock


# pylint: disable=protected-access


TEST_CONFIG = Configuration()
TEST_CONFIG.debug = False
TEST_CONFIG.verbose = False
TEST_CONFIG.kibana = mock.Mock(index_name='mocked-index', default_columns=['dummy'])


class LogstashReaderTest(BaseTestCase):

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.kibana_saved_search.detect_elasticsearch_version')
    @mock.patch.object(KibanaSavedSearchSelectPrompt, '_factor_saved_search_completions')
    @mock.patch.object(KibanaSavedSearchSelectPrompt, '_factor_saved_search_completer')
    def test_prompt_without_saved_searches(
            self,
            mock_factor_completer,
            mock_factor_completions,
            mock_es_detection):
        # test data
        saved_searches = self._load_saved_searches(mock_es_detection, 'saved_searches_empty7')

        # test
        kibana_saved_search_select_prompt = KibanaSavedSearchSelectPrompt(saved_searches)
        result = kibana_saved_search_select_prompt.prompt()
        # check
        mock_factor_completions.assert_not_called()
        mock_factor_completer.assert_not_called()
        self.assertIsNone(result)

    # ----------------------------------------------------------------------
    def _load_saved_searches(self, mock_es_detection, test_data_name):
        test_response = self._get_test_data(test_data_name)
        mock_es_detection.return_value = ELASTICSEARCH_MAJOR_VERSION_7
        mock_handler = mock.MagicMock()
        mock_handler.request.return_value = test_response

        lister = ListKibanaSavedSearchesController(TEST_CONFIG, mock_handler, self._mocked_logger)
        return lister.list()

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.kibana_saved_search.detect_elasticsearch_version')
    def test_factor_saved_search_completions(self, mock_es_detection):
        # test data
        saved_searches = self._load_saved_searches(mock_es_detection, 'saved_searches_kibana7')
        # test
        kibana_saved_search_select_prompt = KibanaSavedSearchSelectPrompt(saved_searches)
        kibana_saved_search_select_prompt._factor_saved_search_completions()
        # check
        result = kibana_saved_search_select_prompt._saved_searches_completions
        expected_result = {
            '---': HTML(
                '<ansimagenta><i>Continue without any saved search</i></ansimagenta>'),
            'Parse Failures': HTML(
                'Columns: <ansiblue>tags, logsource, program, message</ansiblue>'),
            'Webserver': HTML(
                'Columns: <ansiblue>http_host, http_clientip, http_verb, '
                'message, http_code</ansiblue>'),
            'Webserver 404': HTML(
                'Columns: <ansiblue>http_clientip, http_verb, message, http_code</ansiblue>'),
        }

        # compare dict keys for equality
        self.assertEqual(result.keys(), expected_result.keys())
        # compare dict values
        for result_key, item in result.items():
            expected_item = expected_result[result_key]

            self.assertEqual(item.value, expected_item.value)
            self.assertEqual(item.formatted_text, expected_item.formatted_text)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.query.kibana_saved_search.detect_elasticsearch_version')
    def test_factor_saved_search_completer(self, mock_es_detection):
        # test data
        saved_searches = self._load_saved_searches(mock_es_detection, 'saved_searches_kibana7')

        kibana_saved_search_select_prompt = KibanaSavedSearchSelectPrompt(saved_searches)
        kibana_saved_search_select_prompt._factor_saved_search_completions()
        # test
        kibana_saved_search_select_prompt._factor_saved_search_completer()
        # check
        self.assertIsNotNone(kibana_saved_search_select_prompt._saved_searches_completer)
        completions_ = kibana_saved_search_select_prompt._saved_searches_completer.get_completions(
            Document(""),
            CompleteEvent())
        completions = list(completions_)

        expected_completions = [
            Completion(
                text='---',
                start_position=0,
                display=FormattedText([('', '---')]),
                display_meta=HTML(
                    '<ansimagenta><i>Continue without any saved search</i></ansimagenta>')),
            Completion(
                text='Parse Failures',
                start_position=0,
                display=FormattedText([('', 'Parse Failures')]),
                display_meta=HTML(
                    'Columns: <ansiblue>tags, logsource, program, message</ansiblue>')),
            Completion(
                text='Webserver',
                start_position=0,
                display=FormattedText([('', 'Webserver')]),
                display_meta=HTML(
                    'Columns: <ansiblue>http_host, http_clientip, http_verb, '
                    'message, http_code</ansiblue>')),
            Completion(
                text='Webserver 404',
                start_position=0,
                display=FormattedText([('', 'Webserver 404')]),
                display_meta=HTML(
                    'Columns: <ansiblue>http_clientip, http_verb, '
                    'message, http_code</ansiblue>'))]

        # check element count
        self.assertEqual(len(completions), len(expected_completions))
        # check elements
        for idx, value in enumerate(completions):
            expected_value = expected_completions[idx]
            self.assertEqual(value, expected_value)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.prompt.PromptSession')
    def test_prompt_result_positive(self, mock_prompt_session):
        expected_value = 'test-value-positive'
        mock_prompt_session.return_value.prompt.return_value = expected_value

        kibana_saved_search_select_prompt = KibanaSavedSearchSelectPrompt(None)
        # test
        kibana_saved_search_select_prompt._prompt()
        # check
        self.assertEqual(kibana_saved_search_select_prompt._selected_saved_search, expected_value)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.prompt.PromptSession')
    def test_prompt_result_negative_dummy_value(self, mock_prompt_session):
        mock_prompt_session.return_value.prompt.return_value = '---'

        kibana_saved_search_select_prompt = KibanaSavedSearchSelectPrompt(None)
        # test
        kibana_saved_search_select_prompt._prompt()
        # check
        self.assertIsNone(kibana_saved_search_select_prompt._selected_saved_search)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.prompt.PromptSession')
    def test_prompt_result_negative_none(self, mock_prompt_session):
        mock_prompt_session.return_value.prompt.return_value = None

        kibana_saved_search_select_prompt = KibanaSavedSearchSelectPrompt(None)
        # test
        kibana_saved_search_select_prompt._prompt()
        # check
        self.assertIsNone(kibana_saved_search_select_prompt._selected_saved_search)

    # ----------------------------------------------------------------------
    @mock.patch('lstail.prompt.PromptSession')
    def test_prompt_result_negative_empty_string(self, mock_prompt_session):
        mock_prompt_session.return_value.prompt.return_value = ''

        kibana_saved_search_select_prompt = KibanaSavedSearchSelectPrompt(None)
        # test
        kibana_saved_search_select_prompt._prompt()
        # check
        self.assertIsNone(kibana_saved_search_select_prompt._selected_saved_search)
