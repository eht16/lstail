# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from collections import OrderedDict


########################################################################
class DisplayConfiguration:  # pylint: disable=too-few-public-methods

    # ----------------------------------------------------------------------
    def __init__(self):
        self.columns = OrderedDict()
