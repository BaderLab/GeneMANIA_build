#!/bin/bash

# This script goes through each of the ensembl directories in the tmp_ensembl directory
# creates a database the same name as the directory name
# and loads all the tables into the database using mysqlimport 
#
# mysqlimport is not useable in mysql 8 and later.  It was deemed a security risk. 
# to use mysqlimport add the following to your database conf file:
# loose-local-infile = 1
# 
# Another issue with mysql 8 or greater
# No longer has INFORMATION_SCHEMA.  If a database was exported from an older 
# version of mysql there might be references to INFORMATION_SCHEMA and script will
# crash with error.  Update any file containing it from INFORMATION_SCHEMA to 
# PERFORMANCE_SCHEMA
# Easy fix for this issue.  Open mysql and run the following command: 
# set @@global.show_compatibility_56=ON;


RESOURCE="SCRIPT"
#LOG="/home/gmbuild/ensembl_data/current_build.log"

#touch $LOG

#create a directory with today's date so we can track which version of ensembl we are using. 
# get the newest directory - assumption is the newest directory contains the newly downloaded
# ensembl files.
cd /home/gmbuild/ensembl_data
dir_name=$(ls -td */ | head -1)
cd ${dir_name}
echo "current directory - ${dir_name}"

LOG="/home/gmbuild/ensembl_data/${dir_name}/current_build.log"

touch $LOG

for d in */ ; do
     cd $d
     schema_sql=$(ls -l *.sql.gz | awk '{print $NF}')
     echo "$RESOURCE schema file: $schema_file"

     db_name=$(echo $schema_sql | awk -F. '{print $1}')
     echo "$RESOURCE will create database $db_name"

     mysql -u root -pgm.build -e "create database $db_name"
     if [[ $? -eq 0 ]]; then 
         echo "$RESOURCE $db_name created."
     else
         echo "$RESOURCE failed to create $db_name" >> $LOG
         #exit 1
     fi

     echo "$RESOURCE extracting $schema_sql"
     gunzip -f $schema_sql
     echo "$RESOURCE importing ${db_name}.sql"
     mysql -u root -pgm.build $db_name < ${db_name}.sql
     gzip ${db_name}.sql

     if [[ $? -eq 0 ]]; then 
         echo "$RESOURCE $db_name schema successfully created."
     else
         echo "$RESOURCE failed to create schema for $db_name" >> $LOG
         #exit 1
     fi

     # Unzip the txt files in the directory
     for j in *.txt.gz; do
         echo "$RESOURCE extracting text file $j"
         gunzip -f $j;
     done

     # Import all the txt files
     echo "$RESOURCE importing all text files."
     mysqlimport -v -u root -pgm.build $db_name -L *.txt 2> $LOG
     if [[ $? -eq 0 ]]; then
         echo "$RESOURCE Successfully imported data to $db_name"
     else
         echo "$RESOURCE Error! Failed to import data to $db_name" >> $LOG
         #exit 1
     fi
     cd ..
done

cd ..
#move the create ensembl data to the ensembl diretory
#mv ${dir_name} /home/gmbuild/ensembl_data/
