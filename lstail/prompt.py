# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML


DUMMY_SAVED_SEARCH_NAME = '---'


########################################################################
class KibanaSavedSearchSelectPrompt:

    # ----------------------------------------------------------------------
    def __init__(self, saved_searches):
        self._saved_searches = saved_searches
        self._saved_searches_completions = {}
        self._saved_searches_completer = None
        self._selected_saved_search = None

    # ----------------------------------------------------------------------
    def prompt(self):
        if not self._saved_searches:
            return None

        self._factor_saved_search_completions()
        self._factor_saved_search_completer()

        self._prompt()
        return self._selected_saved_search

    # ----------------------------------------------------------------------
    def _factor_saved_search_completions(self):
        self._saved_searches_completions[DUMMY_SAVED_SEARCH_NAME] = HTML(
            '<ansimagenta><i>Continue without any saved search</i></ansimagenta>')

        for saved_search in self._saved_searches:
            meta = HTML(f'Columns: <ansiblue>{saved_search.columns}</ansiblue>')
            self._saved_searches_completions[saved_search.title] = meta

    # ----------------------------------------------------------------------
    def _factor_saved_search_completer(self):
        completion_keys = self._saved_searches_completions.keys()

        self._saved_searches_completer = WordCompleter(
            completion_keys,
            meta_dict=self._saved_searches_completions,
            ignore_case=True)

    # ----------------------------------------------------------------------
    def _prompt(self):
        prompt_session = PromptSession(
            'Saved search: ',
            completer=self._saved_searches_completer,
            mouse_support=True,
            reserve_space_for_menu=20)
        # auto start the completion
        prompt_session.app.current_buffer.start_completion(select_first=False)

        selected_saved_search = prompt_session.prompt()

        if not selected_saved_search or selected_saved_search == DUMMY_SAVED_SEARCH_NAME:
            self._selected_saved_search = None
        else:
            self._selected_saved_search = selected_saved_search
