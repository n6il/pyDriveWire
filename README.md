# pyDriveWire v0.5c-dev
Python Implementation of DriveWire 4 and EmCee Protocols

PyDriveWire is a nearly complete DriveWire4 Server written in Python.  The goal is to eventually implement all of the features available.  The server also implements additional features that are not available in DriveWire4.

PyDriveWire v0.5 also has support for the EmCee Protocol for use with MCX Basic on the TRS-80 MC-10.  

DriveWire 4 and EmCee Procotols can be used simultaneously on the server without reconfiguration.

Features
--------
* (new for v0.5) New [Web User Interface](docs/The%20pyDriveWire%20Manual.md#ch4) (`--ui-port`)
* (new for v0.5) [Configuration File support](docs/The%20pyDriveWire%20Manual.md#ch6)
* (new for v0.5) [Multiple Instance Support](docs/The%20pyDriveWire%20Manual.md#ch7) — Requires config file
* (new for v0.5) [Daemon Mode](docs/The%20pyDriveWire%20Manual.md#ch8) - Linux/macOS Only - Requires config file
* (new for v0.5) [Enhanced `pyDwCli` command console tool](docs/The%20pyDriveWire%20Manual.md#ch5)
* (new for v0.5) [Comprehensive and detailed manual for server features](docs/The%20pyDriveWire%20Manual.md#toc)
* (new for v0.5) [Printing: EmCee/MCX-Basic Printing Support](docs/The%20pyDriveWire%20Manual.md#ch10)
* (new for v0.5) [Printing: `dw printer flush` command](docs/The%20pyDriveWire%20Manual.md#ch10)
* (new for v0.5) [Printing: Selectable output format: txt/pdf](docs/The%20pyDriveWire%20Manual.md#ch10)
* (new for v0.5) [Printing: Selectable output directory](docs/The%20pyDriveWire%20Manual.md#ch10)
* (new for v0.5) [Printing: Run command when print buffer is flushed](docs/The%20pyDriveWire%20Manual.md#ch10)
* (new for v0.5) [HDB-DOS Mode and Disk image offset](docs/The%20pyDriveWire%20Manual.md#ch12)
* Remote dw command input on TCP port
* [Experimental EmCee Protocol Support](docs/The%20pyDriveWire%20Manual.md#ch9)
* Supported on Linux, macOS, and Windows
* `dw server dir` and `dw server list` enhanced to run on _ALL_ OSes (Mac/Windows/Linux, etc)
* [Experimental printing support prints to PDF file](docs/The%20pyDriveWire%20Manual.md#ch10)
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
* MIDI
* OS9 `/Z` console windows
* MShell Support


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
See the [Windows Installation of PyPy(Python) and pyDriveWire](docs/The%20pyDriveWire%20Manual.md#ch2) manual for details.


Run It
------
For a detailed explanation of each option please see the [Command Line and Config File Options](docs/The%20pyDriveWire%20Manual.md#ch3) manual:

    usage: pyDriveWire.py [-h] [-s SPEED] [-a] [-c] [-H HOST] [-p PORT] [-R]
                          [-x EXPERIMENTAL] [-D CMDPORT] [-U UIPORT] [-C CONFIG]
                          [--daemon] [--status] [--stop]
                          [--pid-file DAEMONPIDFILE] [--log-file DAEMONLOGFILE]
                          [--debug] [--version]
                          [FILE [FILE ...]]
    
    pyDriveWire Server <version>
    
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
      -U UIPORT, --ui-port UIPORT
                            pyDriveWire UI Port
      -C CONFIG, --config CONFIG
                            Config File
      --daemon              Daemon Mode, No Repl
      --status              Daemon Status
      --stop                Daemon Status
      --pid-file DAEMONPIDFILE
                            Daemon Pid File
      --log-file DAEMONLOGFILE
                            Daemon Log File
      --debug, -d
      --version, -v


Examples:

* Serial Port: `./pyDriveWire -s 115200 -p /dev/tty.usbserial /tmp/nos96809l2_becker.dsk`
* Listen for TCP connections on port 65504: `./pyDriveWire -a -p 65504 /tmp/nos96809l2_becker.dsk`
* Establish outbound TCP connection: `./pyDriveWire  -c -H 127.0.0.1 -p 23 /tmp/nos96809l2_becker.dsk`
* Experimental Printing support: `./pyDriveWire -x printer -a -p 65504 /tmp/nos96809l2_becker.dsk`



Supported DW Commands
---------------------
The list of [Supported DriveWire Commands](docs/The%20pyDriveWire%20Manual.md#ch13) is in the pyDriveWire manual.

