Python example
==============

Simple example that shows connection to a server and a few operations.

Preparation
-----------

    virtualenv -p python3 env
    source env/bin/activate
    pushd ../../external/py/pywebchannel
    python3 setup.py install
    popd
    pushd ../../libs/py
    pip install -r requirements.txt
    python3 setup.py install
    popd
    pip install -r requirements.txt
    deactivate

Running
-------

    source env/bin/activate
    ./example_low_level_async.py wss://1.2.3.4/core/
    ./example_low_level_plain.py wss://5.6.7.8/core/
    deactivate
