# pyDriveWire v0.5c
Python Implementation of DriveWire 4 and EmCee Protocols

PyDriveWire is a nearly complete DriveWire4 Server written in Python.  The goal is to eventually implement all of the features available.  The server also implements additional features that are not available in DriveWire4.

PyDriveWire also has support for the EmCee Protocol for use with MCX Basic on the TRS-80 MC-10.  

DriveWire 4 and EmCee Procotols can be used simultaneously on the server without reconfiguration.

# <a name="toc"></a>Table of Contents

1. [Features](#ch1)
2. [Getting Started](#ch2)

# 1. <a name="ch1"></a>Features

* (new for v0.5c) [New Easy Installation Methods: Binary Package, Docker](#ch2)
* (new for v0.5c) `dw config show` command
* (new for v0.5c) `dw config save` command
* (new for v0.5c) `dw disk create` command
* (new for v0.5c) Major re-work of Virtual Serial Channels
* (new for v0.5c) [Printing Support Enhancements](docs/The pyDriveWire Manual.md#ch10)
* [Web User Interface](docs/The pyDriveWire Manual.md#ch4) (`--ui-port`)
* [Configuration File support](docs/The pyDriveWire Manual.md#ch6)
* [Multiple Instance Support](docs/The pyDriveWire Manual.md#ch7) — Requires config file
* [Daemon Mode](docs/The pyDriveWire Manual.md#ch8) - Linux/macOS Only - Requires config file
* [Enhanced `pyDwCli` command console tool](docs/The pyDriveWire Manual.md#ch5)
* [Comprehensive and detailed manual for server features](docs/The pyDriveWire Manual.md#toc)
* [Printing: EmCee/MCX-Basic Printing Support](docs/The pyDriveWire Manual.md#ch10)
* [HDB-DOS Mode and Disk image offset](docs/The pyDriveWire Manual.md#ch12)
* Remote dw command input on TCP port
* [EmCee Protocol Support](docs/The pyDriveWire Manual.md#ch9)
* Supported on Linux, macOS, and Windows
* `dw server dir` and `dw server list` enhanced to run on _ALL_ OSes (Mac/Windows/Linux, etc)
* [Experimental printing support prints to PDF or text file](docs/The pyDriveWire Manual.md#ch10)
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


## Notable Missing Features
* MIDI
* OS9 `/Z` console windows
* MShell Support

[Back to top](#toc)

# 2. <a name="ch2"></a>Getting Started

(new for v0.5c) pyDriveWire has two Easy Installtion Methods: Binary Package and Docker.  These options are designed for Ease Of Use and do not require a complex series of installation steps.   pyDriveWire can also be run directly from any `pypy` or `python` install if it meets the appropriate requirements.

In terms of performance, the Python and Binary Package installation methods are fully functional but have the lowest performance.  Docker provides a medium level of performance.  pypy should be used to get the maximum performance out of pyDriveWire.


## 2.1 Binary Package Installation
Binary packages are available at the following location:

[https://github.com/n6il/pyDriveWire/releases/latest](https://github.com/n6il/pyDriveWire/releases/latest)

Packages are available for the following operating systems:

* `linux-x86_64` -- Any modern 64-bit Linux 
* `win-x64` -- 64-bit Windows (Windows 7 or later)
* `win32` -- 32-bit Windows (Windows 7 or later)
*  `rpi3` -- Raspberry Pi 3 (Raspbian Buster)
*  `rpi4` -- Raspberry Pi 4 (Raspbian Jesse)
*  `macOs` -- macOs (High Sierra or later)

Using a Binary Package is very simple:

1. Download the package for your operating system
2. Unzip the package
3. The package contains two executable programs `pyDriveWire` and `pyDwCli` and a copy of this manual.
4. Run the `pyDriveWire` executable.  See next section for examples:
5. Full details of the command line options are in the [Command Line and Config File Options](docs/The pyDriveWire Manual.md#ch3) section.

## 2.2 Running a Binary Package
Example: Run pyDriveWire with the HTTP UI on port 6800 and use a serial port:

    pyDriveWire --ui-port 6800 --port /dev/ttyUSB0 --speed 460800
    
Example: Run pyDriveWire with the HTTP UI on port 6800 and use a serial port and mount two disk images:

    pyDriveWire --ui-port 6800 --port /dev/ttyUSB0 --speed 460800 \
    	/demo/test1.dsk /demo/test2.dsk

Example: Run pyDriveWire with the HTTP UI on port 6800 and the Becker port connection on port 65504:

    pyDriveWire --ui-port 6800 --accept --port 65504

## 2.3 Docker
1. Install Docker Desktop
2. Clone the container: `docker pull mikeyn6il/pydrivewire`
3. Run the container.  See next section for examples.  
4. Full details of the command line options are in the [Command Line and Config File Options](docs/The pyDriveWire Manual.md#ch3) section.

## 2.4 Running The Docker Container
Example: Run pyDriveWire with the HTTP UI on port 6800 and use a serial port:

    docker run -i -p 6800:6800/tcp -p 65504:65504/tcp \
    	--device /dev/ttyUSB0:/dev/ttyUSB0 mikeyn6il/pydrivewire:latest \
    	--ui-port 6800 --port /dev/ttyUSB0 --speed 460800

For Windows use the following `--device` option:

    --device COM4:/dev/ttyUSB0

Example: Run pyDriveWire with the HTTP UI on port 6800 and use a serial port and use a HTTP disk image:

    docker run -i -p 6800:6800/tcp -p 65504:65504/tcp \
    	--device /dev/ttyUSB0:/dev/ttyUSB0 mikeyn6il/pydrivewire:latest \
    	--ui-port 6800 --port /dev/ttyUSB0 --speed 460800 \
    	http://www.ocs.net/~n6il/DWTERM.dsk

Example: Run pyDriveWire with the HTTP UI on port 6800 and the Becker port connection on port 65504:

    docker run -i -p 6800:6800/tcp -p 65504:65504/tcp \
    	mikeyn6il:pydrivewire/latest \
    	--ui-port 6800 --accept --port 65504

 
## 2.4 Installation Requirements<a name="ch2.1"></a>

* pypy -- For maximum performance it is recommended to run the server with
pypy.  pypy is a Python interpreter that does JIT compilation and results in
greatly increased speed
* pyserial -- Install using pip

## 2.5 Supported Operating Systems
* Any OS where you can run Python, including but not limited to:
* Linux
* macOS
* Windows

## 2.5 Installation Details<a name="ch2.1"></a>

Please see [The pyDriveWire Manual - Chapter 2](docs/The pyDriveWire Manual.md#ch2) for detailed installation instructions

