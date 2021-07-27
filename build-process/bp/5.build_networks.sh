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

cd ${CODE_DIR}/loader

export JAVA_HOME=`/usr/libexec/java_home`
export MAVEN_OPTS="-Xmx1g"

echo "JAVA_HOME: $JAVA_HOME"
echo "MAVEN_OPTS: $MAVEN_OPTS"

#echo "[Running mvn assembly:single]"
#mvn clean compile assembly:single
#if [[ $? -ne 0 ]]; then
#	./send_email.sh $EMAIL_TO builder@baderlab.org "mvn assembly failed" "mvn assembly failed"
#	exit 1
#fi

echo "[Process antologies]"
mkdir -p ${SRCDB}/ontologies
mkdir -p ${SRCDB}/ontologies/raw
mkdir -p ${SRCDB}/ontologies/processed

echo "[Filter annotations]"
./r.sh filter_go_annotations ${SRCDB}/db.cfg

echo "[pipelined geomap+p2n+nn]"
./r.sh pipeline ${SRCDB}/db.cfg

echo "[Network numbering]"
./r.sh enumerate_networks ${SRCDB}/db.cfg clear 
./r.sh enumerate_networks ${SRCDB}/db.cfg enumerate 

stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
