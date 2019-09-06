#!/usr/bin/env python3

# Copyright 2019 Menlo Systems GmbH
# Copyright 2019 QUARTIQ GmbH
# Dual-licensed under LGPLv3 and GPLv2+

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
import os


MOCK = bool(os.getenv("OPTICLOCK_MOCK"))
assert MOCK


async def main():
    core = MenloSystemCore()
    await core.connect(sys.argv[1] or "wss://localhost/core/", user="guest", password="")
    async with core:
        if not MOCK:
            core.systemLogic.mode = core.systemLogic.Modes.TurnOn
        if not MOCK:
            core.systemLogic.supplyWlmFrequencyError(0.)
            # core.systemLogic.frequencyOffset = 0.
            # core.systemLogic.driftSlope = 0.
            core.systemLogic.frequencyError = 0.
            core.systemLogic.frequencyFastOffset = 0.
        while True:
            print("mode:", core.systemLogic.mode)
            print("errorMessage:", core.systemLogic.errorMessage)
            print("isOperational:", core.systemLogic.isOperational)
            print("wantWlmReadout:", core.systemLogic.wantWlmReadout)
            print("frequencyOffset:", core.systemLogic.frequencyOffset)
            print("driftSlope:", core.systemLogic.driftSlope)
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        tasks = asyncio.gather(main())
        loop.run_until_complete(tasks)
    except KeyboardInterrupt:
        print("Cancelling")
        tasks.cancel()
        loop.run_forever()
        tasks.exception()
    finally:
        loop.close()
