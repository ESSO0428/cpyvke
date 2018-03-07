#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Name : test_sock.py
Creation Date : mar. 27 févr. 2018 12:58:06 CET
Last Modified : mer. 28 févr. 2018 14:46:09 CET
Created By : Cyril Desjouy

Copyright © 2016-2018 Cyril Desjouy <ipselium@free.fr>
Distributed under terms of the BSD license.

-----------
DESCRIPTION

@author: Cyril Desjouy
"""


import socket
from threading import *
import time


sport = 8000

MainSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
MainSock.connect(('', sport))
MainSock.setblocking(0)


while True:
    time.sleep(1)
    try:
        msg = MainSock.recv(1024)
    except BlockingIOError:
        print('Waiting...')
    else:
        print("{} received".format(msg.decode()))

