# pyDriveWire
Python Implementation of DriveWire 4 and EmCee Protocols

PyDriveWire is a nearly complete DriveWire4 Server written in Python.  The goal is to eventually implement all of the features available.  The server also implements additional features that are not available in DriveWire4.

PyDriveWire v0.4 also has experimental support for the EmCee Protocol for use with MCX Basic on the TRS-80 MC-10.  

DriveWire 4 and EmCee Procotols can be used simultaneously on the server without reconfiguration.

Features
--------
* (new for v0.4) Remote dw command input on TCP port
* (new for v0.4) Experimental EmCee Protocol Support
* (new for v0.4) Added Windows installation instructions
* (new for v0.4) Added `pyDriveWire.bat` file
* (updated v0.4) `dw server dir` and `dw server list` enhanced to run on _ALL_ OSes (Mac/Windows/Linux, etc)
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
* Windows


Installation (Linux/macOS/UNIX)
------------
* Download Latest: [https://github.com/n6il/pyDriveWire/releases](https://github.com/n6il/pyDriveWire/releases)
* Mac: `brew install pypy; pypy -m pip install pyserial`
* Ubuntu: `apt-get install pypy; pypy -m pip install pyserial`

_Experimental Printing Support_

* `pypy -m pip install reportlab`


Installation (Windows)
------------
1. Obtain the latest copy of _Python 2.7 Compatible PyPy for Windows_  from
   https://www.pypy.org/download.html
2. Extract it to the `C:\Program Files (x86)` folder
3. Add 2 entries to your system path:   
  a. the folder where you extracted PyPy to  
  b. the folder above and add `\bin` to the end
4. Download pip: https://bootstrap.pypa.io/get-pip.py
5. Install Pip. Open a command prompt and type: `pypy get-pip.py`
6. Install pyserial: `pip install pyserial`
7. Download (or git clone) the latest pyDriveWire release package from
   https://github.com/n6il/pyDriveWire/releases and extract it.
8. Versions 0.4 and later have a `pyDriveWire.bat` batch file you can run.
   Earlier versions can be started from the command prompt: `pypy
pyDriveWire.py <options>`

Run It
------
    usage: pyDriveWire [-h] [-s SPEED] [-a] [-c] [-H HOST] [-p PORT] [-R]
                          [-x EXPERIMENTAL]
                          FILE [FILE ...]
    
    pyDriveWire Server v0.4
    
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
      -D CMDPORT, --cmd-port CMDPORT
                            Remote dw command input

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


# Experimental EmCee Protocol Support
pyDriveWire version v0.4 adds experimental support for the EmCee protocol used on the TRS-80 MC-10 running MCX Basic (MCX Basic is available on the MCX-128 expansion card).  The EmCee protocol support is always turned on allowing any application connected to a pyDriveWire server to use EmCee and DriveWire protocols simultaneously.  With this setup one could use a DriveWire application on a MC-10 or a EmCee application on a CoCo without the need to switch servers.

As of v0.4 the following MCX Basic Commands are supported:

* `SETDIR`
* `DIR`
* `LOAD`
* `LOADM`


The following file formats are supported:

* `.C10`
* `.CAS`


## Important Note about Simultaneous use of DriveWire and EmCee Protocols
Drive 0 will be used by the EmCee server for mounting the `.C10` or `.CAS` files.  Any DriveWire disk in Drive 0 will be unmounted. If data was written to the DriveWire disk in Drive 0 it is highly recommended to umount the DriveWire disk using the `dw disk eject 0` command before using any of the EmCee features. 

## Notes

1. You must use 38400 baud to use the EmCee protocol on  a MC-10 running MCX Basic
2. The `SETDIR` command works differently than the standard EmCee Server.
3. At the current time pyDriveWire _only_ supports `.C10` and `.CAS` formatted files.  WAV and BIN file support is planned for a future update.
4. At the current time you cannot open a `.C10` or `.CAS` file from the command line.  Use the `LOAD`,  `LOADM`  or `OPEN` commands.

## Using pyDriveWire's EmCee Server

The EmCee server in pyDriveWire is on by default and there are no commands to turn it on or off.  The only special requirement is that ***You must use 38400 baud to use the EmCee protocol on  a MC-10 running MCX Basic***.  Please see the rest of this documentation for how to invoke pyDriveWire.  Once pyDriveWire is started you can use the normal MCX Basic commands to access files on the server.

## `SETDIR <path>` - Set the directory on the server

#### Options

* `<path>` --  full path name a directory on the server

#### Description 

The pyDriveWire version of `SETDIR` is different than the normal EmCee server.  You must provide a full path name to the directory you want to switch to.

#### Examples

* Windows: `SETDIR C:\Users\Mikey\MC-10`
* Mac/Linux: `SETDIR /home/Mikey/MC-10`


## `DIR [<path>]` - List directory on the server

#### Options

* `<path>` --  optional full path name a directory on the server

#### Description

List the directory on the server.  The default directory is the one where pyDrivewire was invoked. `<path>` is optional and must be a full path name to the directory you want to list.

#### Examples

* `DIR`
* Windows: `DIR C:\Users\Mikey\MC-10`
* Mac/Linux: `DIR /home/Mikey/MC-10`


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

