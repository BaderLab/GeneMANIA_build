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

source ./bp.cfg
start=`date`

echo ${CODE_DIR}
cd ${CODE_DIR}/loader

#compile the jar
mvn -Dmaven.repo.local=$HOME/.m2/repository clean install assembly:single

echo "[pipelined geomap]"
echo "./r.sh pipeline ${SRCDB}/db.cfg anno"
./r.sh pipeline ${SRCDB}/db.cfg

stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
