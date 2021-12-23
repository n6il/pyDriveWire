# pyDriveWire Extensions to the DriveWire Protocol

pyDriveWire has many extensions and enhancements compared to the standard
DriveWire4 server.  Some of the extensions are on permanently, others can
be enabled by command line, config file, or server commands.  Still others
are experimental features.  The DriveWire 4 protocol provides extremely
rudimentary ability to tell the client which protocol version the server
supports.  Other information may be available by using server commands, but
using server commands requires at least 100 lines of assembly code just to
run one command and to parse the results.  pyDriveWire provides an
extension which clients can use to determine the server version, which
features are available and which features are currently enabled.  This is
done in a way which is backwards compatible with the DriveWire 4
specification.

## The pyDriveWire Combination Lock

pyDriveWire provides enhanced information to clients by use of a
combination lock mechanism.  Once the client has activated the combination
lock the client can request an individual page(byte) of information from
the server and then the lock is closed again.  The combination lock must be
activated for each individual page desired.

### Combo Locks

| Lock Code | Supported Servers |
|-----------|-------------------|
| `py`      | pyDriveWire v0.5d and later |

### pyDriveWire Combo Lock Detail

pyDriveWire's Combination Lock is activated as follows:

1. Client sends `OP_DWINIT` command byte
2. Client sends `p` lock combination byte #1
3. Server repeats the lock code `p`.  A pyDriveWire server returning `$FF` does not
support this extension.
4. Client sends `OP_DWINIT` command byte
5. Client sends `y` lock combination byte #2
6. Server repeats the lock code `y`.  A pyDriveWire server returning `$FF` does not
support this extension.
7. At this point the combination lock is open
8. Client sends `OP_DWINIT` command byte
9. Client sends byte for desired information page
10. Server returns information for requested page
11. Combination Lock is closed.

The combination for pyDriveWire's lock is the byte 'p' followed by 'y'.
Other DriveWire servers may add their own combination lock and provide
their own information.

If a DriveWire server does not support this extension then it will simply return the default value that it normally would for that server.  This is how the client can determine what type of server it is communicating with and whether the extension is available or not.

| Server | Return Values |
|--------|---------------------|
|DriveWire 2 or 3| No reply
|DriveWire 4| $0404
| pyDriveWire v0.5c and earlier| $FFFF
| pyDriveWire v0.5d and later| `py`

If the client finds the values returned do not match the combo lock then the server does not support this combo lock extension.

## Information Pages

Information pages are called up by the client sending a byte for the
desired information page.  The following pages are reserved and shall not
be used by any server:

* $00 - $0F -- Reserved:: DriveWire Protocol Version
* $F0 - $FF -- Reserved:: DriveWire Protocol Version

The bytes $10 through $EF represent valid requests for information pages.

### Page Data Types
* Byte - Byte 1: data
* String - Byte 1: String Length Byte 2-N: String returned one byte at a time
* Block - Byte 1: Drive Number - Byte 2: length MSB Byte 3: Length LSB

Block Transfers - The server returns data in a similar manner to NamedObjects.  The server presents the data on one of the DriveWire drives and returns the drive number and the data length in bytes to the client.  The client can then issue the required number of OP_READ or OP_READEX calls to obtain the data.

pyDriveWire defines the following information pages:

|Page|Description               |
|---:|--------------------------|
|'E' |Enabled Features, page 1  |
|'e' |Enabled Features, page 2  |
|'F' |Available Features, page 1|
|'f' |Available Features, page 2|
|'V' |Server Version page 1|
|'v' |Server Version page 2|


### Page 'E' - Enabled Features - Page 1

Page Data Type: byte

Supported Servers:

* pyDriveWire v0.5d and later

|Bit|Description|
|--:|------------------------|
|7  |Reserved
|6  |PlaySound Support
|5  |SSH Support
|4  |Printing Support
|3  |DosPlus Mode
|2  |HDBDos Mode
|1  |DLOAD Protocol
|0  |EmCee Protocol - always 1

### Page 'e' - Enabled Features - Page 2

Page Data Type: byte

Supported Servers:

* None

|Bit|Description|
|--:|------------------------|
|7  |Reserved
|6  |
|5  |
|4  |
|3  |
|2  |
|1  |
|0  |

### Page 'F' - Available Features - Page 1

Page Data Type: byte

Supported Servers:

* pyDriveWire v0.5d and later

|Bit|Description|
|--:|------------------------|
|7  |Reserved
|6  |PlaySound Support
|5  |SSH Support
|4  |Printing Support
|3  |DosPlus Mode
|2  |HDBDos Mode
|1  |DLOAD Protocol
|0  |EmCee Protocol - always 1

### Page 'f' - Available Features - Page 2

Page Data Type: byte

Supported Servers:

* None

|Bit|Description|
|--:|------------------------|
|7  | Reserved
|6  |
|5  |
|4  |
|3  |
|2  |
|1  |
|0  |

### Page 'V' - Server Version - Page 1

Page Data Type: byte

Supported Servers:

* pyDriveWire v0.5d and later

|Bits|Description|
|---:|---------------------------|
|4-7 |Major Version - binary 0-15
|0-3 |Minor Version MSB - BCD 0-9

### Page 'v' - Server Version - Page 2

Page Data Type: byte

Supported Servers:

* pyDriveWire v0.5d and later

|Bits|Description|
|---:|---------------------------|
|4-7 |Minor Version LSB - BCD 0-9
|0-3 |Sub Version

Sub Version

|Value|Code|
|----:|----|
|0|None|
|1|`a`|
|2|`b`|
|...||
|15|`o`|


