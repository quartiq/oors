#!/usr/bin/env node
/**
 * @file
 * @brief Example for connecting to menlosystemcore with the qwebchannel.js
 *        library
 * @author Olaf Mandel <o.mandel@menlosystems.com>
 * @copyright Copyright 2019  Menlo Systems GmbH
 * @par License
 * Dual-licensed under LGPLv3 and GPLv2+
 *
 * LGPLv3:
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 * GPLv2+:
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */

var QWebChannel = require('qwebchannel')
var WebSocket = require('ws')

function connect(url, user, password, cb) {
  // Generate transport
  var transport = new WebSocket(url, {rejectUnauthorized: false})
  transport.on('open', function () {
    // Authenticate
    var msg = {
      user: user,
      password: password
    }
    transport.send(JSON.stringify(msg))
  })
  transport.once('message', function (str) {
    // Check authentication result
    var msg = JSON.parse(str)
    if (!msg.authenticated) {
      console.error('Authentication failed:', msg.error)
      transport.close()
      return
    }
    // Generate QWebChannel: result available via callback
    new QWebChannel.QWebChannel(transport, cb)
  })
  transport.on('error', function (err) {
    console.error(err)
  })
}

function dump_objects(objects) {
  var internalQObjectNames = [
    'unwrapQObject',
    'unwrapProperties',
    'propertyUpdate',
    'signalEmitted'
  ]
  // Iterate over all objects
  console.log('Objects:')
  for (var i in objects) {
    console.log('-', i)
    // Generate lists
    var obj = objects[i]
    var rawKeys = Object.keys(obj)
    var keys = rawKeys.filter(function (name) {
      return name[0] !== '_' && !internalQObjectNames.includes(name)
    })
    var props = Object.getOwnPropertyNames(obj).filter(function (name) {
      return !rawKeys.includes(name)
    })
    var propUuids = {}
    for (var j in props) {
      var val = obj[props[j]]
      if (val === null) {
        continue
      }
      if (typeof val === 'object' && Object.getOwnPropertyNames(val)
        .reduce(function (acc, value) {
          return acc &&
            Object.getOwnPropertyNames(val[value]).includes('__id__')
        }, true)) {
        var pretty = {}
        Object.getOwnPropertyNames(val).map(function (value) {
          pretty[value] = val[value].__id__
        })
        propUuids[props[j]] = pretty
      } else if (Object.getOwnPropertyNames(val).includes('__id__')) {
        propUuids[props[j]] = val.__id__
      }
    }
    var methods = keys.filter(function (name) {
      return typeof obj[name] === 'function'
    })
    var others = keys.filter(function (name) {
      return !methods.includes(name)
    })
    var signals = others.filter(function (name) {
      return typeof obj[name].connect === 'function' &&
             typeof obj[name].disconnect === 'function'
    })
    var enums = others.filter(function (name) {
      return !signals.includes(name)
    })
    // Print lists
    console.log('  Enums:')
    for (var j in enums) {
      console.log('  -', enums[j])
    }
    console.log('  Properties:')
    for (var j in props) {
      if (props[j] in propUuids) {
        console.log('  -', props[j], ':', propUuids[props[j]])
      } else {
        console.log('  -', props[j])
      }
    }
    console.log('  Methods:')
    for (var j in methods) {
      console.log('  -', methods[j])
    }
    console.log('  Signals:')
    for (var j in signals) {
      console.log('  -', signals[j])
    }
  }
}

function dump_system(syscmds) {
  // Read three properties
  console.log('OS version:    ', syscmds.osVersion)
  console.log('Kernel version:', syscmds.kernelVersion)
  console.log('App version:   ', syscmds.applicationVersion)
  // Read something that has enum type
  var typeStr
  for (var i in syscmds.AddressType) {
    if (syscmds.addressType === syscmds.AddressType[i]) {
      typeStr = i
    }
  }
  console.log('Address type:', syscmds.addressType, '=', typeStr)
}

function show_log(log, lines) {
  // Call a method with one arg, print return value
  log.readLog(lines, function(msgs) {
    for (var i in msgs) {
      console.log("Log:", msgs[i])
    }
  })
  // Connect to a signal (though it won't be called in this example)
  log.logMessageReceived.connect(function (msg) {
    console.log("Log:", msg)
  })
}

exports.connect = connect
exports.dump_objects = dump_objects
exports.dump_system = dump_system
exports.show_log = show_log

// main routine
if (require.main === module) {
  // Command line arguments and defaults
  var cmdline = process.argv.slice(2)
  var url = cmdline[0] || 'ws://localhost/'
  var user = cmdline[1] || 'guest'
  var password = cmdline[2] || ''

  // Connect to server
  connect(url, user, password, function (channel) {
    // Show all exposed objects
    dump_objects(channel.objects)
    // Read properties
    dump_system(channel.objects.SystemCommands)
    // Call method, connect to signal
    show_log(channel.objects.root.log, 10)
    // Disconnect from server
    channel.transport.close()
  })
}
