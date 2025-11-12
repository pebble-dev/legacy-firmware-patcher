#!/bin/bash

NEW_VERSION=4.4.3-rbl

for DEV in silk snowy_dvt snowy_s3 spalding; do
	aws s3 cp --profile rebble --acl public-read out/Pebble-$NEW_VERSION-${DEV}.pbz s3://rebble-binaries/fw/${DEV}/
done


NEW_VERSION_V3=3.13.3-rbl

for DEV in v2_0 v1_5 ev2_4; do
	aws s3 cp --profile rebble --acl public-read out/Pebble-$NEW_VERSION_V3-${DEV}.pbz s3://rebble-binaries/fw/${DEV}/
done
