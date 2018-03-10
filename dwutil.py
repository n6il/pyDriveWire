from ctypes import *
from struct import *

def dwCrc16(data):
	checksum = sum(bytearray(data))
	return pack(">H", c_ushort(checksum).value)
