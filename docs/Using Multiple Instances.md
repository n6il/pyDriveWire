# Using Multiple pyDriveWire Instances

pyDriveWire allows you to configure and use multiple instances which all run in parallel.  Each instance talks to one DriveWire client and each can mount different disk images.  The instances are configured in a config file to specify the connection point and any options you wish to set for for each instance.

Note:  At the current time instances can only be specified in the config file and can only be started or stopped along with the main invocation of pyDriveWire.

## Configuring Multiple Instances

Instances are configured in a pyDriveWire Config file.

The options and commands for first instance `instance 0`  starts at the top of the config file and includes any lines which are not comments or blank lines.  The main instance commands and options stop at the first instance tag.

Additional instances can be added by adding an instance tag:

    [serial]
    
The name of the instance is for you to know what it's for, the server doesn't use it.

Instances are numbered sequentially.  The first instance is always instance 0.  The instance following that one is instance 1, etc.

Options and commands for the instance start after the instance tag and continue until the next instance tag.

Multiple instances can be specified.

## Example Config

    # Main Instance 
    option accept True
    option port 65504
    option uiPort 6800
    dw server debug 1
    dw server conn debug 1
    dw disk insert 0 /demo/plato.dsk
    
    [serial]
    option port /dev/ttyS0
    option speed 115200
    dw disk insert 0 /demo/DWTERM.dsk
    
    [connect]
    option connect True
    option host mfurman-a01.local
    option port 54321

Instance 0 listens on port 65504 for incoming connections and is mounting a disk image.

Instance 1 uses a serial port at 115200 baud and also mounts a disk image

Instance 2 makes an outgoing TCP/IP connection to the specified host and port.

## Instance Commands

pyDriveWire has a few commands to control instances.  These commands should only be used from the command line interface, the web interface, or pyDwCli.

Note: Using instance commands from a DriveWire Client is not recommended.

* `dw instance show`
* `dw instance select <inst>`

## `dw instance show`

Shows a list of the currently configured instances.  The current instance is marked with an asterisk `*`:

    pyDriveWire(0)>  dw instance show
    
    
    Inst.  Type
    -----  --------------------------------------
    0*     dwsocket.DWSocketServer localhost:65504
    1      dwserial.DWSerial /dev/ttyS0 115200
    2      dwsocket.DWSocket mfurman-a01.local:54321

## `dw instance select <inst>`

Switches to a different instance.

    pyDriveWire(0)>  dw instance select 1
    Selected Instance 1: dwserial.DWSerial /dev/ttyS0 115200
    pyDriveWire(1)>
    
The server will respond with a line telling you which instance you just switched to.
The command prompt will also change to show the current instance.  You can see in the example above that the original prompt was instance 0 and it switched to instance 1.