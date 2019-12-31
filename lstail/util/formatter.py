# -*- coding: utf-8 -*-

import string


########################################################################
class AutoFillFormatter(string.Formatter):
    """
    Gracefully handle missing keys/attributes in the supplied mapping and use an autofill
    value for the missing input.
    """

    # ----------------------------------------------------------------------
    def __init__(self, autofill):
        self.autofill = autofill

    # ----------------------------------------------------------------------
    def get_field(self, field_name, args, kwargs):
        try:
            val = super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            val = self.autofill, field_name
        return val
