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
# Creation Date : Mon Nov 14 09:08:25 2016
# Last Modified : mar. 13 mars 2018 17:06:51 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import os
import curses
from curses import panel
from math import ceil
from time import sleep

from ..utils.kernel import kernel_list, start_new_kernel, shutdown_kernel, connect_kernel
from ..utils.comm import send_msg
from .widgets import WarningMsg, Help


class KernelWin:
    """ Kernel Window. """

    def __init__(self, parent):
        """ Kernel Window Constructor """

        self.parent = parent
        self.RequestSock = parent.RequestSock

        # Queue for kernel changes
        self.kc = parent.kc

        # Define Styles
        self.Config = parent.Config
        self.c_kern_txt = parent.c_kern_txt
        self.c_kern_bdr = parent.c_kern_bdr
        self.c_kern_ttl = parent.c_kern_ttl
        self.c_kern_hh = parent.c_kern_hh
        self.c_kern_co = parent.c_kern_co
        self.c_kern_al = parent.c_kern_al
        self.c_kern_di = parent.c_kern_di
        self.c_kern_pwf = parent.c_kern_pwf

        self.stdscreen = parent.stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()
        self.kernel_info = parent.kernel_info
        self.cf = parent.cf
        # Init Menu
        self.win_title = ' Kernel Manager '

        # Init constants
        self.new_kernel_connection = False
        self.position = 1
        self.page = 1

        # Init Variable Box
        self.row_max = self.screen_height-self.kernel_info  # max number of rows

        self.KernelLst = self.stdscreen.subwin(self.row_max+2, self.screen_width-2, 1, 1)
        self.KernelLst.keypad(1)
        self.KernelLst.bkgd(self.c_kern_txt)
        self.KernelLst.attrset(self.c_kern_bdr | curses.A_BOLD)  # Change border color
        self.panel_kernel = panel.new_panel(self.KernelLst)
        self.panel_kernel.hide()

    def display(self):
        """ Display the kernel explorer. """

        self.panel_kernel.top()     # Push the panel to the bottom of the stack.
        self.panel_kernel.show()    # Display the panel
        self.KernelLst.clear()

        self.pkey = -1
        while self.pkey != 113:
            # Get variables from daemon
            self.cf = self.kc.connection_file
            self.lst = kernel_list(self.cf)
            self.row_num = len(self.lst)

            # Menu Help
            if self.pkey == 104:    # -> h
                help_menu = Help(self.parent)
                help_menu.Display()

            # Navigate in the variable list window
            self.navigate_kernel_lst()

            if self.pkey == ord("\n") and self.row_num != 0:
                self.init_kernel_menu()

            # Erase all windows
            self.KernelLst.erase()

            # Create border before updating fields
            self.KernelLst.border(0)

            # Update all windows (virtually)
            self.update_kernel_lst()     # Update variables list

            # Update display
            self.KernelLst.refresh()

            # Get pressed key
            self.pkey = self.stdscreen.getch()

            # Sleep a while
            sleep(0.1)

            if self.new_kernel_connection:  # Close menu if new connect
                break

            if self.pkey == curses.KEY_RESIZE:
                break

        self.KernelLst.clear()
        self.panel_kernel.hide()
        return self.cf, self.kc

    def update_kernel_lst(self):
        """ Update the kernel list """

        if self.Config['font']['pw-font'] == 'True':
            self.KernelLst.addstr(0, int((self.screen_width-len(self.win_title))/2),
                                  '', curses.A_BOLD | self.c_kern_pwf)
            self.KernelLst.addstr(self.win_title, curses.A_BOLD | self.c_kern_ttl)
            self.KernelLst.addstr('', curses.A_BOLD | self.c_kern_pwf)
        else:
            self.KernelLst.addstr(0, int((self.screen_width-len(self.win_title))/2),
                                  '|' + self.win_title + '|',
                                  curses.A_BOLD | self.c_kern_ttl)

        for i in range(1+(self.row_max*(self.page-1)),
                       self.row_max+1+(self.row_max*(self.page-1))):

            if self.row_num == 0:
                self.KernelLst.addstr(1, 1, "No kernel available",
                                      self.c_kern_hh | curses.A_BOLD)

            else:
                if (i+(self.row_max*(self.page-1)) == self.position+(self.row_max*(self.page-1))):
                    self.KernelLst.addstr(i, 2, self.lst[i-1][0].ljust(self.screen_width-5),
                                          self.c_kern_hh | curses.A_BOLD)
                    if str(self.lst[i-1][1]) == "[Died]":
                        self.KernelLst.addstr(i, self.screen_width-15,
                                              str(self.lst[i-1][1]),
                                              curses.A_BOLD | self.c_kern_di)
                    elif str(self.lst[i-1][1]) == "[Alive]":
                        self.KernelLst.addstr(i, self.screen_width-15,
                                              str(self.lst[i-1][1]),
                                              curses.A_BOLD | self.c_kern_al)
                    elif str(self.lst[i-1][1]) == "[Connected]":
                        self.KernelLst.addstr(i, self.screen_width-15,
                                              str(self.lst[i-1][1]),
                                              curses.A_BOLD | self.c_kern_co)
                else:
                    self.KernelLst.addstr(i, 2,
                                          self.lst[i-1][0].ljust(self.screen_width-5),
                                          self.c_kern_txt | curses.A_DIM)
                    if str(self.lst[i-1][1]) == "[Died]":
                        self.KernelLst.addstr(i, self.screen_width-15,
                                              str(self.lst[i-1][1]),
                                              curses.A_BOLD | self.c_kern_di)
                    elif str(self.lst[i-1][1]) == "[Alive]":
                        self.KernelLst.addstr(i, self.screen_width-15,
                                              str(self.lst[i-1][1]),
                                              curses.A_BOLD | self.c_kern_al)
                    elif str(self.lst[i-1][1]) == "[Connected]":
                        self.KernelLst.addstr(i, self.screen_width-15,
                                              str(self.lst[i-1][1]),
                                              curses.A_BOLD | self.c_kern_co)
                if i == self.row_num:
                    break

        self.stdscreen.refresh()
        self.KernelLst.refresh()

    def navigate_kernel_lst(self):
        """ Navigation though the kernel list"""

        self.pages = int(ceil(self.row_num/self.row_max))
        if self.pkey == curses.KEY_DOWN:
            self.navigate_down()
        if self.pkey == curses.KEY_UP:
            self.navigate_up()
        if self.pkey in (curses.KEY_LEFT, 339) and self.page > 1:
            self.navigate_left()
        if self.pkey in (curses.KEY_RIGHT, 338) and self.page < self.pages:
            self.navigate_right()

    def navigate_right(self):
        """ Navigate Right. """

        self.page = self.page + 1
        self.position = (1+(self.row_max*(self.page-1)))

    def navigate_left(self):
        """ Navigate Left. """

        self.page = self.page - 1
        self.position = 1+(self.row_max*(self.page-1))

    def navigate_up(self):
        """ Navigate Up. """

        if self.page == 1:
            if self.position > 1:
                self.position = self.position - 1
        else:
            if self.position > (1+(self.row_max*(self.page-1))):
                self.position = self.position - 1
            else:
                self.page = self.page - 1
                self.position = self.row_max+(self.row_max*(self.page-1))

    def navigate_down(self):
        """ Navigate Down. """

        if self.page == 1:
            if (self.position < self.row_max) and (self.position < self.row_num):
                self.position = self.position + 1
            else:
                if self.pages > 1:
                    self.page = self.page + 1
                    self.position = 1+(self.row_max*(self.page-1))
        elif self.page == self.pages:
            if self.position < self.row_num:
                self.position = self.position + 1
        else:
            if self.position < self.row_max+(self.row_max*(self.page-1)):
                self.position = self.position + 1
            else:
                self.page = self.page + 1
                self.position = 1+(self.row_max*(self.page-1))

    def init_kernel_menu(self):
        """ Init kernel menu """

        self.selected = self.lst[self.position-1]
        self.kernel_menu_lst = self.create_kernel_menu()

        # Various variables
        self.menuposition = 0
        self.kernel_menu_title = ' ' + self.selected[0].split('-')[1].split('.')[0] + ' '

        # Menu dimensions
        self.kernel_submenu_width = len(max(
            [self.kernel_menu_lst[i][0] for i in range(len(self.kernel_menu_lst))],
            key=len))
        self.kernel_submenu_width = max(self.kernel_submenu_width,
                                        len(self.kernel_menu_title)) + 4
        self.kernel_submenu_height = len(self.kernel_menu_lst) + 2

        # Init Menu
        self.kernel_submenu = self.stdscreen.subwin(self.kernel_submenu_height,
                                                    self.kernel_submenu_width, 2,
                                                    self.screen_width-self.kernel_submenu_width-2)
        self.kernel_submenu.border(0)
        self.kernel_submenu.bkgd(self.c_kern_txt)
        self.kernel_submenu.attrset(self.c_kern_bdr | curses.A_BOLD)  # Change border color
        self.kernel_submenu.keypad(1)

        # Send menu to a panel
        self.panel_kernel_submenu = panel.new_panel(self.kernel_submenu)
        # Hide the panel. This does not delete the object, it just makes it invisible.
        self.panel_kernel_submenu.hide()
        panel.update_panels()

        # Submenu
        self.display_kernel_menu()

    def create_kernel_menu(self):
        """ Create the item list for the kernel menu  """

        if self.selected[1] == '[Connected]':
            return [('New', 'self._new_k()'),
                    ('Remove all died', 'self._rm_all_cf()'),
                    ('Shutdown all alive', 'self._kill_all_k()')]

        elif self.selected[1] == '[Alive]':
            return [('Connect', 'self._connect_k()'),
                    ('New', 'self._new_k()'),
                    ('Shutdown', 'self._kill_k()'),
                    ('Shutdown all alive', 'self._kill_all_k()'),
                    ('Remove all died', 'self._rm_all_cf()')]

        elif self.selected[1] == '[Died]':
            return [('Restart', 'self._restart_k()'),
                    ('New', 'self._new_k()'),
                    ('Remove file', 'self._rm_cf()'),
                    ('Remove all died', 'self._rm_all_cf()'),
                    ('Shutdown all alive', 'self._kill_all_k()')]

        else:
            return []

    def display_kernel_menu(self):
        """ Display the kernel menu """

        self.panel_kernel_submenu.top()        # Push the panel to the bottom of the stack.
        self.panel_kernel_submenu.show()       # Display the panel (which might have been hidden)
        self.kernel_submenu.clear()

        menukey = -1
        while menukey not in (27, 113):
            self.kernel_submenu.border(0)

            if self.Config['font']['pw-font'] == 'True':
                self.kernel_submenu.addstr(0,
                                           int((self.kernel_submenu_width -
                                                len(self.kernel_menu_title) - 2)/2),
                                           '', curses.A_BOLD | self.c_kern_pwf)
                self.kernel_submenu.addstr(self.kernel_menu_title,
                                           curses.A_BOLD | self.c_kern_ttl)
                self.kernel_submenu.addstr('', curses.A_BOLD | self.c_kern_pwf)
            else:
                self.kernel_submenu.addstr(0,
                                           int((self.kernel_submenu_width -
                                                len(self.kernel_menu_title) - 2)/2),
                                           '|' + self.kernel_menu_title + '|',
                                           curses.A_BOLD | self.c_kern_ttl)

            self.kernel_submenu.refresh()

            # Create entries
            for index, item in enumerate(self.kernel_menu_lst):
                if index == self.menuposition:
                    mode = self.c_kern_hh | curses.A_BOLD
                else:
                    mode = self.c_kern_txt | curses.A_DIM

                self.kernel_submenu.addstr(1+index, 1, item[0], mode)

            menukey = self.kernel_submenu.getch()

            if menukey in [curses.KEY_ENTER, ord('\n')]:
                eval(self.kernel_menu_lst[self.menuposition][1])
                break

            elif menukey == curses.KEY_UP:
                self.navigate_kernel_menu(-1)

            elif menukey == curses.KEY_DOWN:
                self.navigate_kernel_menu(1)

        self.kernel_submenu.clear()
        self.panel_kernel_submenu.hide()

    def navigate_kernel_menu(self, n):
        """ Navigate through the kernel submenu """

        self.menuposition += n
        if self.menuposition < 0:
            self.menuposition = 0
        elif self.menuposition >= len(self.kernel_menu_lst):
            self.menuposition = len(self.kernel_menu_lst)-1

    def _new_k(self):
        """ Create a new kernel. """

        kid = start_new_kernel(version=self.Config['kernel version']['version'])
        msg = WarningMsg(self.stdscreen)
        msg.Display('Kernel id {} created (Python {})'.format(kid,
                    self.Config['kernel version']['version']))

    def _connect_k(self):
        """ Connect to a kernel. """

        km, self.kc = connect_kernel(self.selected[0])
        send_msg(self.RequestSock, '<cf>' + self.selected[0])

        # Update kernels connection file and set new kernel flag
        self.cf = self.kc.connection_file
        self.new_kernel_connection = True

    def _restart_k(self):
        """ Restart a died kernel. """

        msg = WarningMsg(self.stdscreen)
        msg.Display('Not Implement yet!')

    def _kill_k(self):
        """ Kill kernel. """

        shutdown_kernel(self.selected[0])
        self.position = 1
        self.page = 1

    def _kill_all_k(self):
        """ Kill all kernel marked as Alive. """

        for json_path, status in self.lst:
            if status == '[Alive]':
                shutdown_kernel(json_path)
        self.page = 1
        self.position = 1  # Reinit cursor location

    def _rm_cf(self):
        """ Remove connection file of died kernel. """

        os.remove(self.selected[0])
        self.page = 1
        self.position = 1  # Reinit cursor location

    def _rm_all_cf(self):
        """ Remove connection files of all died kernels. """

        for json_path, status in self.lst:
            if status == '[Died]':
                os.remove(json_path)
        self.page = 1
        self.position = 1  # Reinit cursor location
