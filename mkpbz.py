#!/usr/bin/env python

"""
Builds a firmware image zipball.
RebbleOS
"""

__author__ = "Joshua Wise <joshua@joshuawise.com>"

from stm32_crc import crc32
import json
import argparse
import zipfile
import time
import os
import struct

parser = argparse.ArgumentParser(description = "Firmware repack tool.")
parser.add_argument("-f", "--firmware", nargs = 1, help = "tintin_fw.bin image")
parser.add_argument("-v", "--version", nargs = 1, help = "new version number")
parser.add_argument("-r", "--respack", nargs = 1, help = "resource pack")
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
if args.firmware:
    badfiles.append(FIRMWARE_NAME)
if args.respack:
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

if args.respack:
    orig_res_data = zin.read(RESPACK_NAME)
    orig_res_data_crc = orig_res_data[4:8]
    print("original respack internal crc was:    %02x %02x %02x %02x" % tuple([ord(i) for i in orig_res_data_crc]))
    
    res_data, res_ts = populate(manifest, "resources", args.respack[0])
    res_data_crc = res_data[4:8]
    z.writestr(RESPACK_NAME, res_data)
    print("stored new respack, with internal crc %02x %02x %02x %02x" % tuple([ord(i) for i in res_data_crc]))

if args.firmware:
    fw_data, fw_ts = populate(manifest, "firmware", args.firmware[0])
    
    # Replace CRCs.
    if args.respack:
        ofs = fw_data.find(orig_res_data_crc)
        while ofs != -1:
            print("found old respack CRC in firmware at offset 0x%x" % ofs)
            ofs = fw_data.find(orig_res_data_crc, ofs+1)
        fw_data = fw_data.replace(orig_res_data_crc, res_data_crc)
    
    # Replace in-image timestamp.
    fw_data = fw_data[:-47] + struct.pack("<I", fw_ts) + fw_data[-43:]

    manifest['firmware']['crc'] = crc32(fw_data)
    z.writestr(FIRMWARE_NAME, fw_data)
    print("stored new firmware")

if args.version:
    manifest['firmware']['versionTag'] = args.version[0]

manifest['generatedBy'] = 'your friends at the Rebble Alliance'

z.writestr("manifest.json", json.dumps(manifest, indent=4, separators=(',', ': ')))
z.close()
