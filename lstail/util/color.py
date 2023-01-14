# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

import os

from lstail.constants import TERM_COLOR_DEFAULT, TERM_COLORS


# ----------------------------------------------------------------------
def factor_color_code(color_name):
    return f'_c_{color_name}'


# ----------------------------------------------------------------------
def get_column_color_key(column_color_name):
    if not column_color_name:
        column_color_name = TERM_COLOR_DEFAULT

    column_color_key = factor_color_code(column_color_name)
    try:
        TERM_COLORS[column_color_key]
    except KeyError as exc:
        raise KeyError(f'Invalid terminal color specification: "{column_color_name}"') from exc
    else:
        return column_color_key


# ----------------------------------------------------------------------
def detect_terminal_color_support(output, force=None):
    try:
        isatty = output.isatty()
    except AttributeError:
        isatty = False

    # allow to globally disable by a common environment variable
    colors_disabled = os.getenv('ANSI_COLORS_DISABLED')

    if force is not None:
        return force

    return isatty and not colors_disabled
