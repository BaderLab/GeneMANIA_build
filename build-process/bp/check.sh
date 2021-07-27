#!/bin/bash

source bp.cfg

#ps a | grep -v grep | grep runbp.py 2>&1 > /dev/null
#if [[ $? -eq 0 ]]; then 
#	echo "A build is already running!"
#	exit 1
#fi

fail=0

printf "Checking for unrar..."
which unrar 2>&1 > /dev/null
if [[ $? -eq 1 ]]; then
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

printf "Checking for python..."
which python 2>&1 > /dev/null
if [[ $? -eq 1 ]]; then
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

printf "Checking for pymysql"
python -c "import pymysql"
if [[ $? -eq 1 ]]; then
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

# TODO: remove this test when all scripts
# updated to using pymysql
printf "Checking for mysql-python..."
python -c "import MySQLdb"
if [[ $? -eq 1 ]]; then 
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

printf "Checking for configobj..."
python -c "import configobj"
if [[ $? -eq 1 ]]; then 
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

printf "Checking for ruffus..."
python -c "import ruffus"
if [[ $? -eq 1 ]]; then
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

printf "Checking for pandas..."
python -c "import pandas"
if [[ $? -eq 1 ]]; then
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

printf "Checking for genemania-engine..."
if [[ ! -d "${HOME}/.m2/repository/org/genemania/genemania-engine" ]]; then 
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

printf "Checking for genemania-common..."
if [[ ! -d "${HOME}/.m2/repository/org/genemania/genemania-common" ]]; then 
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

printf "Checking for plugin-distribution..."
if [[ ! -d "${HOME}/.m2/repository/org/genemania/plugin-distribution" ]]; then 
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

printf "Checking for $RESOURCE_DIR..."
if [[ ! -d $RESOURCE_DIR ]]; then
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

printf "Checking for $DBMIRROR..."
if [[ ! -d $DBMIRROR ]]; then 
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

# These were only used by the old ID Mapper
#printf "Checking for $DBMIRROR/$ENSEMBL_CORE..."
#if [[ ! -d $DBMIRROR/$ENSEMBL_CORE ]]; then 
#	printf " not found!\n"
#	fail=1
#else
#	printf " OK!\n"
#fi
#
#printf "Checking for $DBMIRROR/$ENSEMBL_PLANTS..."
#if [[ ! -d $DBMIRROR/$ENSEMBL_PLANTS ]]; then 
#	printf " not found!\n"
#	fail=1
#else
#	printf " OK!\n"
#fi
#
#printf "Checking for $DBMIRROR/$ENTREZ_FILES..."
#if [[ ! -d $DBMIRROR/$ENTREZ_FILES ]]; then 
#	printf " not found!\n"
#	fail=1
#else
#	printf " OK!\n"
#fi

printf "Checking for $DBMIRROR/$STATIC_DATA..."
if [[ ! -d $DBMIRROR/$STATIC_DATA ]]; then 
	printf " not found!\n"
	fail=1
else
	printf " OK!\n"
fi

if [[ $fail -eq 1 ]]; then
	echo "One or more required dependencies were not found."
	echo "Install all required dependencies before continuing."
	exit 1
fi
