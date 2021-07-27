#!/bin/bash

# Import data that isn't going to change in the future. This is stored in
# our mirrored database

echo "Importing static data."

# if db.cfg is provided as the first argument, assume the user
# wants to refresh bp.cfg
if [[ ! -z $1 ]]; then 
	python create_config.py $1
fi

./check.sh
if [[ $? -eq 1 ]]; then
	exit 1
fi

source bp.cfg
start=`date`

mkdir -p ${SRCDB}/data
pushd ${DBMIRROR}/${STATIC_DATA}

for i in *; do
	echo "[Copying $i to ${SRCDB}/data]"
	cp -r $i ${SRCDB}/data
done

popd

echo "[Importing static data completed]"
stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
