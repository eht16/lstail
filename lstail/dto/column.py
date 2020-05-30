# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.


########################################################################
class Column:  # pylint: disable=too-few-public-methods

    # ----------------------------------------------------------------------
    def __init__(self, names=None, color=None, display=None, padding=None):
        self.names = names
        self.color = color
        self.display = display
        self.padding = padding
