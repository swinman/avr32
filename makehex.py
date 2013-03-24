""""
a python script for making a hex file from a binary file
"""

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals
from future_builtins import (ascii, filter, hex, map, oct, zip)

import logging as log
import sys
import os


def makehex(binfile="program.bin", hexfile=None, offset=0x80000000, cols=16):
    """
    make an intel hex file from a binary
    see wikipedia page for translation
    start is the starting address in memory
    cols is either 16 or 32, if hexfile is not provided same file name is used
    with .hex extension instead of binary
    """
    if hexfile is None:
        hexfile = '.'.join([os.path.splitext(binfile)[0], "hex"])
    with open(binfile, 'rb') as fh:
        page = fh.read()
    lines = [_ihex_make04offset(offset)]
    reladdress = offset
    offsetaddress = offset
    values = [0, 0, 0]
    nremain = cols
    for k, v in enumerate(page):
        reladdress = k + offset
        if reladdress - offsetaddress == 0x10000:
            # finish the current line
            lines.append( _ihex_makeline(values) )
            values = [0, 0, 0]
            nremain = cols
            # start new offset
            offsetaddress = reladdress
            lines.append( _ihex_make04offset(offsetaddress) )
        if nremain == 0:
            lines.append( _ihex_makeline(values) )
            values = [(0xFF & ((reladdress - offsetaddress) >> 8)), 
                    (0xFF & (reladdress - offsetaddress)), 0]
            nremain = cols
        values.append( ord(v) )
        nremain -= 1
    if len(values) > 3: lines.append( _ihex_makeline(values) )
    lines.append(":00000001FF\n")
    with open(hexfile, 'w') as fh:
        fh.write("\n".join(lines))

def _ihex_make04offset(offset):
    """
    use to create an ihex offset
    """
    if offset % 0x10000:
        raise ValueError ("offset must")
    values = [0, 0, 4]
    values.append(0xFF & (offset>>24))
    values.append(0xFF & (offset>>16))
    return _ihex_makeline(values)

def _ihex_makeline(values):
    """
    values are the 2 address bytes, the record type and any values
    append a checksum and prepend number of bytes
    return an ihex formatted line from a list of values
    """
    lendata = len(values) - 3
    try:
        checksum = (0x100 - ((sum(values) + lendata) % 0x100)) & 0xFF
    except TypeError:
        print(values)
    values.append(checksum)
    line = [ ":{0:0>2X}".format(lendata) ]
    for v in values:
        line.append( "{0:0>2X}".format(v) )
    return( "".join(line) )

def parseargs(args):
    """
    parse argument options 
    $ makehex [optional args] {binary filename}
    optional args include: 
        -h {filename} : specify the hex file to create, default bin name
        -o {offset} : specify an offset, default 0x80000000
        -c {columns} : specify number of columns, default 16
    """
    if not len(args):
        return(False, 0,0,0,0)

    binfile = args[-1]
    if not os.path.exists(binfile):
        print ("binary file {0} does not exist".format(binfile))
        return(False, 0,0,0,0)
    args = args[:-1]

    hexfile = None
    offset = 0x80000000
    cols = 16

    while (len(args)):
        if args[0] == '-h':
            args, hexfile = _checkname(args)
        elif args[0] == '-o':
            args, offset = _checkoffset(args)
        elif args[0] == '-c':
            args, cols = _checkcols(args)
        else:
            return (False, 0,0,0,0)
    return (True, binfile, hexfile, offset, cols)


def _checkname(args):
    if len(args) > 1:
        hexfile = args[1]
#TODO : check that the path is a valid path.. how?
        return (args[2:], hexfile)
    else:
        return(['X'], None)

def _checkoffset(args):
    if len(args) > 1:
        offset = int(args[1])
        if offset < 0:
            print("offset must be positive")
            return(['X'], None)
        return(args[2:], offset)
    else:
        return(['X'], None)

def _checkcols(args):
    if len(args) > 1:
        cols = int(args[1])
        if not ((cols == 16) or (cols == 32)):
            print("cols must be 16 or 32")
            return(['X'], None)
        return(args[2:], cols)
    else:
        return(['X'], None)

def printcommands():
    print("makehex [optional args] {binary filename}")
    print("arg format options:")
    print("\t-h {filename} : specify the hex file to create, default bin name")
    print("\t-o {offset} : specify an offset, default 0x80000000")
    print("\t-c {columns} : specify number of columns, default 16")


if __name__=="__main__":
    log.basicConfig(level=log.DEBUG)
    if len(sys.argv) > 1:
        success, binfile, hexfile, offset, cols = parseargs(sys.argv[1:])
        if success:
            makehex(binfile, hexfile, offset, cols)
        else: 
            printcommands()
    else:
        printcommands()
