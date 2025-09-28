#!/usr/bin/env python3

"""
Patches a Pebble Technology Corp firmware into the future.
Rebble Foundation
"""

__author__ = "Joshua Wise <joshua@joshuawise.com>"

from stm32_crc import crc32
import json
import argparse
import zipfile
import time
import os
import struct
import io
import binascii
import pickle

from mkpack import save_pbpack 
from verifpack import verif_pbpack

parser = argparse.ArgumentParser(description = "Firmware patcher tool.")
parser.add_argument("-v", "--version", nargs = 1, help = "new version number")
parser.add_argument("-r", "--respack", nargs = 1, help = "resource pack")
parser.add_argument("-b", "--bluetooth", action = 'store_true', help = "fix Bluetooth LE constants")
parser.add_argument("-t", "--tzdata", nargs = 1, help = "new timezone database")
parser.add_argument("--silk-3v7", action = 'store_true', help = "replace Silk battery percentage table with constants for 3.7V cell")
parser.add_argument("-l", "--license", nargs = 1, help = "new license file")
parser.add_argument("pbzin", help = "template PBZ file")
parser.add_argument("pbzout", help = "output PBZ file")
args = parser.parse_args()

FIRMWARE_NAME = "tintin_fw.bin"
RESPACK_NAME = "system_resources.pbpack"

def populate(manifest, what, filename):
    with open(filename, "rb") as f:
        stat = os.fstat(f.fileno())
        data = f.read()
    manifest[what]["crc"] = crc32(data)
    manifest[what]["size"] = len(data)
    manifest[what]["timestamp"] = int(stat.st_mtime)
    return data, int(stat.st_mtime)

zin = zipfile.ZipFile(args.pbzin, "r")

z = zipfile.ZipFile(args.pbzout, "w", zipfile.ZIP_STORED)

# Copy everything over.
badfiles = [ "manifest.json" ]
if args.license:
    badfiles += ["LICENSE.txt"]
badfiles.append(FIRMWARE_NAME)
badfiles.append(RESPACK_NAME)
for f in zin.namelist():
    if f in badfiles:
        continue
    z.writestr(f, zin.read(f))
    print("copied %s" % f)

if args.license:
    with open(args.license[0], "rb") as f:
       data = f.read()
    z.writestr("LICENSE.txt", data)
    print("added custom license")

manifest = json.loads(zin.read("manifest.json"))

orig_res_data = zin.read(RESPACK_NAME)
orig_res_data_crc = orig_res_data[4:8]
print(f"original respack internal crc was     {binascii.hexlify(orig_res_data_crc).decode()}, size {len(orig_res_data)}")

rfile = io.BytesIO(orig_res_data)
rsrcs = verif_pbpack(rfile, quiet=True)

if args.tzdata:
    # you need pebbleos/tools in your PYTHONPATH for this (or 'pebbleos/tools/resources' symlinked in here)
    import resources
    import pickle

    for rn, data in enumerate(rsrcs):
        if b'Antarctica/McMurdo' in rsrcs[rn]:
            with open(args.tzdata[0], 'rb') as tzf:
                tzdb = pickle.load(tzf)
            rsrcs[rn] = tzdb.data
            print(f"replaced resource {rn} length {len(data)} {data[:16]} with new tzdata length {len(rsrcs[rn])} {rsrcs[rn][:16]}, thanks Steve!")

new_rfile = io.BytesIO()
save_pbpack(new_rfile, rsrcs)

res_data = new_rfile.getvalue()
res_ts = int(time.time())
res_data_crc = res_data[4:8]

manifest["resources"]["crc"] = crc32(res_data)
manifest["resources"]["size"] = len(res_data)
manifest["resources"]["timestamp"] = res_ts

z.writestr(RESPACK_NAME, res_data)
print(f"stored new respack, with internal crc {binascii.hexlify(res_data_crc).decode()}, size {len(res_data)}")

# Patch firmware.
fw_data = zin.read(FIRMWARE_NAME)
fw_ts = int(time.time())

if args.version:
    oldvers = fw_data[-43:-11]
    print("replacing old version \"%s\" with \"%s\"" % (oldvers.replace(b"\x00",b"").decode(), args.version[0]))
    fw_data = fw_data.replace(oldvers, args.version[0].encode().ljust(32, b"\x00"))

if args.silk_3v7:
    OLD_CONSTS = bytes.fromhex("""
00 00 e4 0c 02 00 a2 0d  05 00 1f 0e 0a 00 47 0e
14 00 74 0e 1e 00 97 0e  28 00 b0 0e 32 00 d8 0e
3c 00 0f 0f 46 00 5f 0f  50 00 b9 0f 5a 00 18 10
64 00 86 10 01 00 01 01  01 01 18 ff 01 01 ff 06
""")
    NEW_CONSTS = bytes.fromhex("""
00 00 1c 0c 02 00 52 0d  05 00 10 0e 0a 00 56 0e
14 00 7e 0e 1e 00 a1 0e  28 00 bf 0e 32 00 e2 0e
3c 00 14 0f 46 00 55 0f  50 00 a0 0f 5a 00 f0 0f
64 00 18 10 01 00 01 01  01 01 18 ff 01 01 ff 06
""")
    print("patching silk battery percentage table to 3.7V")
    if fw_data.find(OLD_CONSTS) == -1:
        print("WARNING: silk battery table not found?")
    fw_data = fw_data.replace(OLD_CONSTS, NEW_CONSTS)

if args.bluetooth:
    BLUETOOTH_OLD = b"\x09\x00\x11\x00\x00\x00\x58\x02"
    BLUETOOTH_NEW = b"\x0F\x00\x1E\x00\x00\x00\x58\x02"
    print("patching bluetooth constants")
    if fw_data.find(BLUETOOTH_OLD) == -1:
        print("WARNING: bluetooth constants not found?")
    fw_data = fw_data.replace(BLUETOOTH_OLD, BLUETOOTH_NEW)

# Replace CRCs.
ofs = fw_data.find(orig_res_data_crc)
while ofs != -1:
    print("found old respack CRC in firmware at offset 0x%x" % ofs)
    ofs = fw_data.find(orig_res_data_crc, ofs+1)
fw_data = fw_data.replace(orig_res_data_crc, res_data_crc)
    
# Replace in-image timestamp.
fw_data = fw_data[:-47] + struct.pack("<I", fw_ts) + fw_data[-43:]

z.writestr(FIRMWARE_NAME, fw_data)
print("stored new firmware")

manifest["firmware"]["crc"] = crc32(fw_data)
manifest["firmware"]["size"] = len(fw_data)
manifest["firmware"]["timestamp"] = fw_ts

if args.version:
    manifest['firmware']['versionTag'] = args.version[0]

manifest['generatedBy'] = 'your friends at the Rebble Alliance'

z.writestr("manifest.json", json.dumps(manifest, indent=4, separators=(',', ': ')))
z.close()
