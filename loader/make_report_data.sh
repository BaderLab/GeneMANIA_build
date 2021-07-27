#!/bin/bash
#
# create summary data used for reporting differences
# between database release. Takes as input the 
# result of a build process, eg r1b25, assumed to be
# in /usr/local/genemania/db_build/r1b25
# and writes summary data to a new folder, ${HOME}/db_summary/r1b25
#

PYTHON=python

PYTHONPATH=src/main/python/dbstats

BASE_SUMMARY_DIR=${HOME}/dev/db_summary
BASE_DB_BUILD_DIR=/gm/db_build

# this is eg r1b25
DB=$1

 
SUMMARY_DIR=${BASE_SUMMARY_DIR}/${DB}
DB_BUILD_DIR=${BASE_DB_BUILD_DIR}/${DB}



# remove the old report folder
#rm -rf ${SUMMARY_DIR}

# dump out the data
echo "java -cp target/genemania-loader-*-jar-with-dependencies.jar org.genemania.engine.apps.DatasetSummarizer -cachedir ${DB_BUILD_DIR}/network_cache -indexDir ${DB_BUILD_DIR}/lucene_index -log target/${DB}.log -reportDir $SUMMARY_DIR"
java -cp target/genemania-loader-*-jar-with-dependencies.jar org.genemania.engine.apps.DatasetSummarizer -cachedir ${DB_BUILD_DIR}/network_cache -indexDir ${DB_BUILD_DIR}/lucene_index -log target/${DB}.log -reportDir $SUMMARY_DIR

# load into sqlite
PYTHONPATH=$PYTHONPATH $PYTHON -m buildstatsdb ${SUMMARY_DIR}
