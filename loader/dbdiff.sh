#!/bin/bash
#
# compare two data releases, based on the summary
# sqlite databases. Takes two arguments as input,
# the old and enw db releases eg r1b25 and r2b2.
# these are assumed to have been dumped into
# ${HOME}/db_summary. The resulting report is
# written into ${HOME}/db_summary_reports/r1b25_vs_r2b2 as
# they are being built, and then copied into the webservers 
# directory when completed

PYTHON=python

PYTHONPATH=src/main/python/dbstats

BASE_SUMMARY_DIR=${HOME}/dev/db_summary
BASE_REPORT_DIR=${BASE_SUMMARY_DIR}/reports

#PUBLISH_DIR=/Library/WebServer/Documents/genemania_data_reports
PUBLISH_DIR=genemania_data_reports

# two releases, eg r1b25 and r2b2
DB_OLD=$1
DB_NEW=$2

 
SUMMARY_DIR_OLD=${BASE_SUMMARY_DIR}/${DB_OLD}
SUMMARY_DIR_NEW=${BASE_SUMMARY_DIR}/${DB_NEW}

REPORT_DIR=${BASE_REPORT_DIR}/${DB_OLD}_vs_${DB_NEW}


# remove the old report folder
#rm -rf ${REPORT_DIR}


# load into sqlite

PYTHONPATH=$PYTHONPATH $PYTHON -m dbdiff ${SUMMARY_DIR_OLD} ${SUMMARY_DIR_NEW} ${REPORT_DIR}

#pushd $PYTHONPATH
#$PYTHON dbdiff.py ${SUMMARY_DIR_OLD} ${SUMMARY_DIR_NEW} ${REPORT_DIR}
#popd


# copy to webserver
cp -r ${REPORT_DIR} ${PUBLISH_DIR}
