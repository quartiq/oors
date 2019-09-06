#!/usr/bin/env node
/**
 * @file
 * @brief Example for connecting to menlosystemcore with the menlosystemcore.js
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

var MenloSystemCore = require('menlosystemcore')

// main routine
if (require.main === module) {
  // Command line arguments and defaults
  var cmdline = process.argv.slice(2)
  var url = cmdline[0] || 'ws://localhost/'
  var user = cmdline[1] || 'guest'
  var password = cmdline[2] || ''

  core = new MenloSystemCore()
  // Connect to server
  core.connect(url, user, password)
  core.connectedChanged.connect(function (connected) {
    if (!connected) {
      return
    }
    // Show exposed system logic object
    console.log(core.objectInfo(core.systemLogic))
    // Show all exposed modules
    console.log(core.objectInfo(core.modules))
    // Read a few system properties
    console.log('Identity:      ', core.identity)
    console.log('OS version:    ', core.system.osVersion)
    console.log('Kernel version:', core.system.kernelVersion)
    console.log('App version:   ', core.system.applicationVersion)
    // Read something that has enum type
    console.log('Address type:', core.system.addressType, '=',
      core.enumNum2String(core.system.AddressType, core.system.addressType))
    // Connect to a signal (though it won't be called in this example)
    core.log.logMessageReceived.connect(function (msg) {
      console.log("Log:", msg)
    })
    // Call a method with one arg, print return value
    core.log.readLog(10, function(msgs) {
      for (var i in msgs) {
        console.log("Log:", msgs[i])
      }
      // Disconnect from server
      core.disconnect()
    })
  })
}
