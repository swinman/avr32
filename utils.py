"""
PYTHON WRAPPER FUNCTIONS FOR PROGRAMMING AVR
---------------------------------------
provide a set of tools to help program avr32 - specifically at32uc3b1512 
devices.
"""

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals
from future_builtins import (ascii, filter, hex, map, oct, zip)

import logging as log
from subprocess import call

def parseCFGword(filename="ispcfg.bin"):
    """
    shows information about the config file and returns the word as bytes
    """
    with open(filename,'rb') as fh:
        data = fh.read()
    values = [ord(c) for c in data]
    word = ["{0:0>2X}".format(v) for v in values]
    print("WORD is: 0x {0} {1} {2} {3}".format(*word))
    return(values)

def makeCFGWord(pin=5, pinhigh=False):
    """
    make the cfg word, including a checksum based on a certain pin number and
    pin condition 
    returns the word as a list with 4 byte values
    """
    magic = 0x494F
    pval = 1 if pinhigh else 0
    word3 = ((magic<<17) + (pval<<16) + (pin<<8))>>8
    print ("First 3 bytes: 0x{0:0>6X}".format(word3))
    crc8 = getCRC8(word3)
    print ("Checksum (CRC8): 0x{0:0>2X}".format(crc8))
    word = (word3<<8) + crc8
    whex = "{0:0>8X}".format(word)
    print ("Word is: 0x{0}".format(whex))
    wvals = [int(whex[2 * i : 2 * i + 2], 16) for i in range(4)]
    return wvals

def makeCFGFile(word, filename="ispcfg.bin"):
    """
    word should be a list with 4 int (byte) values
    """
    with open(filename, 'wb') as fh:
        fh.write(bytearray(word))

def getCRC8(word3):
    """
    calculate one byte cyclic redundancy check

    C(x) = x^8 + x^2 + x^1 + x^0 == 1 0 0 0 0 0 1 1 1

    from: http://ghsi.de/CRC/index.php?Polynom=100000111&Message=929E05
    // ========================================================================
    // CRC Generation Unit - Linear Feedback Shift Register implementation
    // (c) Kay Gorontzi, GHSi.de, distributed under the terms of LGPL
    // ========================================================================
    """
    crc = [0,0,0,0,0,0,0,0]
    binstr = [int(b) for b in list("{0:b}".format(word3))]
    for v in binstr:
        doinvert = v ^ crc[7]
        crc[7] = crc[6]
        crc[6] = crc[5]
        crc[5] = crc[4]
        crc[4] = crc[3]
        crc[3] = crc[2]
        crc[2] = crc[1] ^ doinvert
        crc[1] = crc[0] ^ doinvert
        crc[0] = doinvert
    return sum([c*2**i for i, c in enumerate(crc)])


if __name__=="__main__":
    log.basicConfig(level=log.DEBUG)


