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
import enum
from menlosystemcore import MenloSystemCore
import sys
import os


MOCK = bool(os.getenv("OPTICLOCK_MOCK"))
# assert MOCK


def info(obj):
    return dict(
        enums=[k for k, v in vars(obj).items()
                if isinstance(v, type(enum.IntEnum))],
        props=[k for k, v in vars(type(obj)).items()
                if isinstance(v, property)],
        methods=[k for k, v in vars(obj).items()
                if hasattr(v, 'isQtMethod') and v.isQtMethod],
        signals=[k for k, v in vars(obj).items()
                if issubclass(type(v), object)
                and k not in
                ['_id', '_objectSignals', '_propertyCache', '_webChannel']]
    )


async def main():
    core = MenloSystemCore()
    await core.connect(sys.argv[1] or "wss://localhost/core/", user="guest", password="")
    async with core:
        print(core.identity)
        print(list(core.modules))
        print(info(core.settings))
        # print(info(core.modules["DDS"]))
        msgs = await core.log.readLog(10)
        for i in msgs:
            print("Log:", i)
        core.log.logMessageReceived.connect(log)
        sl = core.systemLogic
        sl.isOperationalChanged.connect(isOperational_cb)
        sl.wantWlmReadoutChanged.connect(wantWlmReadout_cb)
        if not MOCK:
            sl.mode = sl.Modes.TurnOn
        if not MOCK:
            sl.supplyWlmFrequencyError(0.)
            # sl.frequencyOffset = 348.16e6.
            # sl.driftSlope = 0.
            # sl.frequencyError = 0.
            # sl.frequencyFastOffset = 0.
        while True:
            sl.supplyWlmFrequencyError(0.)
            # sl.frequencyOffset = 348.16e6.
            print("mode:", sl.mode)
            print("errorMessage:", sl.errorMessage)
            print("isOperational:", sl.isOperational)
            print("wantWlmReadout:", sl.wantWlmReadout)
            print("frequencyOffset:", sl.frequencyOffset)
            print("frequencyError:", sl.frequencyError)
            print("frequencyFastOffset:", sl.frequencyFastOffset)
            print("driftSlope:", sl.driftSlope)
            await asyncio.sleep(1)


def isOperational_cb(v):
    print("isOperational", v)


def wantWlmReadout_cb(v):
    print("wantWlmReadout", v)


def log(v):
    print("log", v)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        tasks = asyncio.gather(main())
        loop.run_until_complete(tasks)
    except KeyboardInterrupt:
        print("Cancelling")
        tasks.cancel()
        try:
            loop.run_until_complete(tasks)
        except asyncio.CancelledError:
            pass
        # loop.run_forever()
        tasks.exception()
    finally:
        loop.close()
