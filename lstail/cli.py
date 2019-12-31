# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

import sys

from lstail.config import LstailConfigParser
from lstail.options import LstailArgumentParser
from lstail.reader import LogstashReader


# ----------------------------------------------------------------------
def _setup_options():
    argument_parser = LstailArgumentParser()
    return argument_parser.parse()


# ----------------------------------------------------------------------
def _setup_config(options):
    config_parser = LstailConfigParser(options)
    return config_parser.parse()


# ----------------------------------------------------------------------
def main():
    options = _setup_options()
    try:
        config = _setup_config(options)
        reader = LogstashReader(config)
        if options.kibana_list_saved_searches:
            reader.list_kibana_saved_searches()
        elif options.version:
            reader.show_version()
        else:
            reader.read()
    except Exception as exc:  # pylint: disable=broad-except
        if options.debug:
            raise
        else:
            print(exc, file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
