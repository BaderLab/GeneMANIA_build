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

echo "[Deleting ${SRCDB}/generic_db]"
rm -rf ${SRCDB}/generic_db

echo "[Loading attributes]"
./r.sh attribute_processor ${SRCDB}/db.cfg load

echo "[Extract data to generic_db]"
./r.sh extract -i copy ${SRCDB}/db.cfg

echo "[Extracting attributes]"
./r.sh attribute_processor ${SRCDB}/db.cfg export

stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
