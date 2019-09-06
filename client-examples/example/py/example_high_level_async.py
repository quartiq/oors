#!/usr/bin/env python3

""" High-level example for connecting to a remote MenloSystemCore instance with
    the menlosystemcore.py module.
"""

__author__ = "Arno Rehn"
__email__ = "a.rehn@menlosystems.com"
__copyright__ = "Copyright 2019 Menlo Systems GmbH"
__license__ = "Dual-licensed under LGPLv3 and GPLv2+"

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
from menlosystemcore import MenloSystemCore
import sys


async def main():
    # Command line arguments and defaults
    cmdline = sys.argv[1:]
    url = cmdline[0] if len(cmdline) > 0 else 'ws://localhost/'
    user = cmdline[1] if len(cmdline) > 1 else 'guest'
    password = cmdline[2] if len(cmdline) > 2 else ''

    core = MenloSystemCore()
    # Connect to server
    await core.connect(url, user, password)

    # Always disconnect at the end to guard against
    # https://bugs.python.org/issue36709 .
    # Here we do this by using the MenloSystemCore instance as an async context
    # manager. Alternatively, ensure that "await core.disconnect()" is always
    # called before the event loop is closed.
    async with core:
        # Show exposed system logic object
        print('SystemLogic:', core.systemLogic)
        # Show all exposed modules
        print('Modules:')
        for name, obj in core.modules.items():
            print("  -", name, "=>", obj)
        # Read a few system properties
        print('Identity:      ', core.identity)
        print('OS version:    ', core.system.osVersion)
        print('Kernel version:', core.system.kernelVersion)
        print('App version:   ', core.system.applicationVersion)
        # Read something that has enum type
        print('Address type:', core.system.addressType, '=',
            str(core.system.AddressType(core.system.addressType)))
        # Call a method, print return value
        msgs = await core.log.readLog(10)
        for i in msgs:
            print("Log:", i)
        # Connect to a signal (though it won't be called in this example)
        core.log.logMessageReceived.connect(lambda msg: print("Log:", msg))

        # Show interactive help screen with methods, properties, signals
        input('Press <ENTER> to show the interactive help for the system'
            ' module.')
        help(core.system)

        # Wait 2 minutes for something to happen on the log
        timeout = 120
        print("Now waiting {}s for new log messages... Press Ctrl+C to abort."
            .format(timeout))
        await asyncio.sleep(timeout)


if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass

