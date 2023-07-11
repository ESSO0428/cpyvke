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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cpyvke.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Creation Date : Wed Nov  9 16:27:41 2016
# Last Modified : lun. 09 avril 2018 21:56:41 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
from matplotlib.pyplot import figure, plot, imshow, show
import numpy as np
import pandas as pd
pd.set_option('display.max_rows', None)     # 显示所有行
pd.set_option('display.max_columns', None)  # 显示所有列

import os
from time import time, sleep
from multiprocessing import Process
import subprocess
import sys
import locale
from inspect import getsource
from cpyvke.curseswin.widgets import suspend_curses
from cpyvke.utils.comm import send_msg


locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


def get_source_code(code):
    return getsource(code)


def inspect_class_instance(class_inst):
    """ Return a dictionnary of :
        * class attributes    : inst.__class__.__dict__
        * instance attributes : int.__dict__
    """
    class_attr = {i: {'type': str(type(class_inst.__class__.__dict__[i])),
                      'value': str(class_inst.__class__.__dict__[i])} for i in
                  class_inst.__class__.__dict__ if not i.startswith('_')}

    inst_attr = {i: {'type': '@' + str(type(class_inst.__dict__[i])),
                     'value': str(class_inst.__dict__[i])} for i in
                 class_inst.__dict__ if not i.startswith('_')}

    return dict(class_attr, **inst_attr)


def inspect_class(class_inst):
    """ Return a dictionnary of :
        * class attributes    : inst.__class__.__dict__
    """
    class_attr = {i: {'type': str(type(class_inst.__dict__[i])),
                      'value': str(class_inst.__dict__[i])} for i in
                  class_inst.__dict__ if not i.startswith('_')}

    return class_attr


def threaded(func):
    """ Run func in thread """

    def run(*k, **kw):
        t = Process(target=func, args=k, kwargs=kw)
        t.start()
        return t

    return run


class Inspect:
    """ Plot/Display variable. """

    def __init__(self, sock, varval, varname, vartype):

        self.sock = sock
        self.varval = varval
        self.vartype = vartype
        self.varname = varname

    def wait(self):
        """ Wait for variable value. """

        i, j = 0, 0
        spinner = [['.', 'o', 'O', 'o'],
                   ['.', 'o', 'O', '@', '*'],
                   ['v', '<', '^', '>'],
                   ['(o)(o)', '(-)(-)', '(_)(_)'],
                   ['◴', '◷', '◶', '◵'],
                   ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
                   ['▁', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃'],
                   ['▉', '▊', '▋', '▌', '▍', '▎', '▏', '▎', '▍', '▌', '▋', '▊', '▉'],
                   ['▖', '▘', '▝', '▗'],
                   ['▌', '▀', '▐', '▄'],
                   ['┤', '┘', '┴', '└', '├', '┌', '┬', '┐'],
                   ['◢', '◣', '◤', '◥'],
                   ['◰', '◳', '◲', '◱'],
                   ['◐', '◓', '◑', '◒'],
                   ['|', '/', '-', '\\'],
                   ['.', 'o', 'O', '@', '*'],
                   ['◡◡', '⊙⊙', '◠◠'],
                   ['◜ ', ' ◝', ' ◞', '◟ '],
                   ['◇', '◈', '◆'],
                   ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
                   ['⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈'],
                   ['Searching.', 'Searching..', 'Searching...']
                   ]


    @staticmethod
    def type_struct():
        return ('dict', 'tuple', 'list', 'set', 'frozenset',
                'str', 'unicode', 'bytes', 'bytearray')

    @staticmethod
    def type_numeric():
        return ('int', 'float', 'complex')

    @threaded
    def plot2D(self):
        try:
            """ Plot 2D variable. """

            figure()
            imshow(self.varval)
            show()
        except:
            print("ERROR can't display plot")

    @threaded
    def plot1D(self):
        """ Plot 1D variable. """
        try:
            figure()
            plot(self.varval)
            show()
        except:
            print("ERROR can't display plot")

    @threaded
    def plot1Dcols(self):
        """ Plot 2D variable : superimpose all columns """
        try:
            figure()
            for i in range(np.shape(self.varval)[1]):
                plot(self.varval[:, i])
            show()
        except:
            print("ERROR can't display plot")

    @threaded
    def plot1Dlines(self):
        """ Plot 2D variable : superimpose all lines """
        try:
            figure()
            for i in range(np.shape(self.varval)[0]):
                plot(self.varval[i, :])
            show()
        except:
            print("ERROR can't display plot")

    def save_np(self, varname, SaveDir, METHOD='npy'):
        """ Save numpy variable to file """

        if METHOD == 'txt':
            np.savetxt(SaveDir + varname + '.txt', self.varval)

        if METHOD == 'npy':
            np.save(SaveDir + varname, self.varval)

        if METHOD == 'npz':
            np.savez_compressed(SaveDir + varname, var=self.varval)

    def save(self, SaveDir):
        """ Save variable to text file """

        filename = SaveDir + self.varname

        if self.vartype != 'str' and self.vartype != 'unicode':
            self.varval = str(self.varval)

        if self.vartype == 'unicode':
            with open(filename, 'w') as f:
                f.write(self.varval.encode(code))
        if self.varval in ['DataFrame', 'Series']:
            code = self.varname + ".to_csv('" + self.filename + "', index=False)"
        else:
            with open(filename, 'w') as f:
                f.write(self.varval)

    def display(self, app='less', arg='Help'):
        """
        Display variable using **App** (less|vim).
        If a module is provided, use **arg** to choose wich methode to use.
        """

        filename = '/tmp/tmp_cVKE'

        # Convert all type of variable to string
        if self.vartype != 'str' and self.vartype != 'unicode' and self.vartype not in ['DataFrame', 'Series', 'Index', 'MultiIndex']:
            self.varval = str(self.varval)

        #
        if self.vartype in ['DataFrame', 'Series', 'Index', 'MultiIndex']:
            # code = self.varname + ".to_csv('" + filename + "', index=True, sep='" + "\t" + "')"
            # send_msg(self.sock.RequestSock, '<code>' + code)
            # self.wait()
            filename = '/tmp/tmp_' + self.varname + '.tsv'
            if os.path.exists(filename):
                pass
            else:
                with open(filename, 'w') as f:
                    f.write(self.varval)


        elif self.vartype == 'unicode':
            with open(filename, 'w') as f:
                f.write(self.varval.encode(code))

        elif self.vartype == 'function':
            try:
                if arg == 'help':
                    with open(filename, 'w') as f:
                        f.write(self.varval)
            except ImportError:
                print('Not found!')


        elif self.vartype == 'module':
            if arg == 'help':
                sys.stdout = open(filename, 'w')
                try:
                    exec('import {}'.format(self.varval))
                    print(help(self.varval))
                except ImportError:
                    print('Not found!')

        else:
            with open(filename, 'w') as f:
                f.write(self.varval)

        with suspend_curses():
            if app == 'less' and os.path.exists(filename):
                try:
                    # Try opening with lvim
                    command1 = ["column", "-t", "-s", "\t", filename]
                    command2 = ["less", "-S"]
                    command3 = ["lvim", "-"]
                    
                    p1 = subprocess.Popen(command1, stdout=subprocess.PIPE)
                    p2 = subprocess.Popen(command2, stdin=p1.stdout, stdout=subprocess.PIPE)
                    p1.stdout.close()
                    p3 = subprocess.Popen(command3, stdin=p2.stdout)
                    p2.stdout.close()
                    p3.communicate()
                except FileNotFoundError:
                    try:
                        # If lvim is not available, try opening with nvim
                        command1 = ["column", "-t", "-s", "\t", filename]
                        command2 = ["less", "-S"]
                        command3 = ["nvim", "-"]
                        
                        p1 = subprocess.Popen(command1, stdout=subprocess.PIPE)
                        p2 = subprocess.Popen(command2, stdin=p1.stdout, stdout=subprocess.PIPE)
                        p1.stdout.close()
                        p3 = subprocess.Popen(command3, stdin=p2.stdout)
                        p2.stdout.close()
                        p3.communicate()
                    except FileNotFoundError:
                        try :
                            # If lvim is not available, try opening with vim
                            command1 = ["column", "-t", "-s", "\t", filename]
                            command2 = ["less", "-S"]
                            command3 = ["vim", "-"]
                            
                            p1 = subprocess.Popen(command1, stdout=subprocess.PIPE)
                            p2 = subprocess.Popen(command2, stdin=p1.stdout, stdout=subprocess.PIPE)
                            p1.stdout.close()
                            p3 = subprocess.Popen(command3, stdin=p2.stdout)
                            p2.stdout.close()
                            p3.communicate()
                        except FileNotFoundError:               

                            command1 = ["column", "-t", "-s", "\t", filename]
                            command2 = ["less", "-S"]
                            
                            p1 = subprocess.Popen(command1, stdout=subprocess.PIPE)
                            p2 = subprocess.Popen(command2, stdin=p1.stdout)
                            p1.stdout.close()
                            p2.communicate()
            elif app == 'dataexplore' and os.path.exists(filename):
                command = f'{app} -i {filename}; rm {filename}'
                process = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            elif os.path.exists(filename):
                subprocess.run([app, filename])
            else:
                pass
            subprocess.run(['rm', filename])


class ProceedInspection:
    """ Object inspection """

    def __init__(self, app, sock, logger, name, value, typ, pos, page):
        """ Class constructor """

        self.app = app
        self.sock = sock
        self.logger = logger
        self.varname = name
        self.varval = value
        self.vartype = typ
        self.position = pos
        self.page = page
        self.doc = None

    def get_variable(self):
        """ Get Variable characteristics. """
        if self.vartype in ['module']:
            self.get_module()

        if self.vartype in ['function']:
            self.get_function_code()
            self.get_function_doc()

        elif self.vartype in ['builtin_function_or_method']:
            self.get_function_doc()

        elif self.vartype in Inspect.type_struct():
            self.get_structure()

        elif self.vartype == 'ndarray':
            self.get_ndarray()

        elif self.vartype in ['DataFrame', 'Series', 'Index', 'MultiIndex']:
            self.get_dataframe()

        elif '.' + self.vartype in self.varval:     # Class instance
            self.vartype = 'class'
            self.get_class_instance()

        elif self.vartype == 'type':                # Class
            self.get_class()

        else:
            self._ismenu = True

        return self._ismenu, self.varname, self.varval, self.vartype, self.doc

    def get_function_doc(self):
        """ Get function __doc__ """

        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\tfcpyvke0.write(str({}.__doc__))".format(self.filename, self.varname)
        try:
            send_msg(self.sock.RequestSock, '<code>' + self.code)
            self.logger.debug("Inspecting '{}' with type '{}'".format(self.varname, self.vartype))
            self.wait()
            with open(self.filename, 'r') as f:
                self.doc = f.read()
        except Exception:
            self.logger.error('Get traceback', exc_info=True)
            self.kernel_busy()
        else:
            self.logger.debug('kd5 answered : {}'.format(self.varval))
            os.remove(self.filename)
            self._ismenu = True

    def get_function_code(self):
        """ Get function __doc__ """

        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\tfcpyvke0.write(str(_inspect.getsource({})))".format(self.filename, self.varname)
        self.send_code()

    def get_class_instance(self):
        """ Get Class characteristics. """

        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\tfcpyvke0.write(str(_inspect.inspect_class_instance({})))".format(self.filename, self.varname)
        self.send_code()

    def get_class(self):
        """ Get Class characteristics. """

        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\tfcpyvke0.write(str(_inspect.inspect_class({})))".format(self.filename, self.varname)
        self.send_code()

    def get_module(self):
        """ Get modules characteristics """

        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\tfcpyvke0.write(str({}.__name__))".format(self.filename, self.varname)
        self.send_code()

    def get_structure(self):
        """ Get Dict/List/Tuple characteristics """

        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\tfcpyvke0.write(str({}))".format(self.filename, self.varname)
        self.send_code()

    def get_ndarray(self):
        """ Get ndarray characteristics. """

        self.filename = '/tmp/tmp_' + self.varname + '.npy'
        code = "_np.save('" + self.filename + "', " + self.varname + ')'
        try:
            send_msg(self.sock.RequestSock, '<code>' + code)
            self.logger.debug("Name of module '{}' asked to kd5".format(self.varname))
            self.wait()
            self.varval = np.load(self.filename)
        except Exception:
            self.logger.error('Get traceback : ', exc_info=True)
            self.kernel_busy()
        else:
            self.logger.debug('kd5 answered')
            os.remove(self.filename)
            self._ismenu = True

    def get_dataframe(self):
        """ Get pandas characteristics. """
        
        self.filename = '/tmp/tmp_' + self.varname + '.tsv'
        if self.vartype == 'Index':
            code = f"""
                column_str = ',\\n'.join([f'  {{col}}' for col in {self.varname}.tolist()])
                wrapped_str = f"Index([\\n{{column_str}}\\n])"
                with open('{self.filename}', 'w') as f:
                    f.write(wrapped_str)
            """
        elif self.vartype == 'MultiIndex':
            code = f"""
                with open('{self.filename}', 'w') as f:
                    f.write(str({self.varname}))
            """
        else:
            code = self.varname + ".to_csv('" + self.filename + "', index=True, sep='\t')"
        try:
            send_msg(self.sock.RequestSock, '<code>' + code)
            self.logger.debug("Name of module '{}' asked to kd5".format(self.varname))
            self.wait()
        except Exception:
            self.logger.error('Get traceback:', exc_info=True)
            self.kernel_busy()
        else:
            self.logger.debug('kd5 answered')
            try:
                with open(self.filename, 'r') as f:
                    self.varval = f.read()
                os.remove(self.filename)
                self._ismenu = True
            except FileNotFoundError:
                self.logger.error("File not found: {}".format(self.filename))
            except Exception as e:
                self.logger.error("An error occurred while processing file: {}".format(e))
            # with open(self.filename, 'r') as f: self.varval = f.read()
            # os.remove(self.filename)
            # self._ismenu = True


    def get_help(self):
        """ Help item in menu """

        if self.vartype == 'function':
            self.filename = '/tmp/tmp_' + self.varname
            self.code = "with open('{}' , 'w') as fcpyvke0:\n\tfcpyvke0.write(str({}.__doc__))".format(self.filename, self.varname)
            self.send_code()

    def send_code(self):
        """ Send code to kernel and except answer ! """

        try:
            send_msg(self.sock.RequestSock, '<code>' + self.code)
            self.logger.debug("Inspecting '{}' with type '{}'".format(self.varname, self.vartype))
            self.wait()
            with open(self.filename, 'r') as f:
                if self.vartype in ['str', 'function', 'module', 'builtin_function_or_method']:
                    self.varval = f.read()
                else:
                    self.varval = eval(f.read())
        except Exception:
            self.logger.error('Get traceback', exc_info=True)
            self.kernel_busy()
        else:
            self.logger.debug('kd5 answered : {}'.format(self.varval))
            os.remove(self.filename)
            self._ismenu = True

    def kernel_busy(self):
        """ Handle silent kernel. """

        self.app.wng.display('Kernel Busy ! Try again...')
        self.varval = '[Busy]'
        self._ismenu = False

    def wait(self):
        """ Wait for variable value. """

        i, j = 0, 0
        spinner = [['.', 'o', 'O', 'o'],
                   ['.', 'o', 'O', '@', '*'],
                   ['v', '<', '^', '>'],
                   ['(o)(o)', '(-)(-)', '(_)(_)'],
                   ['◴', '◷', '◶', '◵'],
                   ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
                   ['▁', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃'],
                   ['▉', '▊', '▋', '▌', '▍', '▎', '▏', '▎', '▍', '▌', '▋', '▊', '▉'],
                   ['▖', '▘', '▝', '▗'],
                   ['▌', '▀', '▐', '▄'],
                   ['┤', '┘', '┴', '└', '├', '┌', '┬', '┐'],
                   ['◢', '◣', '◤', '◥'],
                   ['◰', '◳', '◲', '◱'],
                   ['◐', '◓', '◑', '◒'],
                   ['|', '/', '-', '\\'],
                   ['.', 'o', 'O', '@', '*'],
                   ['◡◡', '⊙⊙', '◠◠'],
                   ['◜ ', ' ◝', ' ◞', '◟ '],
                   ['◇', '◈', '◆'],
                   ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
                   ['⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈'],
                   ['Searching.', 'Searching..', 'Searching...']
                   ]

        search = spinner[21]
        spinner = spinner[19]
        ti = time()
        while os.path.exists(self.filename) is False:
            self.app.stdscr.addstr(self.position + 1 - (self.page-1)*self.app.row_max, 1,
                                   spinner[i], self.app.c_exp_txt | curses.A_BOLD)
            self.app.stdscr.addstr(self.app.screen_height - 1, 0,
                                   search[j], self.app.c_exp_txt | curses.A_DIM)

            self.app.stdscr.refresh()
            if i < len(spinner) - 1:
                i += 1
            else:
                i = 0

            if j < len(search) - 1:
                j += 1
            else:
                j = 0

            if time() - ti > 3:
                break

            sleep(0.05)

        self.app.stdscr.refresh()
