#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : KernelDaemon5.py
# Creation Date : Fri Nov  4 21:49:15 2016
# Last Modified : jeu. 08 déc. 2016 15:38:14 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <cyril.desjouy@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""


###############################################################################
# IMPORTS
###############################################################################
from time import sleep
import threading
from ktools import init_kernel, ProcInfo


def WhoToDict(string):
    ''' Format output of daemon to a dictionnary '''

    variables = {}
    for item in string.split('\n')[2:-1]:
        var_name = filter(None, item.split(' '))[0]
        var_typ = filter(None, item.split(' '))[1]
        var_val = filter(None, item.split(' '))[2:]
        var_val = ' '.join(var_val)
        if var_typ != 'function':
            variables[var_name] = {'value': var_val, 'type': var_typ}
    return variables


class Watcher(threading.Thread):
    '''
    Daemon : watch the kernel input and update variable list.
    The client may also request for the content of a variable.
    '''

    def __init__(self, kc, delay, qvar, qreq, qkc, ONLY_DAEMON=False):

        # Inputs
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        self._stop = threading.Event()
        self.kc = kc
        self.delay = delay
        self.qvar = qvar    # Use Socker instead ?
        self.qreq = qreq
        self.qkc = qkc
        self.ONLY_DAEMON = ONLY_DAEMON

        # Init variables
        self.msg = 0
        self.CheckInput()
        self.variables = self.Exec('whos')
        self.qvar.put(WhoToDict(self.variables))

    def run(self):
        ''' Run the variable explorer daemon '''

        mem = 0
        while True:

            # Memory usage
            if self.ONLY_DAEMON:
                mem = ProcInfo(mem)

            # Check in new entries in kernel
            self.CheckInput()

            # If new entries, update variables
            if self.msg == 1:
                self.variables = self.Exec('whos')
                # Send to CUI
                self.SendToCUI()

            # Listen if CUI request a value
            self.CheckRequest()

            # watch for change of kernel
            self.KernelChange()

            # Terminate daemon
            if self._stop.isSet():
                break

            sleep(self.delay)

    def KernelChange(self):
        ''' Watch kernel changes '''

        if self.qkc.qsize() > 0:
            self.kc = self.qkc.get(timeout=0)
            init_kernel(self.kc)
            # Force update
            self.variables = self.Exec('whos')
            # Send to CUI
            self.SendToCUI()

    def SendToCUI(self):
        ''' Send variables to CUI '''

        if self.qvar.qsize() > 0:
            self.qvar.queue.clear()

        self.qvar.put(WhoToDict(self.variables))

    def CheckRequest(self):
        ''' Check if CUI sent a request and answer '''

        if self.qreq.qsize() > 0:
            value = self.Exec(self.qreq.get())

    def CheckInput(self):
        ''' Check the iopub msgs available '''

        self.msg = 0
        while self.kc.iopub_channel.msg_ready():
            data = self.kc.get_iopub_msg(timeout=0.1)

            if self.ONLY_DAEMON is True:
                print(data['msg_type'])
                print(data['content'])
                print('\n')

            # Wait for answer when execute reset
            if data['msg_type'] == 'execute_input':
                if data['content']['code'] == 'reset':
                    init_kernel(self.kc)
                    data = self.kc.get_iopub_msg()

            # Wait for end execution (script)
            if data['msg_type'] == 'execute_input':
                if 'run' in data['content']['code']:
                    data = self.kc.get_iopub_msg()

            # For long script with output to sdtout
            while data['msg_type'] == 'stream':
                data = self.kc.get_iopub_msg()

            self.msg = 1

    def stop(self):
        ''' Stop thread. '''

        self._stop.set()

    def Exec(self, code):
        ''' Execute **code** '''

        value = 'No Value !'

        self.kc.execute(code, store_history=False)

        while self.kc.iopub_channel.msg_ready() == False:  # To fix.Have to wait
            sleep(0.5)

        while self.kc.iopub_channel.msg_ready():
            data = self.kc.get_iopub_msg()
            if data['msg_type'] == 'stream' and code == 'whos':
                value = data['content']['text']
                if self.ONLY_DAEMON is True:
                    print('Execute result :')
                    print(data['content']['text'])

            elif data['msg_type'] == 'execute_result' and code != 'whos':
                value = data['content']['data']['text/plain']

            elif data['msg_type'] == 'stream' and code != 'whos':
                value = data['content']['text']

        self.msg = 0

        return value

if __name__ == "__main__":

    from ktools import connect_kernel
    from jupyter_client import find_connection_file
    from Queue import Queue

    delay = 0.5
    cf = find_connection_file('27146')
    km, kc = connect_kernel(cf)

    qvar = Queue()
    qreq = Queue()
    qkc = Queue()

    WK = Watcher(kc, delay, qvar, qreq, qkc, True)
    WK.start()
    WK.join()


