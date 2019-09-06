#!/usr/bin/env python3

"""Example how to control the opticlock system"""

__author__ = "Olaf Mandel"
__email__ = "o.mandel@menlosystems.com"
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
from datetime import datetime
from menlosystemcore import MenloSystemCore
import random
import sys


async def main():
    # Command line arguments and defaults
    cmdline = sys.argv[1:]
    url = cmdline[0] if len(cmdline) > 0 else 'ws://localhost/'
    user = cmdline[1] if len(cmdline) > 1 else 'guest'
    password = cmdline[2] if len(cmdline) > 2 else ''
    if '/' not in url:
        url = 'wss://{}/core/'.format(url)
        print('Modifying url to', url)

    core = MenloSystemCore()
    # Connect to server
    await core.connect(url, user, password)

    # Always disconnect at the end to guard against
    # https://bugs.python.org/issue36709 .
    # Here we do this by using the MenloSystemCore instance as an async context
    # manager. Alternatively, ensure that "await core.disconnect()" is always
    # called before the event loop is closed.
    async with core:

        # switch on the system
        core.systemLogic.mode = core.systemLogic.Modes.TurnOn
        # display current system mode
        mode = core.systemLogic.mode
        print('Current mode:', int(mode), '=', mode)

        # check if there was a error (not automatically fixable)
        if core.systemLogic.errorMessage:
            print('Error detected:', core.systemLogic.errorMessage)
        else:
            print('No error found')

        # check if system is complete operational
        print('Currently operational:', core.systemLogic.isOperational)

        # set default target frequency
        core.systemLogic.frequencyTarget = 344179529654654
        # display current target frequency
        print('Current target frequency (not needed for'
            + ' supplyWlmFrequencyError):', core.systemLogic.frequencyTarget,
            'Hz')

        # check if wavemeter should provide readings
        print('Wavemeter desired:', core.systemLogic.wantWlmReadout)
        # provide wavemeter reading, anyway (simulated): first absolute
        wlmFrequency = random.normalvariate(344179529.655e6, 1e6)
        print('Supplying absolute WLM reading:', wlmFrequency, 'Hz')
        core.systemLogic.supplyWlmFrequency(wlmFrequency)
        # and now as an error from the target frequency (simulated):
        wlmFrequencyError = random.normalvariate(0, 1e6)
        print('Supplying WLM error (reading - target):',
              wlmFrequencyError, 'Hz')
        core.systemLogic.supplyWlmFrequencyError(wlmFrequencyError)

        # initialize frequency management settings (simulated)
        fOffs = random.uniform(-1e6, 1e6)
        fDrift = random.normalvariate(0, 1e1)
        print('Cavity drift compensation:')
        print('  frequency:', fOffs, 'Hz')
        print('  slope:    ', fDrift, 'Hz/s')
        core.systemLogic.frequencyOffset = fOffs
        core.systemLogic.driftSlope = fDrift
        print('After one second of drifting...')
        await asyncio.sleep(1)
        print('  frequency:', core.systemLogic.frequencyOffset, 'Hz')

        # Supply the df measured against the clock (simulated)
        df = random.normalvariate(0, 0.1)
        print('Measured frequency error against clock:', df, 'Hz')
        core.systemLogic.frequencyError = df
        # from now on, this gets integrated until a different value is set

        # offset the frequency for the clock algorithm
        fShift = 5.1e6
        print('Shift the clock laser by:', fShift, 'Hz')
        core.systemLogic.frequencyFastOffset = fShift


if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass

