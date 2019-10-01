conda create -n menlo python=3.5 pyqt=5.6
conda install -c conda-forge websockets
pip install git+https://github.com/MenloSystems/pywebchannel.git


async def main():
        print(list(core.modules))
        print(info(core.settings))
        # print(info(core.modules["DDS"]))
        msgs = await core.log.readLog(10)
        for i in msgs:
            print("Log:", i)
        core.log.logMessageReceived.connect(log)
        sl = core.systemLogic
        # sl.isOperationalChanged.connect(isOperational_cb)
        # sl.wantWlmReadoutChanged.connect(wantWlmReadout_cb)
        if not MOCK:
            sl.mode = sl.Modes.TurnOn
            sl.supplyWlmFrequencyError(0.)
            # sl.frequencyOffset = 348.16e6.
            # sl.driftSlope = 0.
            # sl.frequencyError = 0.
            # sl.frequencyFastOffset = 0.
        while True:
            # sl.supplyWlmFrequencyError(0.)
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
