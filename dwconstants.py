#!/usr/bin/env python3

"""
DriveWire Protocol Constants
"""

PYDW_VERSION_MAJOR = 0
PYDW_VERSION_MINOR = 6
PYDW_VERSION_SUB = None
PYDW_VERSION_STRING = 'v%s.%s%s' % (
        PYDW_VERSION_MAJOR,
        PYDW_VERSION_MINOR,
        PYDW_VERSION_SUB)

# DriveWire Protocol Commands
OP_NAMEOBJ_MOUNT = b'\x01'    # chr(0x01)
OP_NAMEOBJ_CREATE = b'\x02'   # chr(0x02)
OP_RESET3 = b'\xF8'           # chr(0xF8)
OP_RESET2 = b'\xFE'           # chr(0xFE)
OP_RESET1 = b'\xFF'           # chr(0xFF)
OP_INIT = b'\x49'             # chr(0x49)
OP_TERM = b'\x54'             # chr(0x54)
OP_DWINIT = b'\x5A'           # chr(0x5A)
OP_TIME = b'\x23'             # chr(0x23)
OP_NOP = b'\x00'              # chr(0x00)
OP_READ = b'\x52'             # chr(0x52)
OP_REREAD = b'\x72'           # chr(0x72)
OP_WRITE = b'\x57'            # chr(0x57)
OP_READEX = b'\xD2'           # chr(0xD2)
OP_REREADEX = b'\xF2'         # chr(0xF2)
OP_REWRITE = b'\x77'          # chr(0x77)
OP_GETSTAT = b'\x47'          # chr(0x47)
OP_SETSTAT = b'\x53'          # chr(0x53)
OP_PRINT = b'\x50'            # chr(0x50)
OP_PRINTFLUSH = b'\x46'       # chr(0x46)
OP_SERINIT = b'\x45'          # chr(0x45)
OP_SERREAD = b'\x43'          # chr(0x43)
OP_SERREADM = b'\x63'         # chr(0x63)
OP_SERWRITE = b'\xC3'         # chr(0xC3)
OP_FASTWRITE0 = b'\x80'       # chr(0x80)
OP_FASTWRITE1 = b'\x81'       # chr(0x81)
OP_FASTWRITE2 = b'\x82'       # chr(0x82)
OP_FASTWRITE3 = b'\x83'       # chr(0x83)
OP_FASTWRITE4 = b'\x84'       # chr(0x84)
OP_FASTWRITE5 = b'\x85'       # chr(0x85)
OP_FASTWRITE6 = b'\x86'       # chr(0x86)
OP_FASTWRITE7 = b'\x87'       # chr(0x87)
OP_FASTWRITE8 = b'\x88'       # chr(0x88)
OP_FASTWRITE9 = b'\x89'       # chr(0x89)
OP_FASTWRITE10 = b'\x8A'      # chr(0x8A)
OP_FASTWRITE11 = b'\x8B'      # chr(0x8B)
OP_FASTWRITE12 = b'\x8C'      # chr(0x8C)
OP_FASTWRITE13 = b'\x8D'      # chr(0x8D)
OP_FASTWRITE14 = b'\x8E'      # chr(0x8E)
OP_FASTWRITE15 = b'\x8F'      # chr(0x8F)
OP_SERWRITEM = b'\x64'        # chr(0x64)
OP_SERGETSTAT = b'\x44'       # chr(0x44)
OP_SERSETSTAT = b'\xC4'       # chr(0xC4)
OP_SERTERM = b'\xC5'          # chr(0xC5)
OP_PLAYSOUND = b'\xFA'        # chr(0xFA)
OP_PLYSNDSTP = b'\xFB'        # chr(0xFB)

# Error Codes
E_OK = 0
E_EOF = 211
E_WRPROT = 242
E_CRC = 243
E_READ = 244
E_WRITE = 245
E_NOTRDY = 246
E_SEEK = 247
E_PLAYSOUND = 250

# Protocol Constants
NULL = b'\x00'  # chr(0)

SECSIZ = 256
INFOSIZ = 4
CRCSIZ = 2
STATSIZ = 2

# Serial Status Commands
SS_ComSt = b'\x28'   # chr(0x28)
SS_Open = b'\x29'    # chr(0x29)
SS_Close = b'\x2A'   # chr(0x2A)

# pyDriveWire features
FEATURE_EMCEE    = 0b00000001
FEATURE_DLOAD    = 0b00000010
FEATURE_HDBDOS   = 0b00000100
FEATURE_DOSPLUS  = 0b00001000
FEATURE_PRINTER  = 0b00010000
FEATURE_SSH      = 0b00100000
FEATURE_PLAYSND  = 0b01000000
FEATURE_RESERVED = 0b10000000

# EmCee Protocol
MC_ATTENTION = b'\x21'  # chr(0x21)
MC_LOAD = b'\x4C'       # chr(0x4C)
MC_GETBLK = b'\x47'     # chr(0x47)
MC_NXTBLK = b'\x4E'     # chr(0x4E)
MC_SAVE = b'\x53'       # chr(0x53)
MC_WRBLK = b'\x57'      # chr(0x57)
MC_OPEN = b'\x4F'       # chr(0x4F)
MC_DIRFIL = b'\x46'     # chr(0x46)
MC_RETNAM = b'\x24'     # chr(0x24)
MC_DIRNAM = b'\x44'     # chr(0x44)
MC_SETDIR = b'\x43'     # chr(0x43)
MC_REWRBLK = b'\x77'    # chr(0x77)
MC_PRINT = b'\x50'      # chr(0x50)

# EmCee Errors
E_MC_FC = 8
E_MC_IO = 34
E_MC_FM = 36
E_MC_DN = 38
E_MC_NE = 40
E_MC_WP = 42
E_MC_FN = 44
E_MC_FS = 46
E_MC_IE = 48
E_MC_FD = 50
E_MC_AO = 52
E_MC_NO = 54
E_MC_DS = 56

# DLOAD Constants
# 1.  P.ACK - Acknowledge - C8 hex.
DLOAD_P_ACK = b'\xC8'    # chr(0xC8)
# 2.  P.ABRT - Abort - BC hex.
DLOAD_P_ABRT = b'\xBC'   # chr(0xBC)
# 3.  P.BLKR - Block request - 97 hex.
DLOAD_P_BLKR = b'\x97'   # chr(0x97)
# 4.  P.FILR - File request - 8A hex.
DLOAD_P_FILR = b'\x8A'   # chr(0x8A)
# 5.  P.NAK - Negative Acknowledge - DE hex.
DLOAD_P_NAK = b'\xDE'    # chr(0xDE)

# DLOAD File Types
DLOAD_FT_BASIC = b'\x00'  # chr(0x00)
DLOAD_FT_ML = b'\x02'     # chr(0x02)
DLOAD_FT_FNF = b'\xFF'    # chr(0xFF)

# DLOAD Ascii Flag
DLOAD_AF_ASCII = b'\xFF'  # chr(0xFF)
DLOAD_AF_BIN = b'\x00'    # chr(0x00)

# DLOAD Protocol Constants
DLOAD_BLOCK_SIZE = 128
DLOAD_MSB_SHIFT = 7

# Utility functions for Python 3 compatibility
def byte_to_chr(b):
    """Convert single byte to character for compatibility"""
    if isinstance(b, bytes) and len(b) == 1:
        return chr(b[0])
    elif isinstance(b, int):
        return chr(b)
    else:
        return str(b)

def chr_to_byte(c):
    """Convert character or int to single byte"""
    if isinstance(c, str) and len(c) == 1:
        return bytes([ord(c)])
    elif isinstance(c, int):
        return bytes([c])
    elif isinstance(c, bytes) and len(c) == 1:
        return c
    else:
        raise ValueError("Invalid input for chr_to_byte: {}".format(repr(c)))

# vim: ts=4 sw=4 sts=4 expandtab
