# pyDriveWire
Python Implementation of DriveWire 4

PyDriveWire is a nearly complete DriveWire4 Server written in Python.  The goal is to eventually implement all of the features available.  The server also implements additional features that are not available in DriveWire4.

Features
--------
* (new for v0.3) Experimental printing support
* (new for v0.3) New command line parameters, see the "Run It" section for details
* Connections to serial ports at all supported baud rates: 38400, 57600, 115200, 230400, 460800, 921600
* Listen for incoming connection on any TCP port with a default of 65504
* Ability to make outgoing TCP connections for serial-net converters
* Disks to be mounted can be specified on the command line
* Interactive CLI allowing all dw commands to be run
* Support for DriveWire 4 virtual ports
   * `dw` commmands over vport
   * `AT` Modem-style connections
   * Outbound connections with `ATD`/`ATDT` or `tcp connect`
   * Inbound vports via `tcp listen/join/kill` commands


Notable Missing Features
------------------------
* Support for mounting disks via URL/URI
* MIDI
* Experimental text-only support in v0.3
* OS9 `/Z` console windows


Requirements
------------
* pypy -- For maximum performance it is recommended to run the server with
pypy.  pypy is a Python interpreter that does JIT compilation and results in
greatly increased speed
* pyserial -- Install using pip

Supported Operating Systems
---------------------------
* Any OS where you can run Python, including but not limited to:
* Linux
* macOS
* Windows support is _PRELIMINARY_.  Minimal testing has been done but it should work


Installation (Linux/macOS/UNIX)
------------
* Download Latest: [https://github.com/n6il/pyDriveWire/releases](https://github.com/n6il/pyDriveWire/releases)
* Mac: `brew install pypy; pypy -m pip install pyserial`
* Ubuntu: `apt-get install pypy; pypy -m pip install pyserial`

_Experimental Printing Support_

* `pypy -m pip install reportlab`

Run It
------
    usage: pyDriveWire.py [-h] [-s SPEED] [-a] [-c] [-H HOST] [-p PORT] [-R]
                          [-x EXPERIMENTAL]
                          FILE [FILE ...]
    
    pyDriveWire Server v0.3
    
    positional arguments:
      FILE                  list of files
    
    optional arguments:
      -h, --help            show this help message and exit
      -s SPEED, --speed SPEED
                            Serial port speed
      -a, --accept          Accept incoming TCP connections on --port
      -c, --connect         Connect to TCP connections --host --port
      -H HOST, --host HOST  Hostname/IP
      -p PORT, --port PORT  Port to use
      -R, --rtscts          Serial: Enable RTS/CTS Flow Control
      -x EXPERIMENTAL       experimental options

Examples:

* Serial Port: `./pyDriveWire -s 115200 -p /dev/tty.usbserial /tmp/nos96809l2_becker.dsk`
* Listen for TCP connections on port 65504: `./pyDriveWire -a -p 65504 /tmp/nos96809l2_becker.dsk`
* Establish outbound TCP connection: `./pyDriveWire  -c -H 127.0.0.1 -p 23 /tmp/nos96809l2_becker.dsk`
* Experimental Printing support: `./pyDriveWire -x printer -a -p 65504 /tmp/nos96809l2_becker.dsk`


Experimental Printing Support
---------------------
pyDriveWire v0.3 includes experimental printing support.  The `-x printer` command line option enables it.  Currently this only suports printing text, and the out is rendered into a PDF.

_Prerequisites_

Printing support requires the reportlab module.  This module can be installed with pip:

    pypy -m pip install reportlab

_Use_

Most of the standard Nitros9 DriveWire builds have printing support built in.  Any program that uses the standard `/P` printing device will work just fine.  A simple example for testing:

    dir >/P

The console log will explain where the output PDF went:

    DWServer: Enabling experimental printing support
    Printing: opening print buffer: /var/folders/1y/cjrxv35d76bc54myg7hy7k1c0000gn/T/tmp2zG0Pb.txt
    Printing to: /var/folders/1y/cjrxv35d76bc54myg7hy7k1c0000gn/T/tmpWdKRQY.pdf
    Printing: closing print buffer: /var/folders/1y/cjrxv35d76bc54myg7hy7k1c0000gn/T/tmp2zG0Pb.txt


Supported DW Commands
---------------------
* `dw disk` 
	* `dw disk show`
	* `dw disk insert 0 <file>`
	* `dw disk eject 0`
	* `dw disk reset 0` -- (re-open)
* `dw port`
	* `dw port show`
	* `dw port close <n>`
*  `dw server`
	* `dw server instance`
	* `dw server dir [<path>]`
	* `dw server list <file>`
* `tcp` commands
	* `tcp connect <host> <port>`
	* `tcp listen <port> ...` -- Remainder of options ignored
	* `tcp join <channel>`
	* `tcp kill <channel>`
* AT Commands
   * `ATD<host>:<port>`
   * `ATDT<host>:<port>`
   * `ATE`
   * `ATH`
   * `ATI`
   * `ATO`
   * `ATZ`
* Debugging commands
   * `dw port debug <n> [true/false]`
	* `dw server debug [true/false]`
	* `dw server dump`
	* `dw server timeout <s>`

