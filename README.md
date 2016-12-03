# pyDriveWire
Python Implementation of DriveWire 4

pyDriveWire is a Python implementation of the DriveWire 4 protocol.  The goal is to eventually implement all of the features available.  The server also implements additional features that are not available in DriveWire4.

Features
--------
* Connections to serial ports at all supported baud rates: 38400, 57600, 115200, 230400, 460800, 921600
* Listen for incoming connection on any TCP port with a default of 65504
* Ability to make outgoing TCP connections for serial-net converters
* Disks to be mounted can be specified on the command line
* Interactive console allowing all dw commands to be run
* Support for DriveWire 4 virtual ports
   * `dw` commmands over vport
   * `AT` Modem-style connections
   * Outbound connections with `ATD`/`ATDT` or `tcp connect`
   * Inbound vports via `tcp listen/join/kill` commands


Notable Missing Features
------------------------
* Support for mounting disks via URL/URI
* MIDI
* Printing
* OS9 `/Z` console windows


Requirements
------------
* pypy -- For maximum performance it is recommended to run the server with
pypy.  pypy is a Python interpreter that does JIT compilation and results in
greatly increased speed
* pyserial -- Install using pip


Installation
------------
* `git clone https://github.com/n6il/pyDriveWire/pyDriveWire.git`
* Mac: `brew install pypy; pypy -m pip install pyserial`
* Ubuntu: `apt-get install pypy; pypy -m pip install pyserial`


Run It
------
    Usage: ./pyDriveWire.py <port> <speed> [<file>] [...]

	    ./pyDriveWire.py /dev/tty.usbserial-FTF4ZN9S 115200 ...
	    ./pyDriveWire.py accept <port> ...
	    ./pyDriveWire.py connect <host> <port> ...


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

