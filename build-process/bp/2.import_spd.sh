#!/bin/bash


# monitor each process running in the background so we know when it finishes
function watch_processes {
	for job in `jobs -p`; do 
		wait $job || let "fail+=1"
	done
}
echo "Importing Shared Protein Domains."

# if db.cfg is provided as the first argument, assume the user
# wants to refresh bp.cfg
if [[ ! -z $1 ]]; then 
	python create_config.py $1
fi

./check.sh
if [[ $? -eq 1 ]]; then
	exit 1
fi

source bp.cfg
start=`date`

spd=${RESOURCE_DIR}/spd
spdbuild=${BUILD_DIR}/spd

mkdir -p $spdbuild
pushd $spdbuild

echo "[The Ensembl shared protein domains were exported from the ensembl instance for the following org: ${SPD_ORG}]"

cp -r ${DBMIRROR}/spd/* $spdbuild

fail=0
watch_processes

if [[ $fail -ne 0 ]]; then 
	echo "[An error occurred while importing shared protein domains]"
	exit 1
fi
echo "[Done importing from Ensembl]"

#echo "[Waiting to copy to ${SRCDB}...]"
#sleep 30

mkdir -p ${SRCDB}/data

#echo "### COPY NEW SPD FILES TO ${SRCDB} ###"
#echo "### PRESS ENTER WHEN DONE          ###"
#read

# delete old spd files
rm -rf ${SRCDB}/interpro
rm -rf ${SRCDB}/pfam
rm -rf ${SRCDB}/data/interpro
rm -rf ${SRCDB}/data/pfam

# copy new spd files
#cp -r interpro ${SRCDB}
#cp -r pfam ${SRCDB}

# copy new spd files
mkdir -p ${SRCDB}/interpro
mkdir -p ${SRCDB}/pfam

echo "[Current dir: `pwd`]"
pushd interpro
echo "[Copying interpro files to ${SRCDB}/interpro]"
cp -r * ${SRCDB}/interpro
popd
pushd pfam
echo "[Copying pfam files to ${SRCDB}/pfam]"
cp -r * ${SRCDB}/pfam
popd


# create configuration files for spds
pushd ${CODE_DIR}/loader
for i in $SPD_ORG; do
    echo "[Importing ${i}]"

    # get the short organism code. Eg: homo_sapiens => Hs
    first_letter=`echo $i | cut -c1 | tr "[:lower:]" "[:upper:]"`
    second_letter=`printf $i | cut -d '_' -f2 | cut -c1`
    org="${first_letter}${second_letter}"
    echo "[Creating metadata for $org]"

    echo "./r.sh import_file ${SRCDB}/db.cfg -r ${SRCDB}/interpro/${i}/raw/all.txt -o $org -g spd -s INTERPRO -c interpro"
    ./r.sh import_file ${SRCDB}/db.cfg -r ${SRCDB}/interpro/${i}/raw/all.txt -o $org -g spd -s INTERPRO -c interpro
    echo "./r.sh import_file ${SRCDB}/db.cfg -r ${SRCDB}/pfam/${i}/raw/pfam.txt -o $org -g spd -s PFAM -c pfam"
    ./r.sh import_file ${SRCDB}/db.cfg -r ${SRCDB}/pfam/${i}/raw/pfam.txt -o $org -g spd -s PFAM -c pfam
done
popd

# pull interpro id, name, description from database

# get the database names, store into arrays
databases=$(cat ${ORG_DIR}/*.properties | grep "^db=" | cut -d"=" -f2)
shortcodes=$(cat ${ORG_DIR}/*.properties | grep "^organism=" | cut -d"=" -f2)
declare -a dbarray=($databases)
declare -a scarray=($shortcodes)

total=$((${#dbarray[@]} - 1)) # -1 because for loop {n..m} uses <= instead of <
for i in $(eval echo "{0..${total}}"); do
	current_org=`echo ${dbarray[$i]} | awk -F'_core_' '{print $1}'`
	echo ${current_org}

	mkdir -p ${SRCDB}/data/interpro/${scarray[$i]}/ids/
	
	ls ${SRCDB}/interpro/${current_org}/ids/* 

	#cp the ids from precomputed directory
	cp ${SRCDB}/interpro/${current_org}/ids/* ${SRCDB}/data/interpro/${scarray[$i]}/ids/
#	chmod 755 ${SRCDB}/data/interpro/${scarray[$i]}/ids/
#	rm -f ${SRCDB}/data/interpro/${scarray[$i]}/ids/ipr.txt
#    echo "[DB: ${dbarray[$i]}]"
#	mysql -h172.17.0.3 -uroot -pgm.build -D ${dbarray[$i]} -e "select dbprimary_acc, display_label, description from xref where dbprimary_acc like 'IPR%';" > ${SRCDB}/data/interpro/${scarray[$i]}/ids/ipr.txt

done

echo "[Importing shared protein domains completed]"
stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
