# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from copy import deepcopy


########################################################################
class Query:

    # ----------------------------------------------------------------------
    def __init__(self, index, query, time_field_name):
        self.index = index
        self.query = query
        self.time_field_name = time_field_name

    # ----------------------------------------------------------------------
    def clone(self):
        new_query = deepcopy(self.query)
        return Query(self.index, new_query, self.time_field_name)
