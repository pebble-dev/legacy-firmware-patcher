#!/usr/bin/env python

__author__ = "Joshua Wise <joshua@joshuawise.com>"

from stm32_crc import crc32
import struct
import json
import os

TAB_OFS = 0x0C
RES_OFS = 0x200C

def save_pbpack(fname, rsrcs):
    """
    Outputs a handful of resources to a file.
    
    |rsrcs| is a list of resources, with the first mapping to resource index
    "1".  Although the PebbleOS resource structure permits a sparse mapping
    -- i.e., one in which one must read the whole resource table to find the
    index that one desires -- the RebbleOS resource loader simply ignores
    the ID number in each table entry, and indexes directly in to find what
    it wants.  (And, further, every Pebble pbpack that I can find only has
    them in order.)  So we, in keeping, will only generate things like that.
    
    """
    
    # First, turn the resource table into a list of entries, including
    # index, offset, size, and CRC.
    def mk_ent(data):
        ent = { "idx": mk_ent.idx, "offset": mk_ent.offset, "size": len(data), "crc": crc32(data), "data": data }
        mk_ent.offset += len(data)
        mk_ent.idx += 1
        return ent
    mk_ent.offset = 0
    mk_ent.idx = 1
    rsrc_ents = [ mk_ent(data) for data in rsrcs ]
    
    with open(fname, 'w+') as fd:
        fd.write(struct.pack('I', len(rsrc_ents))) # Number of resources.
        # We'll come back to the big CRC later.
        
        # Write out the table.
        fd.seek(TAB_OFS)
        for ent in rsrc_ents:
            fd.write(struct.pack('iiiI', ent["idx"], ent["offset"], ent["size"], ent["crc"]))
        
        # Write out the resources themselves.
        for ent in rsrc_ents:
            fd.seek(RES_OFS + ent["offset"])
            fd.write(ent["data"])
        
        # Now compute the CRC of the whole show.
        fd.seek(RES_OFS)
        alldata = fd.read()
        
        totlen = fd.tell()
        
        fd.seek(4)
        fd.write(struct.pack('I', crc32(alldata)))
    
    return totlen

def main():
    """
    Command-line driver.
    """
    
    import argparse
    
    parser = argparse.ArgumentParser(description = "Resource pack generator for RebbleOS.")
    parser.add_argument("pack", help = "output pack file name")
    parser.add_argument("dir", help = "directory to pack from")
    args = parser.parse_args()
    
    files = os.listdir(args.dir)
    files.sort()
    
    def readfile(fn):
        with open(fn, 'rb') as fd:
            return fd.read()
    
    fdata = [readfile("%s/%s" % (args.dir, fn)) for fn in files]
    bytes = save_pbpack(args.pack, fdata)
    print("wrote %s (%d bytes)" % (args.pack, bytes))

if __name__ == '__main__':
    main()
