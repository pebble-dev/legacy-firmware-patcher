#!/usr/bin/env python

__author__ = "Joshua Wise <joshua@joshuawise.com>"

from stm32_crc import crc32
import struct

TAB_OFS = 0x0C
RES_OFS = 0x200C

def verif_pbpack(fname, unpdir = None, quiet=False):
    rsrcs = []

    if type(fname) == str:
        fd = open(fname, 'rb')
    else:
        fd = fname

    nrsrcs, crc = struct.unpack('II', fd.read(8))
    
    # Verify the CRC.
    fd.seek(RES_OFS)
    alldata = fd.read()
    dcrc = crc32(alldata)
    if crc == dcrc:
        if not quiet:
            print("OK: file CRC matches");
    else:
        print("ERR: file CRC mismatch: %x vs %x" % (crc, dcrc))
    
    for rsrc in range(nrsrcs):
        fd.seek(TAB_OFS + rsrc * 16)
        idx, ofs, size, crc = struct.unpack("iiiI", fd.read(16))
        
        fd.seek(RES_OFS + ofs)
        data = fd.read(size)
        dcrc = crc32(data)
        
        if crc == dcrc:
            if not quiet:
                print("OK: resource %d (idx %d), ofs %d, size %d, crc %x" % (rsrc, idx, ofs, size, crc))
        else:
            print("ERR: resource %d (idx %d), ofs %d, size %d, crc %x != computed crc %x" % (rsrc, idx, ofs, size, crc, dcrc))
        
        rsrcs.append(data)
        if unpdir is not None:
            with open('%s/%03d' % (unpdir, idx), 'wb') as ofd:
                ofd.write(data)
    
    fd.seek(0)
    wholecrc = crc32(fd.read())
    if not quiet:
        print("Whole file CRC is %x (%d)" % (wholecrc, wholecrc)) 
    
    if type(fname) == str:
        fd.close()
    
    return rsrcs

def main():
    """
    Command-line driver.
    """
    
    import argparse
    parser = argparse.ArgumentParser(description = "Resource pack verifier.")
    parser.add_argument("name", help = "filename to verify")
    parser.add_argument("-u", "--unpack", nargs = 1, default = None, help = "directory to unpack to")
    args = parser.parse_args()
    
    if args.unpack:
        verif_pbpack(args.name, args.unpack[0])
    else:
        verif_pbpack(args.name)

if __name__ == '__main__':
    main()
