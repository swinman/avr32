""""
a python script for making a user page...

a nice way to use this is to create an alias

alias makeuser="python ~/software/avr32/makeuser.py"

so that using this tool from the command lines is
$ makeuser 1010-1234-5115-SERIALNUMBER

"""

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals
from future_builtins import (ascii, filter, hex, map, oct, zip)

import logging as log
import sys
import os
from avr32.makehex import makehex


# TODO : implement arg parse for -sn, -pin, -phigh, -fn, -bin


def makeuser(serialnumber="", pin=5, pinhigh=False, filename='userpage'):
    """
    puts the value for word in the last 4 bytes of the 512 byte user page
    puts the value for the serial number in the first x bytes of the user page
    filename.bin and filename.hex will be created.
    """
    # init the page
    page = bytearray([0xFF] * 512)

    # add the serial number
    for i, c in enumerate(list(serialnumber)):
        page[i] = c
    if len(serialnumber):
        page[i+1] = 0

    # add bootloader configuration word
    word = _makeCFGWord(pin, pinhigh)
    revword = list(word)
    revword.reverse()
    for i, b in enumerate(revword):
        page[-1 - i] = b

    binfn = ".".join([filename, "bin"])
    hexfn = ".".join([filename, "hex"])

    with open(binfn, 'wb') as fh:
        fh.write(page)

    makehex(binfn, hexfn, 0x80800000)

    keepbin = False
    if not keepbin:
        os.remove(binfn)

def _makeCFGWord(pin=5, pinhigh=False):
    """ make the cfg word, including a checksum based on a certain pin number and
    pin condition 
    returns the word as a list with 4 byte values
    """
    magic = 0x494F
    pval = 1 if pinhigh else 0
    word3 = ((magic<<17) + (pval<<16) + (pin<<8))>>8
    print ("First 3 bytes: 0x{0:0>6X}".format(word3))
    crc8 = _getCRC8(word3)
    print ("Checksum (CRC8): 0x{0:0>2X}".format(crc8))
    word = (word3<<8) + crc8
    whex = "{0:0>8X}".format(word)
    print ("Word is: 0x{0}".format(whex))
    wvals = [int(whex[2 * i : 2 * i + 2], 16) for i in range(4)]
    return wvals

def _parseCFGword(filename="ispcfg.bin", display=True):
    """
    shows information about the config file and returns the word as bytes
    """
    with open(filename, 'rb') as fh:
        data = fh.read()
    values = [ord(c) for c in data]
    if display:
        word = ["{0:0>2X}".format(v) for v in values]
        print("WORD is: 0x {0} {1} {2} {3}".format(*word))
        pin = values[2]
        val = values[1] % 2
        print("IO Condition: Pin {0} {1}".format(pin, "High" if val else "Low"))
    return(values)

def _getCRC8(word3):
    """
    calculate one byte cyclic redundancy check

    C(x) = x^8 + x^2 + x^1 + x^0 == 1 0 0 0 0 0 1 1 1

    from: http://ghsi.de/CRC/index.php?Polynom=100000111&Message=929E05
    // ========================================================================
    // CRC Generation Unit - Linear Feedback Shift Register implementation
    // (c) Kay Gorontzi, GHSi.de, distributed under the terms of LGPL
    // ========================================================================
    """
    crc = [0, 0, 0, 0, 0, 0, 0, 0]
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
    if len(sys.argv) > 1:
        serialnumber = sys.argv[1]
        print("Creating user page with serial number: {0}".format(serialnumber))
        makeuser(serialnumber)
