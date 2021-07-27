#!/bin/bash


# monitor each process running in the background so we know when it finishes
#function watch_processes {
#	for job in `jobs -p`; do 
#		wait $job || let "fail+=1"
#	done
#}
echo "Importing Shared Protein Domains."

# if db.cfg is provided as the first argument, assume the user
# wants to refresh bp.cfg
#if [[ ! -z $1 ]]; then 
#	python create_config.py $1
#fi

#./check.sh
#if [[ $? -eq 1 ]]; then
#	exit 1
#fi

#source bp.cfg
ENSEMBL_CORE_RELEASE=$1
CONFIG_FILE=$2
start=`date`

#download the required ensembl version

echo "Using ensembl version $ensembl_version"
git clone https://github.com/Ensembl/ensembl.git --branch release/${ENSEMBL_CORE_RELEASE} --single-branch $HOMEDIR/ensembl_${ENSEMBL_CORE_RELEASE}
export PERL5LIB=$HOMEDIR/ensembl_${ENSEMBL_CORE_RELEASE}/modules

spdbuild=./spd

if [ ! -d $spdbuild ]; then
	mkdir $spdbuild
fi	
pushd $spdbuild

#echo "[Getting shared protein domains for the following: ${SPD_ORG}]"
echo "[Getting shared protein domains from Ensembl: ${ENSEMBL_CORE_RELEASE}]"

../get_spd.pl ../${CONFIG_FILE} all interpro ${ENSEMBL_CORE_RELEASE} 
../get_spd.pl ../${CONFIG_FILE} pfam pfam ${ENSEMBL_CORE_RELEASE}

# pull interpro id, name, description from database 

# get the database names, store into arrays
databases=$(mysql -hlocalhost -uroot -pgm.build -e "show databases;" )
declare -a dbarray=($databases)

total=$((${#dbarray[@]} - 1)) # -1 because for loop {n..m} uses <= instead of <
for i in $(eval echo "{0..${total}}"); do
	if [[ ${dbarray[$i]} =~ ${ENSEMBL_CORE_RELEASE} ]]; then
		current_org=`echo ${dbarray[$i]} | awk -F'_core_' '{print $1}'`
		echo ${current_org}
		mkdir -p interpro/${current_org}/ids/

		chmod 755 interpro/${current_org}/ids/
		rm -f interpro/${current_org}/ids/ipr.txt
    		echo "[DB: ${dbarray[$i]}]"
		mysql -hlocalhost -uroot -pgm.build -D ${dbarray[$i]} -e "select dbprimary_acc, display_label, description from xref where dbprimary_acc like 'IPR%';" > interpro/${current_org}/ids/ipr.txt
	fi
done


stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
