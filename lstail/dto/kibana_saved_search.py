# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.


########################################################################
class KibanaSavedSearch:

    # ----------------------------------------------------------------------
    def __init__(self, title, columns):
        self.title = title
        self.columns = columns

    # ----------------------------------------------------------------------
    def __eq__(self, other):
        if isinstance(other, KibanaSavedSearch):
            return self.title == other.title and self.columns == other.columns

        return False

    # ----------------------------------------------------------------------
    def __repr__(self):
        return f'KibanaSavedSearch(title="{self.title}", columns="{self.columns}")'
