# Command Line and Config File Options

This manual section is meant as a quick and comprehensive guide to all of the pyDriveWire configuraiton options.  Many of the options have a detailed manual page which describes that individual feature.  There will be a link to those pages.

## Command Line Options
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


## Config File (global)

The pyDriveWire config file can be used to set all of the command line options.

The config file can either be in a default location or can be specified from the command line.

Please see the pyDriveWire Config File and Using Multiple Instances guides for more detail about the config file.

Note: Command line options have prescidence over config file.  This means that if both are specified the command line version will be used.

Note: Options are noted as either instance specific (instance) or global (global).  Global options can only be specified in Instance 0.

### Default Config file location

The default location for the config file is in your home directory: `~/.pydrivewirerc`

* Linux: `/home/<userid>/.pydrivewirerc`
* Mac: `/Users/<userid>/.pydrivewirerc`
* Windows: `C:\Users\<userid>\.pydrivewirerc`

Note: This option cannot be specified in a config file

### Specify a config file location: 

    -C <config_file>
    
or

    --config <config_file> 

## Serial Port (instance)



pyDriveWire will start a server instance which listens for the DriveWire or EmCee client on `<serial_port>` at `<baud>` 

* Linux/Mac:  This should be a device such as `/dev/ttyUSB0`
* Windows: `COM1`

### Command Line:

    --port <serial_port> --speed <baud>
or

    -p <serial_port> -s <baud>`

### Config File:

    option port <serial_port>
    option speed <baud>

Serial Port mode also supports RTS/CTS flow control.

Note: DO NOT use this with a CoCo or MC-10 Bit Banger port.  This is intended for use with a UART that properly implements flow control.  The RS-232 Pak or any device with a 6551 UART does not implement flow control properly.

### Command Line:

    -R
or

    --rtscts

### Config File:

    option rtscts [True|False]
    
Note: Omitting this option line defaults to `False`

## TCP Server (Accept Incoming Connections) (instance)

pyDriveWire will start a server instance which listens for the DriveWire or EmCee client on `<tcp_port>`.  Note that only one client can connect to each port.

### Command Line:

    --accept --port <tcp_port>
    
or
    
    -a -c <tcp_port>
   

### Config File:

    option accept True
    option port <tcp_port>
    
## Outgoing TCP Connections (instance)

pyDriveWire will start a server instance which makes an outgoing TCP connection to `<hostname>:<tcp_port>`.  Once that connection has been established pyDriveWire will listen for DriveWire or EmCee commands on that connection.  This is useful for many Telnet-To-Serial bridge devices.

### Command Line

    --connect --host <hostname> --port <tcp_port>
or

    -c -H <hostname> -p <tcp_port>

### Config File:

    option accept True
    option port <tcp_port>
    
## Web/HTTP UI (global)

pyDriveWire has a Web/HTTP User Interface.  See the [Web User Interface]() manual for more details.

### Command Line:

    -U <ui_port>

or

    --ui-port <ui_port>

### Config File:

    option uiPort <ui_port>
    
## Debugging (global)

pyDriveWire has 3 levels of debugging: 

* Default: No Debugging (Level 0)
* Command Debugging (Level 1)
* Connection Debugging (Level 2)

The Debugging option on the command line or config file is _global_ and is applied to All Instances.

Note: The config file option _must_ be put in the first instance.

### Default: Debug Level 0

No debugging commands are sent on the pyDriveWire Console.  This is the default if no debugging option or command is specified.

You may also specify this in the config file:

    option debug 0
    

### Debug Level 1: Command Logging

This debugging level displays one line for each command the DriveWire or EmCee client sends to the server.  See the pyDriveWire Debugging Guide for more detail.


### Command Line:

    -d

### Config file:

    option debug 1

### Debug Level 2: Connection Debugging

This debugging level includes command debug level 1 and in addition to that displays a HexDump of every byte the pyDriveWire server sends and receives from the client.   This can be extremely verbose and slows down the pyDriveWire server slightly so it is not recommended for normal use.  See the pyDriveWire Debugging Guide for more detail.

### Command Line:

    -dd

### Config file:

    option debug 2
    

## Start pyDriveWire in Daemon Mode (global)

Note: If you are using a config file it is recommended to put the pid file and log file options in the config file and to run the server with `--daemon -C <config_file>`

Note: If your config file is in the default location you do not need to specify it on the command line

### Command Line:

    --daemon [-C <config_file>] [--pid-file <pid_file> --log-file <log_file>]

### Config file:

    option daemon True/False
    option daemonPidFile <pid_file>
    option daemonLogFile <log_file>
    
    
## pyDriveWire in Daemon Mode Status

Note: Either the config file or pid file option is required.

Note: This option cannot be specified in a config file

Note: If your config file is in the default location you do not need to specify it on the command line


### Command Line:

    --status [-C <config_file>]

or

    --status [--pid-file <pid_file>]

## Stop pyDriveWire in Daemon Mode

Note: Either the config file or pid file option is required.

Note: This option cannot be specified in a config file

Note: If your config file is in the default location you do not need to specify it on the command line

### Command Line:

    --stop [-C <config_file>]

or

    --stop [--pid-file <pid_file>]

