# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.


########################################################################
class HttpRetryError(Exception):
    pass


########################################################################
class UnsupportedFilterTypeError(Exception):
    pass


########################################################################
class InvalidTimestampFormatError(Exception):
    pass


########################################################################
class InvalidTimeRangeFormatError(Exception):
    pass


########################################################################
class StopReaderLoop(Exception):
    pass


########################################################################
class DocumentIdAlreadyProcessedError(Exception):

    # ----------------------------------------------------------------------
    def __init__(self, document_id, document_values):
        super().__init__()
        self.document_id = document_id
        self.document_values = document_values

    # ----------------------------------------------------------------------
    def __str__(self):
        msg = 'Received already processed document "{}". Document: {}'.format(
            self.document_id,
            self.document_values)
        return '{}'.format(msg)


########################################################################
class KibanaSavedSearchNotFoundError(Exception):
    pass


########################################################################
class ElasticSearchIndexNotFoundError(Exception):
    pass


########################################################################
class ColumnNotFoundError(Exception):
    pass
