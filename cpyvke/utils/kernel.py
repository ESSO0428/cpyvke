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
# Creation Date : Fri Nov 4 21:49:15 2016
# Last Modified : mer. 28 mars 2018 23:08:44 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import asyncio
from jupyter_client.blocking.client import BlockingKernelClient
from jupyter_client.asynchronous.client import AsyncKernelClient
from jupyter_client import manager
import threading
import os
import sys
import subprocess
import psutil
import logging
import socket
import time
import glob
import random

logger = logging.getLogger("cpyvke.ktools")

def generate_unused_kernel_id(exclude_ids=None):
    runtime_dir = os.path.expanduser("~/.local/share/jupyter/runtime/")
    existing_ids = set()
    for filename in glob.glob(runtime_dir + "/kernel-*.json"):
        kernel_id = filename.split("-")[1].split(".")[0]
        existing_ids.add(kernel_id)

    if exclude_ids is None:
        exclude_ids = set()

    while True:
        kernel_id = str(random.randint(1, 999999))
        if kernel_id not in existing_ids and kernel_id not in exclude_ids:
            return kernel_id

def start_new_kernel(LogDir=os.path.expanduser("~") + "/.cpyvke/", version=3):

    kernel_id = generate_unused_kernel_id()
    """ Start a new kernel and return the kernel id """
    runtime_dir = os.path.expanduser("~/.local/share/jupyter/runtime")
    python_executable = sys.executable
    # python or ~/anaconda3/bin/python .... or env python ...
    kernel_cmd = [python_executable, '-m', 'ipykernel_launcher', '-f', '{}/kernel-{}.json'.format(runtime_dir, kernel_id)]

    with open(LogDir + 'kd5.lock', "w") as f:
        # if version == '2':
        #     subprocess.Popen(["ipython", "kernel"], stdout=f)
        # else:
        #     subprocess.Popen(["ipython3", "kernel"], stdout=f)
        subprocess.Popen(kernel_cmd, stdout=f)

    time.sleep(1)

    with open(LogDir + 'kd5.lock', "r") as f:
        kid = f.read().split('kernel-')[1].split('.json')[0]

    with open(LogDir + 'kd5.lock', "w") as f:
        f.write(kid)

    logger.info('Create :: Kernel id. {}'.format(kid))

    return kid


def is_runing(cf):
    """ Check if kernel is alive.
    """

    # kc = BlockingKernelClient()
    kc = AsyncKernelClient()
    kc.load_connection_file(cf)
    # kc.start_channels()
    port = kc.get_connection_info()['iopub_port']

    # if check_server(port):
    if is_open("127.0.0.1", port):
        return True
    else:
        return False


def check_server(port):
    """ Check if a service is listening on port.

    NOTE : Too slow for curses interface -> replaced by socket tests : is_open()

    """

    # addr = [item.laddr for item in psutil.net_connections('inet') if str(port) in str(item.laddr[1])]
    addr = [item.laddr for item in psutil.net_connections('inet') if item.laddr and str(port) in str(item.laddr[1])]
    if addr:
        return True
    else:
        return False


def is_open(ip, port):
    """ Check if port is open on ip """

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except socket.error:
        return False


def set_kid(cf):
    return cf.split('kernel-')[1].split('.json')[0]


def kernel_list(cf=None):
    """ List of connection files. """

    try:
        path = os.path.expanduser('~/.local/share/jupyter/runtime/')
        lstk1 = [path + item for item in os.listdir(path) if 'kernel' in item]
    except FileNotFoundError:
        lstk1 = []

    try:
        path = '/run/user/1000/jupyter/'
        lstk2 = [path + item for item in os.listdir(path) if 'kernel' in item]
    except FileNotFoundError:
        lstk2 = []

    lstk = lstk1 + lstk2

    try:
        lst = [(item, '[Alive]' if is_runing(item) else '[Died]') for item in lstk]
    except Exception:
        logger.error('No kernel available', exc_info=True)
        return []
    else:
        return [(cf, '[Connected]') if cf in item else item for item in lst]


def kernel_dic(cf=None):
    """ Dictionnary of connection files. The keys are :
        {'name': {'value': val, 'type': 'type'}}
    """

    try:
        path = os.path.expanduser('~/.local/share/jupyter/runtime/')
        lstk1 = [path + item for item in os.listdir(path) if 'kernel' in item]
    except FileNotFoundError:
        lstk1 = []

    try:
        path = '/run/user/1000/jupyter/'
        lstk2 = [path + item for item in os.listdir(path) if 'kernel' in item]
    except FileNotFoundError:
        lstk2 = []

    lstk = lstk1 + lstk2

    try:
        return {set_kid(item): {'value': item, 'type': 'Connected'} if is_runing(item) and item == cf
                else {'value': item, 'type': 'Alive'} if is_runing(item)
                else {'value': item, 'type': 'Died'} for item in lstk}
    except Exception:
        logger.error('No kernel available', exc_info=True)
        return {}


def print_kernel_list():
    """ Display kernel list. """
    klst = kernel_list()
    print('{:-^79}'.format('| List of available kernels |'))

    if not klst:
        print('{:^79}'.format('No kernel available'))
        print('{:^79}'.format('Last run of the daemon may have quit prematurely.'))
    else:
        for item in klst:
            print('{0[0]:71}{0[1]:>8}'.format(item))
    print(79*'-')


def print_kernel_dic():
    """ Display kernel list. """
    klst = kernel_dic()
    print('{:-^79}'.format('| List of available kernels |'))

    if not klst:
        print('{:^79}'.format('No kernel available'))
        print('{:^79}'.format('Last run of the daemon may have quit prematurely.'))
    else:
        for item in klst:
            print("{0[value]:71}{0[type]:>8}".format(klst[item]))
    print(79*'-')


def connect_kernel(cf):
    """ Connect a kernel. """

    if is_runing(cf):
        kc = BlockingKernelClient(connection_file=cf)
        # kc = AsyncKernelClient(connection_file=cf)
        kc.load_connection_file(cf)
        km = None

    else:
        # Kernel manager
        # km = manager.KernelManager(connection_file=cf)
        km = manager.AsyncKernelManager(connection_file=cf)
        km.start_kernel()
        # Kernel Client
        # kc = km.blocking_client()
        kc = km.client()

    init_kernel(kc)

    return km, kc


async def connect_kernel_as_manager(cf):
    """ Connect a kernel """

    # Kernel manager
    # km = manager.KernelManager(connection_file=cf)
    km = manager.AsyncKernelManager(connection_file=cf)
    await km.start_kernel()
    # Kernel Client
    # kc = km.blocking_client()
    kc = km.client()
    init_kernel(kc)

    return km, kc


def init_kernel(kc, backend='tk'):
    """ init communication. """

    backend = 'tk'

    kc.execute("import numpy as _np", store_history=False)
    kc.execute("import pandas as _pd", store_history=False)
    kc.execute("_np.set_printoptions(threshold={})".format(sys.maxsize), store_history=False)
    kc.execute("%matplotlib {}".format(backend), store_history=False)
    kc.execute("import cpyvke.utils.inspector as _inspect", store_history=False)


def find_and_kill_ipykernel_launcher(cmd):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.name() == 'python' and all(arg in proc.cmdline() for arg in cmd):
            proc.kill()

async def async_shutdown_kernel(cf):
    """ Shutdown a kernel based on its connection file. """

    km, kc = await connect_kernel_as_manager(cf)
    await km.shutdown_kernel(now=True)

    kernel_cmd = ['-m', 'ipykernel_launcher', '-f', cf]
    find_and_kill_ipykernel_launcher(kernel_cmd)

def shutdown_kernel(cf):
    asyncio.run(async_shutdown_kernel(cf))
    


# def shutdown_kernel(cf):
#     """ Shutdown a kernel based on its connection file. """

#     km, kc = connect_kernel_as_manager(cf)
#     # km.shutdown_kernel(now=True)
#     def shutdown():
#         kc.stop_channels()  # 停止通道
#         km.shutdown_kernel(now=True)
#         km.cleanup_resources()  # 清理資源

#     shutdown_thread = threading.Thread(target=shutdown)
#     shutdown_thread.start()


async def async_restart_kernel(cf):
    """ Restart a kernel based on its connection file. """

    km, kc = await connect_kernel_as_manager(cf)
    try:
        await km.start_kernel()
    except Exception:
        logger.error('Issue restarting kernel', exc_info=True)

def restart_kernel(cf):
    asyncio.run(async_restart_kernel(cf))


