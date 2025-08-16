#!/usr/bin/env python3
"""
dwtelnet.py - Telnet Connection Support for PyDriveWire

Telnet protocol handling for terminal connections to remote systems.
Provides telnet negotiation, terminal emulation, and legacy system 
connectivity through the DriveWire virtual serial interface.
"""

import socket
import threading
import select
from dwio import DWIO
import time
from dwlib import canonicalize

# Telnet protocol constants (from deprecated telnetlib)
IAC = bytes([255])  # Interpret As Command
DONT = bytes([254])
DO = bytes([253])
WONT = bytes([252])
WILL = bytes([251])
SB = bytes([250])   # Subnegotiation Begin
SE = bytes([240])   # Subnegotiation End
ECHO = bytes([1])
NOOPT = bytes([0])


class DWTelnet(DWIO):
    def __init__(self, host='localhost', port=23, debug=False):
        DWIO.__init__(self, threaded=True, debug=debug)
        self.host = host
        self.port = int(port)
        self.sock = None
        self.binding = None
        self.connected = False

    def isConnected(self):
        return self.sock is not None and self.connected

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)  # 10 second timeout
            self.sock.connect((self.host, self.port))
            self.connected = True
            
            # Set socket to non-blocking for read operations
            self.sock.setblocking(False)
            
            if self.debug:
                print("Telnet: Connected to {}:{}".format(self.host, self.port))
                
        except (socket.error, OSError) as e:
            print("Telnet connection failed: {}".format(str(e)))
            self._close()
            raise

    def _read(self, count=256):
        data = b''
        if not self.isConnected():
            return data
        try:
            # Use select to check if data is available
            ready, _, _ = select.select([self.sock], [], [], 0.1)
            if ready:
                data = self.sock.recv(count)
                if data == b'':
                    raise Exception("EOF")
                # Process telnet commands
                data = self._process_telnet_data(data)
        except socket.error as ex:
            if ex.errno not in (socket.EAGAIN, socket.EWOULDBLOCK):
                print(str(ex))
                print("ERROR: Connection Closed")
                self._close()
        except Exception as ex:
            print(str(ex))
            print("ERROR: Connection Closed")
            self._close()
        
        if self.debug and data != b'':
            print("tel read:", canonicalize(data))
        return data

    def _write(self, data):
        if not self.isConnected():
            return 0
        if self.debug and data != b'':
            print("tel write:", canonicalize(data))
        try:
            # Ensure data is bytes
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            bytes_sent = self.sock.send(data)
            return bytes_sent
        except Exception as ex:
            print(str(ex))
            print("ERROR: Connection Closed")
            self._close()
            return 0

    def _close(self):
        self._print("Closing Connection...")
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except BaseException:
                pass
            self.sock = None
        self.abort = True

    def _process_telnet_data(self, data):
        """
        Process telnet IAC commands in the data stream
        Simple implementation that handles basic negotiation
        """
        if IAC not in data:
            return data
            
        result = b''
        i = 0
        while i < len(data):
            if data[i:i+1] == IAC and i + 2 < len(data):
                cmd = data[i+1:i+2]
                opt = data[i+2:i+3]
                
                # Handle basic telnet negotiation
                if cmd == WILL:
                    if opt == ECHO:
                        # Accept echo
                        response = IAC + DO + opt
                    else:
                        # Reject other options
                        response = IAC + DONT + opt
                    self._send_telnet_response(response)
                elif cmd == WONT:
                    # Acknowledge
                    response = IAC + DONT + opt
                    self._send_telnet_response(response)
                elif cmd == DO:
                    # We don't support any options
                    response = IAC + WONT + opt
                    self._send_telnet_response(response)
                elif cmd == DONT:
                    # Acknowledge
                    response = IAC + WONT + opt
                    self._send_telnet_response(response)
                
                i += 3  # Skip IAC + cmd + opt
            else:
                result += data[i:i+1]
                i += 1
                
        return result

    def _send_telnet_response(self, response):
        """Send telnet negotiation response"""
        try:
            self.sock.send(response)
            if self.debug:
                print("tel negotiation:", [hex(b) for b in response])
        except Exception as ex:
            if self.debug:
                print("Telnet negotiation send failed:", str(ex))


if __name__ == '__main__':
    import sys

    sock = DWTelnet(debug=True)

    def cleanup():
        print("main: Closing telnet connection")
        sock.close()
    import atexit
    atexit.register(cleanup)

    try:
        # Get connection details
        host = input("Host (localhost): ") or "localhost"
        port = input("Port (23): ") or "23"
        
        sock.host = host
        sock.port = int(port)
        sock.connect()
        
        print("Connected! Type 'quit' to exit")
        while sock.isConnected():
            try:
                # Check for incoming data
                data = sock._read()
                if data:
                    print(data.decode('utf-8', errors='replace'), end='')
                
                # Simple input handling (in real usage, this would be event-driven)
                import sys
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = input()
                    if line.lower() == 'quit':
                        break
                    sock._write(line + '\r\n')
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print("Error:", str(e))
                break
                
    except Exception as e:
        print("Connection failed:", str(e))
    finally:
        cleanup()


# vim: ts=4 sw=4 sts=4 expandtab
