# pyDriveWire Config File
pyDriveWire accepts options from either the command line or a config file.
There are two ways to provide a config file to pyDriveWire:

* The `-C <cfgFile>` or `--config <cfgFile>` command line options
* A default config file in `~/.pydrivewirerc`

If the config file exists it is read in.  Options are applied to the config and commands are run through the command parser.

#### Note ####
    If both command line options and a config file are
    provided the config file options override the 
    command line options

## Config File Format ##
The config file has two different types of options

1. Options
2. Commands

_Options_ -- Option entries can be used to set any of the command line options to pyDriveWire.  Options always start with the word `option` and have the following format:

    option <optionName> <optionValue>

_Commands_ are any lines in the config file that are not options.  These are standard pyDriveWire commands and they are run through the command parser immediately on start-up so some of the commands may not make sense.

_Comments_ are any lines where the first non-whitespce character is a `#`

### Example Config File ###
    # options
    option accept True
    option port 65504
    option uiPort 6800
    
    # commands
    dw server debug 1
    dw server conn debug 1
    dw disk insert 0 /demo/DWTERM.dsk
    
    
### TCP/IP Accept Options ###
    option accept True
    option port 65504
    
### TCP/IP Connect Options ###
    option connect True
    option host 127.0.0.1
    option port 23
    
### Serial Options ###
    option port /dev/tty.usbserial
    option speed 115200
    
### Web Interface
    option uiPort 6800
    
#### Daemon Mode
    option daemon True
    option daemonPidFile /tmp/pyDriveWire.pid
    option daemonLogFile /tmp/pyDriveWire.log