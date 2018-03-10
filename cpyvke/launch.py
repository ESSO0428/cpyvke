#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright © 2016-2018 Cyril Desjouy <ipselium@free.fr>
#
# This file is part of cpyvke
#
# cpyvke is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cpyvke is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cpyvke. If not, see <http://www.gnu.org/licenses/>.
#
#
# Creation Date :
# Last Modified : sam. 10 mars 2018 20:19:10 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""


import os


def main():
    """
    launch ipython console.
    """
    logdir = os.path.expanduser('~') + '/.cpyvke/'
    lockfile = logdir + 'kd5.lock'

    if os.path.exists(lockfile):
        with open(lockfile, 'r') as f:
            kernel_id = f.readline()

        cmd = 'jupyter console --existing kernel-{}.json'.format(kernel_id)
        os.system(cmd)

    else:
        print('No associated kernel found !')


if __name__ == "__main__":
    main()
