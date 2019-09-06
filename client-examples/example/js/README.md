JavaScript example
==================

Simple example that shows connection to a server and a few operations.

Preparation
-----------

    pushd ../../libs/js
    npm i
    popd
    npm i

Running
-------

    ./example_low_level.js wss://1.2.3.4/core/
    ./example_high_level.js wss://1.2.3.4/core/

Browser
-------

The browser example is a single file `example-browser.html` that needs
to reside in the document-root of the device together with the two
libraries `qwebchannel.js` and `menlosystemcore.js`.
