#!/bin/bash

NEW_VERSION=4.4.3-rbl
OLD_VERSION=4.3

for DEV in silk snowy_dvt snowy_s3 spalding; do
	./patchpbz.py -v v$NEW_VERSION -b Pebble-$OLD_VERSION-$DEV.pbz out/Pebble-$NEW_VERSION-$DEV.pbz -t tzdata.bin.reso --license rbl-license.txt
done

./patchpbz.py -v v$NEW_VERSION-3v7 -b Pebble-4.3-silk.pbz out/Pebble-$NEW_VERSION-silk-3v7.pbz -t tzdata.bin.reso --license rbl-license.txt --silk-3v7

NEW_VERSION_V3=3.13.3-rbl
OLD_VERSION_V3=3.12.3

for DEV in v2_0 v1_5 ev2_4; do
	./patchpbz.py -v v$NEW_VERSION_V3 -b Pebble-$OLD_VERSION_V3-$DEV.pbz out/Pebble-$NEW_VERSION_V3-$DEV.pbz -t tzdata.bin.reso --license rbl-license.txt
done
