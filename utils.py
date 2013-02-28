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

def parseCFGword(filename="ispcfg.bin",display=True):
    """
    shows information about the config file and returns the word as bytes
    """
    with open(filename,'rb') as fh:
        data = fh.read()
    values = [ord(c) for c in data]
    if display:
        word = ["{0:0>2X}".format(v) for v in values]
        print("WORD is: 0x {0} {1} {2} {3}".format(*word))
        pin = values[2]
        val = values[1]%2
        print("IO Condition: Pin {0} {1}".format(pin, "High" if val else "Low"))
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

def commandhelp():
    command = ["avr32program","help","commands"]
    call(command)

def optionshelp():
    command = ["avr32program", "-h"]
    call(command)

def getStatus():
    command = ["avr32program", "status"]
    call(command)

def cpuinfo(full=False):
    command = ["avr32program", "cpuinfo"]
    if full: command.append("-F")
    call(command)

def chiperase(full=False):
    """
    call a chiperase
    """
    command = ["avr32program","chiperase"]
    if full: command.append("-F")
    call(command)

def flashBootloader(filename="at32uc3b-isp-1.0.3.bin"):
    """
    load the bootloader file (bootloader binary is at filename)
    """
    command = ["avr32program", "program",
            "-Fbin",
            "-O0x80000000",
            "-v",
            "-finternal@0x80000000",
            "-e",
            "-cxtal",
            filename]
    call(command)

def flashCFGword(filename="ispcfg.bin"):
    """
    flash the user page with the binary file provided
    """
    command = ["avr32program", "program",
            "-Fbin",
            "-O0x808001FC",
            "-v",
            "-finternal@0x80000000",
            "-e",
            "-cxtal",
            filename]
    value = parseCFGword(filename)
    call(command)

def writefuses(fuses='0xFC07FFFF'):
    """
    write the fuses word provided
    """
    command = ["avr32program", "writefuses",
            "-f internal@0x80000000", 
            fuses]
    call(command)

def readfuses():
    command = ["avr32program", "readfuses",
            "-f internal@0x80000000",
            "gp"]
    call(command)

def lsusb(grep="03eb"):
    """
    doesn't work
    """
    command = ["lsusb", "|", "grep", grep]
    call(command)

def viewuser(filename="userpage.bin", cols=16):
    """
    used to view the contents of the user page in hex format
    """
    with open(filename, 'rb') as fh:
        page = fh.read()
    if len(page) != 512: log.warn("User page should be 512 bytes")
    for k in range((512+cols-1)//cols):
        print ("{0:0>2X}: ".format(k), end="")
        for i in range(cols):
            print ("{0:0>2X} ".format(ord(page[i+k*cols])), end="")
        print("")

def makeUser(word, filename='userpage.bin'):
    """
    puts the value for word in the last 4 bytes of the 512 byte user page
    """
    page = bytearray([0xFF]*512)
    revword = list(word)
    revword.reverse()
    for i, b in enumerate(revword):
        page[-1-i] = b
    with open(filename, 'wb') as fh:
        fh.write(page)

def makeHex(binfile="userpage.bin", hexfile="userpage.hex", cols=16):
    """
    make an intel hex file from a binary
    assumes 16 bytes per field - don't use 32
    see wikipedia page for translation
    """
    with open(binfile, 'rb') as fh:
        page = fh.read()
    if len(page) != 512: log.warn("User page should be 512 bytes")
    recordtype = 0          # 0-5, 0 is data
    lines = [":020000048080FA"]
    for k in range((512+cols-1)//cols):
        values = [cols, (k*cols)//256, (k*cols)%256, recordtype]
        line = [":{0:0>2X}{1:0>2X}{2:0>2X}{3:0>2X}".format(*values)]
        for i in range(cols):
            value = ord(page[i+k*cols])
            values.append(value)
            line.append("{0:0>2X}".format(value))
#        checksum = (((sum(values) & 0xFF) ^ 0xFF) + 0x01) & 0xFF
        checksum = (0x100 - (sum(values) % 0x100)) & 0xFF
#        thecheck = (sum(values) + checksum) & 0xFF
#        if thecheck > 0:
#            raise ValueError ("you fucked up on line {0}".format(k))
        line.append("{0:0>2X}".format(checksum))
        lines.append("".join(line))
    lines.append(":00000001FF")
    with open(hexfile, 'wb') as fh:
        fh.write("\n".join(lines))

def makeBin(binfile="userpage.bin", hexfile="userpage.hex"):
    """
    make a binary file from an intel hex file
    """
    pass


if __name__=="__main__":
    log.basicConfig(level=log.DEBUG)


