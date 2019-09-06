# -*- coding: utf-8 -*-


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


from pywebchannel.asyncronous import QWebChannel, QObject
from pywebchannel.qwebchannel import Signal
from websockets.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed
import asyncio
import collections.abc
import enum
import inspect
import json
import ssl
import sys
import urllib.parse


class AuthenticationError(Exception):

    def __init__(self, errorString):
        self.errorString = errorString

    def __str__(self):
        return self.errorString


class ReadOnlyDotDict(collections.abc.Mapping):

    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    __getattr__ = __getitem__

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)


class Signal:

    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def disconnect(self, callback):
        self._callbacks.remove(callback)

    def emit(self, *args, **kwargs):
        for cb in self._callbacks:
            cb(*args, **kwargs)


class MenloSystemCore:
    """ High-level interface class for a remote MenloSytemCore instance
    """

    def __init__(self):
        self._webChannel = None
        self._moduleMapping = None
        self._signal_connectedChanged = Signal()
        self._closeCode = None
        self._closeReason = None
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()

    @property
    def closeCode(self):
        return self._closeCode


    @property
    def closeReason(self):
        return self._closeReason


    @property
    def connected(self):
        return self._webChannel is not None


    @property
    def connectedChanged(self):
        return self._signal_connectedChanged


    @property
    def webChannel(self):
        """ The currently connected QWebChannel instance
        """
        return self._webChannel


    @property
    def systemLogic(self):
        """ The system logic object exported by the MenloSystemCore instance
        """
        if not self._webChannel:
            return
        return self._webChannel.objects["root"].systemLogic


    @property
    def identity(self):
        """ The identity string exported by the MenloSystemCore instance
        """
        if not self._webChannel:
            return
        return self._webChannel.objects["root"].identity


    @property
    def modules(self):
        """ All modules exported by the MenloSystemCore instance
        """
        if not self._webChannel:
            return
        if not self._moduleMapping:
            self._moduleMapping = ReadOnlyDotDict(
                self._webChannel.objects["root"].modules)

        return self._moduleMapping


    @property
    def settings(self):
        """ The settings manager exported by the MenloSystemCore instance
        """
        if not self._webChannel:
            return
        return self._webChannel.objects["root"].settings


    @property
    def log(self):
        """ The log interface exported by the MenloSystemCore instance
        """
        if not self._webChannel:
            return
        return self._webChannel.objects["root"].log


    @property
    def system(self):
        """ The system interface exported by the MenloSystemCore instance
        """
        if not self._webChannel:
            return
        return self._webChannel.objects["SystemCommands"]


    async def disconnect(self):
        """ Disconnects from the MenloSystemCore instance
        """
        if not self._webChannel:
            return

        await self._webChannel.transport.close()

        # Guard against "parallel" disconnects
        if not self._webChannel:
            return

        del self._webChannel
        self._webChannel = None
        self._moduleMapping = None
        self.connectedChanged.emit(False)


    async def connect(self, url=None, user=None, password=None, loop=None):
        """ Coroutine. Connects to a MenloSystemCore instance at url

        The values of user and password can override the username and password
        given in url. Specify event loops other than the default in the loop
        parameter.

        Throws exceptions if the connection can't be established.
        """
        await self.disconnect()

        self._closeCode = None
        self._closeReason = None

        if loop is None:
            loop = asyncio.get_event_loop()

        # Create transport
        ssl_opts = {}
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme == 'wss':
            ssl_opts = { 'ssl': ssl.SSLContext() }

        transport = await ws_connect(url, **ssl_opts, loop=loop)

        # If no username or password are provided, fall back to those
        # specified in the URL
        if user is None:
            user = parsed_url.username
        if password is None:
            password = parsed_url.password

        # If we still don't have anything, default to "guest" + empty pw
        if user is None:
            user = "guest"
        if password is None:
            password = ""

        # Authenticate
        msg = {
            'user': user,
            'password': password
        }

        await transport.send(json.dumps(msg, separators=(',', ':')))

        # Check authentication result
        msg = json.loads(await transport.recv())

        if not msg['authenticated']:
            await transport.close()
            raise AuthenticationError(msg['error'])

        # Create QWebChannel
        self._webChannel = QWebChannel()

        # Read out messages in a task
        async def reader():
            while transport.open:
                try:
                    msg = await transport.recv()
                except ConnectionClosed as e:
                    self._closeCode = e.code
                    self._closeReason = e.reason
                    await self.disconnect()
                    break
                except:
                    if not transport.open or loop.is_closed():
                        break
                    else:
                        raise
                self._webChannel.message_received(msg)

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

        # Finish self._webChannel initialisation
        self._webChannel.connection_made(TaskSendingTransport(transport))

        await self._webChannel
        self.connectedChanged.emit(True)

        return self
