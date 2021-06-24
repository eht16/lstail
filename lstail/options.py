# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser


########################################################################
class LstailArgumentParser:

    # ----------------------------------------------------------------------
    def __init__(self, argv=None):
        self._argv = argv
        self._argument_parser = None
        self._initial_query_exclusive_group = None
        self._actions_exclusive_group = None
        self._arguments = None

    # ----------------------------------------------------------------------
    def parse(self):
        self._init_argument_parser()
        self._setup_arguments()
        self._parse_arguments()
        return self._arguments

    # ----------------------------------------------------------------------
    def _init_argument_parser(self):
        self._argument_parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
        # mutually exclusive group for --lines and --range to support only one of them or none
        # but not both at once
        self._initial_query_exclusive_group = self._argument_parser.add_mutually_exclusive_group()

        # mutually exclusive group for actions: --version and --list-saved-searches
        self._actions_exclusive_group = self._argument_parser.add_mutually_exclusive_group()

    # ----------------------------------------------------------------------
    def _setup_arguments(self):
        self._actions_exclusive_group.add_argument(
            '-V',
            '--version',
            dest='version',
            action='store_true',
            help='show version and exit',
            default=False)

        self._argument_parser.add_argument(
            '-d',
            '--debug',
            dest='debug',
            action='store_true',
            help='enable tracebacks',
            default=False)

        self._argument_parser.add_argument(
            '-v',
            '--verbose',
            dest='verbose',
            action='store_true',
            help='Show own log messages',
            default=False)

        self._argument_parser.add_argument(
            '-c',
            '--config',
            dest='config_file_path',
            metavar='FILE',
            help='configuration file path')

        self._argument_parser.add_argument(
            '-f',
            '--follow',
            dest='follow',
            action='store_true',
            help='Constantly fetch new data from ElasticSearch',
            default=False)

        self._actions_exclusive_group.add_argument(
            '-l',
            '--list-saved-searches',
            dest='kibana_list_saved_searches',
            action='store_true',
            help='List all saved searches from Kibana',
            default=False)

        self._argument_parser.add_argument(
            '-H',
            '--no-header',
            dest='no_header',
            action='store_true',
            help='Do not print header line before the output',
            default=False)

        self._argument_parser.add_argument(
            '--csv',
            dest='csv_output',
            action='store_true',
            help='Use CSV (comma separated) output',
            default=False)

        self._initial_query_exclusive_group.add_argument(
            '-n',
            '--lines',
            dest='initial_query_size',
            metavar='NUM',
            type=int,
            help='Output the last NUM lines, instead of the last 10')

        self._argument_parser.add_argument(
            '-q',
            '--query',
            dest='custom_search',
            metavar='QUERY',
            help='Set/Overwrite the search query (use Lucene query syntax)')

        # ~self._argument_parser.add_argument(
        self._initial_query_exclusive_group.add_argument(
            '-r',
            '--range',
            dest='initial_time_range',
            metavar='RANGE',
            help='Query events from the last RANGE minutes(m)/hours(h)/days(d)')

        self._argument_parser.add_argument(
            '-s',
            '--saved-search',
            dest='kibana_saved_search',
            metavar='NAME',
            help='Saved search title as stored in Kibana ("-" to select from a list)')

        self._argument_parser.add_argument(
            '--select-saved-search',
            dest='select_kibana_saved_search',
            action='store_true',
            help='Interactively select a saved search from a list',
            default=False)

    # ----------------------------------------------------------------------
    def _parse_arguments(self):
        self._arguments = self._argument_parser.parse_args(self._argv)
