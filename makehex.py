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
# FIXME : for some reason i'm getting an error with line endings using DFU-prog.
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


if __name__=="__main__":
    log.basicConfig(level=log.DEBUG)
    sys.argv



