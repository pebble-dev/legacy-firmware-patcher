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

parser = argparse.ArgumentParser(description = "tintin_fw patch tool")
parser.add_argument("-b", "--bluetooth", action = 'store_true', help = "fix Bluetooth LE constants")
parser.add_argument("-v", "--version", nargs = 1, help = "new version number")
parser.add_argument("fwin", help = "template tintin_fw file")
parser.add_argument("fwout", help = "output tintin_fw file")
args = parser.parse_args()

with open(args.fwin, "rb") as f:
    data = f.read()

if args.version:
    oldvers = data[-43:-11]
    print("replacing old version \"%s\" with \"%s\"" % (oldvers.replace("\x00",""), args.version[0]))
    data = data.replace(oldvers, args.version[0].ljust(32, "\x00"))

if args.bluetooth:
    BLUETOOTH_OLD = "\x09\x00\x11\x00\x00\x00\x58\x02"
    BLUETOOTH_NEW = "\x0F\x00\x1E\x00\x00\x00\x58\x02"
    print("patching bluetooth constants")
    if data.find(BLUETOOTH_OLD) == -1:
        print("WARNING: bluetooth constants not found?")
    data = data.replace(BLUETOOTH_OLD, BLUETOOTH_NEW)

with open(args.fwout, "wb") as f:
    f.write(data)
