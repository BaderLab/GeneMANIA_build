#!/bin/bash

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

ASSOCDB=""
go=${RESOURCE_DIR}/go
gobuild=${BUILD_DIR}/go

#if [[ ! -d $go ]]; then
#	go_notfound
#	exit 1
#fi


start=`date`
mkdir -p $go
mkdir -p $gobuild

cd ${CODE_DIR}/loader

echo "[Creating Up-propagated GO annotations from GO obo and GAF downloads]"
./r.sh query_go_annotations_goatools ${SRCDB}/db.cfg
wait

stop=`date`

echo "Start: $start"
echo "Stop : $stop"
