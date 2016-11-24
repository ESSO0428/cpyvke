#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : CUITools.py
# Creation Date : Mon Nov 21 23:26:57 2016
# Last Modified : jeu. 24 nov. 2016 14:06:21 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <cyril.desjouy@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""

###############################################################################
# IMPORT
###############################################################################


###############################################################################
# FORMAT CELL
###############################################################################
def format_cell(variables, string, max_width):
    ''' Format cells for display '''

    max_width = int((max_width-5)/3)
    name = string.ljust(max_width)
    typ = '[' + variables[string]['type'] + ']'
    typ = typ.ljust(max_width)

    if 'module' in variables[string]['value']:
        val = variables[string]['value'].split("'")[1]
        val = val.ljust(max_width)

    elif 'elem' in variables[string]['value']:
        val1 = variables[string]['value'].split(":")[0]
        val2 = variables[string]['value'].split("`")[1]
        val = val1 + ' [' + val2 + ']'
        val = val.ljust(max_width)
    else:
        # Repr to avoid interpreting \n in strings
        val = repr(variables[string]['value']).split("'")[1].ljust(max_width)

    if len(val) > max_width:
        val = val[0:max_width-4] + '... '

    if len(name) > max_width:
        name = name[0:max_width-4] + '... '

    if len(typ) > max_width:
        typ = typ[0:max_width-4] + '... '

    return name[0:max_width] + val[0:max_width] + typ[0:max_width]
