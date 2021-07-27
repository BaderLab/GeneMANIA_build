#!/bin/bash

#there is no requirement to run this script on the docker. 
# This script simply downloads all the ensembl mysql dumps
# 
# When you launch your docker session you need to specify the location
# of the tmp_ensembl directory as one of the volumes as follows
# 
# -v /home/gmbuild/ensembl_data:/home/genemania/ensembl_data 

#configured for the docker image.  change into the docker ensembl dir
cd /home/gmbuild/ensembl_data

#create a directory with today's date so we can track which version of ensembl we are using. 
dir_name=`date '+%B_%d_%Y'`
mkdir ${dir_name}
cd ${dir_name}

#this variable contains the list of species you want to download
# to add a new species simply add the name of the new species
# to the end of this line.  For example- "\|bos_taurus_core"
#
# **verify the species is available at ftp.ensembl.org/pub/current_mysql**
SPECIES='homo_sapiens_core\|caenorhabditis_elegans_core\|danio_rerio_core\|drosophila_melanogaster_core\|mus_musculus_core\|rattus_norvegicus_core\|saccharomyces_cerevisiae_core'

#get the latest versions of the mysql dumps from the current_mysql directory
# on the ensembl ftp site - store results in an array
ENSEMBL_DBS=( $(curl -l -s  ftp://ftp.ensembl.org/pub/current_mysql/ --user anonymous:anonymous | grep ${SPECIES}) )

for i in "${ENSEMBL_DBS[@]}" ; 
do 
# Trying to replace the ftpmirror with rsync to see if increases the time
#    ../ftpmirror.py ftp.ensembl.org /pub/current_mysql/${i} ${i}
	printf "\n==> Rsync ${i}:\n"

	RC=1 
	while [[ $RC -ne 0 ]] # if rsync is not successful (code 0), try again
	do
        	rsync -av rsync://ftp.ensembl.org/ensembl/pub/current_mysql/${i} .
		RC=$? # saves the return code
		
		# print DONE or ERROR
		if [ $RC -eq 0 ]
        	then
                	printf "\n[ DONE ] : ${i}\n"
        	else
                	printf "\n[[ ERROR ]] : ${i} -- Trying again...\n"
        		rm -rf ${i} # TODO: is this necessary???
		fi
	
		# added sleep because rsync is failing randomly after some of the species
                sleep 90
	done

	#not sure the purpose of this line to create an empty file.  Maybe it is important later in the pipeline ????
    #touch d.${i}

done

#inorder to use rsync needed to add /all/ infront of directory list.
# found this info here: https://github.com/boutroslab/cld/blob/master/MANUAL.md
#Arabidopsis is in a separate ftp site - unfortunately there is no current_mysql directory
# if you want to get the latest version you will need to manually change the version below
CURRENT_ARABIDOPSIS=$(curl -l -s  ftp://ftp.ensemblgenomes.org/pub/current/plants/mysql/ --user anonymous:anonymous | grep arabidopsis_thaliana_core) 
#CURRENT_ARABIDOPSIS="arabidopsis_thaliana_core_42_95_11"
#../ftpmirror.py ftp.ensemblgenomes.org /pub/current/plants/mysql/${CURRENT_ARABIDOPSIS} ${CURRENT_ARABIDOPSIS}
rsync -av rsync://ftp.ensemblgenomes.org/pub/current/plants/mysql/${CURRENT_ARABIDOPSIS} .


#E-coli is also in a separate ftp site - unfortunately there is no current_mysql directory
# if you want to get the latest version you will need to manually change the version below
# if the below doesn't work then you need to manually download directly from the ftp site
CURRENT_ECOLI=$(curl -l -s  ftp://ftp.ensemblgenomes.org/pub/current/bacteria/mysql/ --user anonymous:anonymous | grep bacteria_90_collection_core) 
#CURRENT_ECOLI="bacteria_90_collection_core_42_95_1"
#../ftpmirror.py ftp.ensemblgenomes.org /pub/current/bacteria/mysql/${CURRENT_ECOLI} ${CURRENT_ECOLI}
rsync -av rsync://ftp.ensemblgenomes.org/all/pub/current/bacteria/mysql/${CURRENT_ECOLI} .

