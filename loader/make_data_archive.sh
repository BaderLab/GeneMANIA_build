#!/bin/bash
#
# create a dataset archive for upload to website
# takes version string as input, assumes lucene index
# and network cache is under DBBUILD_DIR, and creates
# output archive folder under REPORTDIR.

#this is eg r1b25
DBVER=$1
DBBUILD_DIR=/usr/local/genemania/db_build
REPORTDIR=~/publish_report

java -Xmx1024m -cp target/genemania-loader-*-jar-with-dependencies.jar org.genemania.engine.apps.DatasetPublisher -cachedir ${DBBUILD_DIR}/${DBVER}/network_cache -indexDir ${DBBUILD_DIR}/${DBVER}/lucene_index -log ${REPORTDIR}/publish_${DBVER}.log -reportDir ${REPORTDIR}
