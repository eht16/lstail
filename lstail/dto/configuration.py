# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from collections import deque

from lstail.dto.display import DisplayConfiguration
from lstail.dto.format import FormatConfiguration
from lstail.dto.kibana import KibanaConfiguration
from lstail.dto.parser import ParserConfiguration


########################################################################
class Configuration:  # pylint: disable=too-few-public-methods,too-many-instance-attributes

    # ----------------------------------------------------------------------
    def __init__(self):
        self.initial_query_size = None
        self.initial_time_range = None
        self.default_index = None
        self.refresh_interval = None
        self.verify_ssl_certificates = None
        self.header_color = None
        self.no_header = None
        self.csv_output = None
        self.timeout = None
        self.follow = None
        self.verbose = None
        self.debug = None
        self.select_kibana_saved_search = None

        self.servers = deque()
        self.kibana = KibanaConfiguration()
        self.parser = ParserConfiguration()
        self.format = FormatConfiguration()
        self.display = DisplayConfiguration()

    # ----------------------------------------------------------------------
    def __repr__(self):
        return f'<{self.__class__.__name__}(debug={self.debug}, verbose={self.verbose})>'
