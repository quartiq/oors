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

import enum
import json
import ssl
import sys
from websocket import WebSocketApp
from pywebchannel import QWebChannel

def connect(url, user, password, cb):
    # Generate QWebChannel: result available via callback
    channel = QWebChannel(cb)
    def open(transport):
        # Authenticate
        msg = {
            'user': user,
            'password': password
        }
        transport.send(json.dumps(msg, separators=(',', ':')))
    def message(transport, msgstr):
        # Check authentication result
        msg = json.loads(msgstr)
        if not msg['authenticated']:
            print('Authentication failed:', msg['error'], file=sys.stderr)
            transport.close()
            return
        # Overwrite this function, replace with a connection to the channel
        transport.on_message = lambda transport, msgstr: (
            channel.message_received(msgstr))
        channel.connection_made(transport)
    # Generate transport, return it so caller can execute run_forever
    return WebSocketApp(url,
        on_open=open,
        on_message=message,
        on_close=lambda transport: channel.connection_closed(),
        on_error=lambda transport, err: print(err, file=sys.stderr))

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

def show_log(log, lines, cb=None):
    # Call a method with one arg, print return value
    def dump_log(msgs):
        for i in msgs:
            print("Log:", i)
        if cb:
            cb()
    log.readLog(lines, dump_log)
    # Connect to a signal (though it won't be called in this example)
    log.logMessageReceived.connect(lambda msg: print("Log:", msg))

def disconnect(channel):
    channel.transport.close()
    # workaround: websocket.WebSocketApp calls on_close too late, so inform
    # QWebChannel explicitly
    channel.connection_closed()

# main routine
if __name__ == '__main__':
    # Command line arguments and defaults
    cmdline = sys.argv[1:]
    url = cmdline[0] if len(cmdline) > 0 else 'ws://localhost/'
    user = cmdline[1] if len(cmdline) > 1 else 'guest'
    password = cmdline[2] if len(cmdline) > 2 else ''

    def run(channel):
        # Show all exposed objects
        dump_objects(channel.objects)
        # Read properties
        dump_system(channel.objects['SystemCommands'])
        # Call method, connect to signal
        show_log(channel.objects['root'].log, 10,
            # Disconnect from server
            # Need to do this in a callback after the last reply was received
            lambda: disconnect(channel))
    # Connect to server
    connect(url, user, password, run).run_forever(
        sslopt={"cert_reqs": ssl.CERT_NONE})
