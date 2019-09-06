#!/usr/bin/env python3
# @file
# @brief Example for connecting to menlosystemcore with the pywebchannel
#        library
# @author Olaf Mandel <o.mandel@menlosystems.com>
# @copyright Copyright 2019  Menlo Systems GmbH
# @par License
# Dual-licensed under LGPLv3 and GPLv2+
#
# LGPLv3:
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# GPLv2+:
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import asyncio
import enum
import json
import sys
import ssl
import urllib.parse
import websockets.client
from pywebchannel.async import QWebChannel

async def connect(url, user, password):
    # Generate transport
    ssl_opts = {}
    if urllib.parse.urlparse(url).scheme == 'wss':
        ssl_opts = { 'ssl': ssl.SSLContext() }
    transport = await websockets.client.connect(url, **ssl_opts)
    # Authenticate
    msg = {
        'user': user,
        'password': password
    }
    await transport.send(json.dumps(msg, separators=(',', ':')))
    # Check authentication result
    msg = json.loads(await transport.recv())
    if not msg['authenticated']:
        print('Authentication failed:', msg['error'], file=sys.stderr)
        await transport.close()
        return
    # Generate QWebChannel
    loop = asyncio.get_event_loop()
    init_future = loop.create_future()
    channel = QWebChannel(lambda channel:
        loop.call_soon_threadsafe(init_future.set_result, channel))
    # Read out messages in a task
    async def reader():
        while transport.open:
            try:
                msg = await transport.recv()
            except:
                if transport.open:
                    raise
                else:
                    break
            channel.message_received(msg)
    loop.create_task(reader())
    # Wrap transport so everything is sent via a task
    class TaskSendingTransport:
        def __init__(self, realTransport):
            self._realTransport = realTransport
        def send(self, msg):
            loop.create_task(self._safeSend(msg))
        async def close(self):
            await self._realTransport.close()
        async def _safeSend(self, msg):
            try:
                await self._realTransport.send(msg)
            except:
                if self._realTransport.open:
                    raise
    # Finish channel initialisation
    channel.connection_made(TaskSendingTransport(transport))
    await init_future
    return channel

def dump_objects(objects):
    internalQObjectObjects = [
        '_id',
        '_objectSignals',
        '_propertyCache',
        '_webChannel'
    ]
    # Iterate over all objects
    print('Objects:')
    for i in sorted(objects):
        print('-', i)
        # Generate lists
        obj = objects[i]
        enums = [k for k, v in vars(obj).items()
                 if isinstance(v, type(enum.IntEnum))]
        props = [k for k, v in vars(type(obj)).items()
                 if isinstance(v, property)]
        propUuids = {}
        for n in props:
            val = getattr(obj, n)
            if isinstance(val, dict):
                isMapOfObjects = True
                for v in val.values():
                    if not hasattr(v, '_id'):
                        isMapOfObjects = False
                if isMapOfObjects:
                    propUuids[n] = {k: v._id for k, v in val.items()}
            elif hasattr(val, '_id'):
                propUuids[n] = val._id
        methods = [k for k, v in vars(obj).items()
                   if hasattr(v, 'isQtMethod') and v.isQtMethod]
        signals = [k for k, v in vars(obj).items()
                   if issubclass(type(v), object)
                   and k not in internalQObjectObjects]
        # Print lists
        print('  Enums:')
        for j in sorted(enums):
            print('  -', j)
        print('  Properties:')
        for j in sorted(props):
            if j in propUuids:
                print('  -', j, ':', propUuids[j])
            else:
                print('  -', j)
        print('  Methods:')
        for j in sorted(methods):
            print('  -', j)
        print('  Signals:')
        for j in sorted(signals):
            print('  -', j)

def dump_system(syscmds):
    # Read three properties
    print('OS version:    ', syscmds.osVersion)
    print('Kernel version:', syscmds.kernelVersion)
    print('App version:   ', syscmds.applicationVersion)
    # Read something that has enum type
    for i in syscmds.AddressType:
        if syscmds.addressType == i:
            typeStr = i
    print('Address type:', syscmds.addressType, '=', typeStr)

async def show_log(log, lines):
    # Call a method
    msgs = await log.readLog(lines)
    for i in msgs:
        print("Log:", i)

    # Connect to a signal (though it won't be called in this example)
    log.logMessageReceived.connect(lambda msg: print("Log:", msg))

# main routine
if __name__ == '__main__':
    # Command line arguments and defaults
    cmdline = sys.argv[1:]
    url = cmdline[0] if len(cmdline) > 0 else 'ws://localhost/'
    user = cmdline[1] if len(cmdline) > 1 else 'guest'
    password = cmdline[2] if len(cmdline) > 2 else ''

    loop = asyncio.get_event_loop()
    # Connect to server
    channel = loop.run_until_complete(connect(url, user, password))
    if channel:
        # Show all exposed objects
        dump_objects(channel.objects)
        # Read properties
        dump_system(channel.objects['SystemCommands'])
        # Call method, connect to signal
        loop.run_until_complete(show_log(channel.objects['root'].log, 10))
        # Disconnect from server
        loop.run_until_complete(channel.transport.close())
