HOW TO RUN IT:

rm out/*
./patch_all.sh
./upload_all.sh (make sure your AWS creds are working...)
./update_cohorts_json.py out ../../rws/rebble-cohorts/config.json
