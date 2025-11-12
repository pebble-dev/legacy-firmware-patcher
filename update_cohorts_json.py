#!/usr/bin/env python3

"""
Update the cohorts config.json for the contents of out/.
Rebble Foundation

This is an astonishing hack.  But it is what it is.
"""

__author__ = "Joshua Wise <joshua@joshuawise.com>"

import os
import re
import sys
import json
import zipfile
import hashlib

OUTPATH = sys.argv[1]
CONFIG_JSON = sys.argv[2]

# come up with platforms and versions.  this overkills on silk-3v7, but we
# ignore that later anyway, so it's ok
platforms = {}
for filename in os.listdir(OUTPATH):
    vers,plat = re.match(r"Pebble-(.+)-(.+)\.pbz", filename).groups()
    platforms[plat] = { 'version': vers, 'filename': filename }

print(platforms)

with open(CONFIG_JSON, 'r') as f:
    config = json.load(f)

for hw in config['hardware']:
    if hw not in platforms:
        continue
    vers,filename = platforms[hw]['version'], platforms[hw]['filename']

    print(f"updating hardware {hw} -> {vers}")
    if vers not in config['notes']:
        config['notes'][vers] = "*** WRITE RELEASE NOTES HERE, YA GOOFBALL ***"
    
    with zipfile.ZipFile(f"{OUTPATH}/{filename}", "r") as zf:
        with zf.open("manifest.json", "r") as mf:
            manifest = json.load(mf)
    ts = manifest['firmware']['timestamp']
    if vers not in config['timestamps'] or ts < config['timestamps'][vers]:
        print(f"resetting {vers} ts to {ts}")
        config['timestamps'][vers] = ts
    
    with open(f"{OUTPATH}/{filename}", "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    
    config['hardware'][hw]['normal'] = { 'version': vers, 'sha-256': sha }

with open(CONFIG_JSON, 'w') as f:
    json.dump(config, f, indent=2)
