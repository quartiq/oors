/**
 * @file
 * @brief Library to connect to a MenloSystemCore instance remotely
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

'use strict';

(function (global) {
  // get dependencies in a portable way
  var QWebChannel
  var WebSocket
  if (typeof require === 'undefined') {
    QWebChannel = { QWebChannel: global.QWebChannel }
    WebSocket = function (url, options) { return new global.WebSocket(url) }
  } else {
    QWebChannel = require('qwebchannel')
    WebSocket = require('ws')
  }

  // @class MenloSystemCore
  // @brief Proxy for an instance of MenloSystemCore (the program)
  //
  // An instance of this class only needs to be connected to via the connect()
  // method and after that is achieved, all remote properties of the program
  // are available for inspection or remote-control.
  //
  // There are no constructor arguments.
  var MenloSystemCore = function () {
    var core = this
    var channel = null
    var connected = false
    var connectedCbs = []

    var mirrorProp = function (obj, name, defaultValue, access) {
      Object.defineProperty(obj, name, {
        enumerable: true,
        get: function () {
          if (connected) {
            var res = access(channel.objects)
            if (typeof res === 'undefined') {
              return defaultValue
            } else {
              return res
            }
          } else {
            return defaultValue
          }
        }
      })
    }

    var setConnected = function (val) {
      connected = val
      for (var i in connectedCbs) {
        connectedCbs[i](connected)
      }
    }

    // @brief SystemLogic object
    mirrorProp(this, 'systemLogic', null, function (objs) {
      return objs.root.systemLogic
    })
    // @brief identity string
    mirrorProp(this, 'identity', '', function (objs) {
      return objs.root.identity
    })
    // @brief Modules map
    mirrorProp(this, 'modules', {}, function (objs) {
      return objs.root.modules
    })
    // @brief SettingsManager object
    mirrorProp(this, 'settings', null, function (objs) {
      return objs.root.settings
    })
    // @brief LogExporter object
    mirrorProp(this, 'log', null, function (objs) {
      return objs.root.log
    })
    // @brief SystemCommands object
    mirrorProp(this, 'system', null, function (objs) {
      return objs.SystemCommands
    })

    // @brief Connection status
    Object.defineProperty(this, 'connected', {
      enumerable: true,
      get: function () {
        return connected
      }
    })

    // @brief Change-signal for the connection status
    this.connectedChanged = {
      connect: function (callback) {
        if (typeof callback !== 'function') {
          console.error('Bad callback given to connect to signal '
            + 'connectedChanged')
          return
        }
        connectedCbs.push(callback)
      },
      disconnect: function (callback) {
        if (typeof callback !== 'function') {
          console.error('Bad callback given to disconnect from signal '
            + 'connectedChanged')
          return
        }
        var idx = connectedCbs.indexOf(callback)
        if (idx === -1) {
            console.error('Cannot find connection of signal connectedChanged '
              + 'to ' + callback.name)
            return
        }
        connectedCbs.splice(idx, 1)
      }
    }

    // @brief Connect to a remote MenloSystemCore server
    // @param url  URL of the server, must have ws or wss scheme
    //             (default = 'ws://localhost/')
    // @param user Name of the user to connect as (default = 'guest')
    // @param password Password for authentication (default = '')
    // @note The connection is asynchronous: connect to the #connectedChanged
    //       signal to learn when the connection succeeded.
    this.connect = function (url, user, password) {
      // Default values
      url = url || 'ws://localhost/'
      user = user || 'guest'
      password = password || ''
      // Sequencing check
      if (connected) {
        console.error('Already connected to a server')
        return
      }
      // Instantiate transport
      var transport = new WebSocket(url, {rejectUnauthorized: false})
      transport.onopen = function () {
        // Authenticate
        var msg = {
          user: user,
          password: password
        }
        transport.send(JSON.stringify(msg))
      }
      transport.onmessage = function (str) {
        // Only execute this once
        transport.onmessage = null
        // Only interested in the data
        if (typeof str === 'object' && typeof str.data === 'string') {
          str = str.data
        }
        // Check authentication result
        var msg
        try {
          msg = JSON.parse(str)
        } catch(e) {
          console.error('Invalid response received:', str)
          transport.close()
          setConnected(false)
          return
        }
        if (!msg.authenticated) {
          console.error('Authentication failed:', msg.error)
          transport.close()
          setConnected(false)
          return
        }
        // Generate QWebChannel
        channel = new QWebChannel.QWebChannel(transport, function(ch) {
          setConnected(true)
        })
      }
      transport.onerror = function (err) {
        console.error(err)
      }
      transport.onclose = function () {
        setConnected(false)
      }
    }

    // @brief Disconnect from the remote MenloSystemCore server
    // @note The disconnection is asynchronous: connect to the #connectedChanged
    //       signal to learn when the connection is broken
    this.disconnect = function () {
      if (!connected) {
        console.error('Not currently connected to a server')
        return
      }
      channel.transport.close()
    }

    // @brief Access to the low-level QWebChannel
    // @note Try not to disconnect or otherwise interfere with the transport.
    Object.defineProperty(this, 'webChannel', {
      enumerable: true,
      get: function () {
        return webChannel
      }
    })

    // @brief Helper to convert a number to the enum key
    // @param type The enum-type where to do the conversion
    // @param value The numeric value to convert
    // @return The enum key (string) or a number string if not valid
    this.enumNum2String = function (type, value) {
      for (var i in type) {
        if (value === type[i]) {
          return i
        }
      }
      return value
    }

    // @brief Helper to convert an enum key to a number
    // @param type The enum-type where to do the conversion
    // @param key The enum key to convert
    // @return The numeric value or first entry if not valid
    this.enumString2Num = function (type, key) {
      if (key in type) {
        return type[key]
      } else {
        return type[Object.keys(type)[0]]
      }
    }

    // @brief Extracts information about QObjects
    // @param obj The object to examine, may also be an array or a map
    // @return Information about enums, properties, methods and signals
    this.objectInfo = function (obj) {
      if (typeof obj !== 'object' ) {
        return
      } else if (obj === null) {
        return null
      } else if (Array.isArray(obj)) {
        return obj.map(core.objectInfo)
      } else if (obj.constructor.name !== 'QObject') {
        var res = {}
        for (var i in obj) {
          res[i] = core.objectInfo(obj[i])
        }
        return res
      } else {
        var internalQObjectNames = [
          'unwrapQObject',
          'unwrapProperties',
          'propertyUpdate',
          'signalEmitted'
        ]
        var res = {}
        var rawKeys = Object.keys(obj)
        var keys = rawKeys.filter(function (name) {
          return name[0] !== '_' && !internalQObjectNames.includes(name)
        })
        res.properties = Object.getOwnPropertyNames(obj).filter(
          function (name) {
            return !rawKeys.includes(name)
          })
        res.methods = keys.filter(function (name) {
          return typeof obj[name] === 'function'
        })
        var others = keys.filter(function (name) {
          return !res.methods.includes(name)
        })
        res.signals = others.filter(function (name) {
          return typeof obj[name].connect === 'function' &&
                 typeof obj[name].disconnect === 'function'
        })
        res.enums = others.filter(function (name) {
          return !res.signals.includes(name)
        })
        return res
      }
    }
  }

  // @brief Restores the original MenloSystemCore from he global namespace
  // @return the MenloSystemCore of this module
  //
  // This is intended in the (unlikely) case that this module is used in the
  // browser and another object called MenloSystemCore already exists.
  MenloSystemCore.noConflict = function () {
    global.MenloSystemCore = globalMenloSystemCore
    return MenloSystemCore
  }
  var globalMenloSystemCore = global.MenloSystemCore

  // Now export the MenloSystemCore class, either for NodeJS or the browser
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = MenloSystemCore
  } else {
    global.MenloSystemCore = MenloSystemCore
  }
})(this)
