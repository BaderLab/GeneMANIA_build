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
# **verify the species is available at one of the ftp species sites indicated below**
# Depending on the genus the species data might located in different locations
SPECIES='saccharomyces_cerevisiae_core'

#get the latest versions of the mysql dumps from the current_mysql directory
# on the ensembl ftp site - store results in an array
# for most eukaryotes you will find the species here-

# Change with the May 2021 release of Ensembl the ftp_site and rsync site are different
# see here - https://useast.ensembl.org/info/data/ftp/rsync.html
# need to add "ensembl" after the domain name of the address for RSYNC
FTP_SITE='ftp.ensembl.org/pub/current_mysql/'

RSYNC_SITE='ftp.ensembl.org/ensembl/pub/current_mysql/'
#FTP_SITE='ftp.ensemblgenomes.org/pub/current/plants/mysql/' 
#FTP_SITE='ftp.ensemblgenomes.org/pub/current/bacteria/mysql/'
#FTP_SITE='ftp.ensemblgenomes.org/pub/current/fungi/mysql/'
#FTP_SITE='ftp.ensemblgenomes.org/pub/current/metazoa/mysql/'

#FTP_SITE='ftp.ebi.ac.uk/ensemblgenomes/pub/current/protists/mysql/' 
#FTP_SITE='ftp.ensemblgenomes.org/pub/current/protists/mysql/'

ENSEMBL_DBS=( $(curl -l -s  ftp://${FTP_SITE} --user anonymous:anonymous | grep ${SPECIES}) )

for i in "${ENSEMBL_DBS[@]}" ; 
do 
	printf "\n==> Rsync ${i} FROM ${RSYNC_SITE}:\n"

	RC=1 
	while [[ $RC -ne 0 ]] # if rsync is not successful (code 0), try again
	do
		rsync -av rsync://${RSYNC_SITE}${i} .
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


done

