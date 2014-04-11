""""
a python script for making a user page...

a nice way to use this is to create an alias

alias makeuser="python ~/software/avr32/makeuser.py"

so that using this tool from the command lines is
$ makeuser -sn 1010-1234-5115-SERIALNUMBER

--- NOTE ---
the AT32UC3Bxxx comes shipped with a bootloader running. if you launch
out of the bootloader it can be accessed by shorting pin A13 to ground.
this pin is the joystick on the EVK1101 and SCK on the sensor board

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


def makeuser(serialnum="", pin=5, pinhigh=False, filename=None, keepbin=False):
    """
    puts the value for word in the last 4 bytes of the 512 byte user page
    puts the value for the serial number in the first x bytes of the user page
    filename.bin and filename.hex will be created.

    the default (shipped) value for the boot select pin is 0x0D (pin A13)
    """
    # make a filename if not provided
    if filename is None:
        filename = serialnum if serialnum != "" else "userpage"

    # init the page
    page = bytearray([0xFF] * 512)

    # add the serial number
    for i, c in enumerate(list(serialnum)):
        page[i] = c
    if len(serialnum):
        page[i+1] = 0

    # add bootloader configuration word
    if pin is not None:
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

def parseargs(args):
    """
    parse argument options -b, -sn, -p, -f, -kb
    """
    b = False
    sn = ""
    p = 5
    phigh = False
    fn = None
    keepbin = False

    if args[0] == "-b":
        if len(args) == 1:
            return(True, sn, None, phigh, fn, keepbin)
        elif len(args) == 3 and args[1] == '-f':
            fn = args[2]
            return(True, sn, p, phigh, fn)
        else:
            return(False, 0,0,0,0,0)

    while (len(args)):
        if args[0] == '-sn':
            args, sn = _checkname(args)
        elif args[0] == '-p':
            args, p, phigh = _checkpin(args)
        elif args[0] == '-f':
            args, fn = _checkname(args)
        elif args[0] == '-kb':
            args = args[1:]
            keepbin = True
        else:
            return (False, 0,0,0,0,0)
    return (True, sn, p, phigh, fn, keepbin)

def _checkname(args):
    if len(args) > 1:
        return (args[2:], args[1])
    else:
        return (['X'],None)

def _checkpin(args):
    if len(args) == 1:
        return(['X'], None, None)
    elif args[1] == '-h' and len(args) > 2:
        return(args[3:], int(args[2]), True)
    else:
        return(args[2:], int(args[1]), False)

def printcommands():
    print("arg options, must use one:")
    print("\t-sn {serial number} : specify serial number")
    print("\t-p [-h] {pin} : specify pin, optional set high (default low)")
    print("\t-b : for blank userpage")
    print("\t-f {filename} : specify filename - noextension")
    print("\t-kb : specify to keep binary intermediate")


if __name__=="__main__":
    log.basicConfig(level=log.DEBUG)
    if len(sys.argv) > 1:
        success, sn, pin, high, fn, keepbin = parseargs(sys.argv[1:])
        if success:
            makeuser(sn, pin, high, fn, keepbin)
        else:
            printcommands()
    else:
        printcommands()
