#!/bin/bash

function get_version {
	echo "[Getting iRefIndex version]"
	#curl -s https://irefindex.vib.be/download/irefindex/data/release > ${SRCDB}/version/irefindex.txt

	echo "[Getting release date]"
	curl -sl https://irefindex.vib.be/download/irefindex/data/archive/release_17.0/psi_mitab/MITAB2.6/ | grep '.zip' | awk -F "href=\"" '{print $2}' | awk -F. '{print $3}' | head -1 >> ${SRCDB}/version/irefindex.txt

    echo "[Version and release]"
    cat ${SRCDB}/version/irefindex.txt
}


function static_version {
      if [[ ! -d "$SRCDB/version" ]]; then
	      mkdir $SRCDB/version
      fi

	echo "27062021" > ${SRCDB}/version/irefindex.txt
}

function download_static_data {
	echo "[Downloaded static data from baderlab ftp site - consider checking for updated data]"

	URL="http://download.baderlab.org/GeneMANIA/data_build/"

	echo "URL [$URL]"
        
	FILE="iref_v17_July2021.tar.gz"
	
	echo "wget --verbose ${URL}/${FILE} -O ${iref}/${FILE}"
	wget --verbose ${URL}/${FILE} -O ${iref}/${FILE}
}

function download_data {
	echo "[Downloading current iRefIndex data]"
	URL="https://irefindex.vib.be/download/irefindex/data/archive/release_17.0/psi_mitab/MITAB2.6"
	echo "URL: [$URL]"

	# get the release date
	release=`tail -1 ${SRCDB}/version/irefindex.txt | tr -d '\n'`
	for file in ${IREF_ORG}; do 
		#echo "curl -w \"%{http_code}\" ${URL}/${file}.mitab.${release}.txt.zip -o ${iref}/${file}.mitab.${release}.txt.zip | tail -1"
		#recv=`curl -w "%{http_code}" ${URL}/${file}.mitab.${release}.txt.zip -o ${iref}/${file}.mitab.${release}.txt.zip | tail -1`

		echo "wget --verbose ${URL}/${file}.mitab.${release}.txt.zip -O ${iref}/${file}.mitab.${release}.txt.zip"
		wget --verbose ${URL}/${file}.mitab.${release}.txt.zip -O ${iref}/${file}.mitab.${release}.txt.zip 

		# check http response code
		#if [[ $recv -ne 200 ]]; then
		#	echo "[Download failed]"
		#	return 1
		#fi
	done
}

function watch_processes {
	for job in `jobs -p`; do 
		wait $job || let "fail+=1"
	done
}

echo "Importing iRefIndex"

# if db.cfg is provied as the first argument, assume the user
# wants to refresh bp.cfg
if [[ ! -z $1 ]]; then 
	python create_config.py $1
fi

./check.sh
if [[ $? -eq 1 ]]; then
	exit 1
fi

source bp.cfg

iref=${RESOURCE_DIR}/iref
mkdir -p ${iref}

#Although we are able to download the updated data from the iref download site we are 
# unable to unzip the files on linux.  Unzipping on Mac works
# in the meantime added the latest files to the genemania databuild data files on baderlab
# ftp site - periodically check for updates
#get_version
#download_data

static_version

download_static_data

if [[ $? -eq 1 ]]; then 
	echo "[Download site not working, checking for previously downloaded data]"
	release=`cat ${SRCDB}/version/irefindex.txt | tail -1`
	for i in $IREF_ORG; do 
		echo "[Checking for ${iref}/${i}.zip]"
		if [[ ! -f ${iref}/${i}.mitab.${release}.txt.zip ]]; then 
			echo "[Previously downloaded data incomplete]"
			exit 1
		fi
	done
	echo "[Using previously downloaded data]"
fi

start=`date`

irefbuild=${BUILD_DIR}/iref
echo "[Removing old iRefIndex build]"
rm -rf ${irefbuild}
mkdir -p ${irefbuild}

echo "changing to iref build directory ${irefbuild}"
pushd ${irefbuild}
#uncomment if we revert to getting iref directly from source again.
#cp ${iref}/*.zip . 
#for i in *.zip; do 
#	echo "Unpacking ${i}..."
#	unzip $i
#	rm -f $i
#done

echo "Copying ${iref}/*.gz over to current directory"
cp ${iref}/*.gz .
tar -xzvf *.tar.gz

echo "[Extracting A.Thaliana from All]"
v=`tail -1 ${SRCDB}/version/irefindex.txt`
grep -w 3702 All*.txt > 3702.mitab.${v}.txt

echo "[Extracting D.Rerio from All]"
v=`tail -1 ${SRCDB}/version/irefindex.txt`
grep -w 7955 All*.txt > 7955.mitab.${v}.txt

echo "[Extracting E.Coli from All]"
v=`tail -1 ${SRCDB}/version/irefindex.txt`
grep -w 83333 All*.txt > 83333.mitab.${v}.txt

#echo "[Extracting Human from All - because human file downloaded is corrupt]"
#v=`tail -1 ${SRCDB}/version/irefindex.txt`
#grep -w 9606 All*.txt > 9606.mitab.${v}.txt

echo "[Merging S. cerevisiae files]"
v=`tail -1 ${SRCDB}/version/irefindex.txt`
tail -n +2 559292.mitab.${v}.txt > yeast2.txt
cat yeast2.txt >> 4932.mitab.${v}.txt


echo "[Deleting old iRefIndex data]"
rm -rf ${SRCDB}/iref
rm -rf ${SRCDB}/data/iref_direct

echo "[Copying new iRefIndex data]"
mkdir -p ${SRCDB}/iref

export PYTHONPATH=".:${CODE_DIR}/loader/src/main/python/dbutil/"
echo "[PYTHONPATH: $PYTHONPATH]"

for i in *.txt; do 
	echo "Parsing ${i}..."
	taxid=$(echo ${i} | cut -d. -f1)
	organism=""
	echo "Using Tax ID: $taxid"

	# we only have tax id's so find the corresponding organism short id
	for file in ${ORG_DIR}/*.properties; do 
		grep "taxid=${taxid}" ${file}
		if [[ $? -eq 0 ]]; then 
			organism=`grep organism $file | cut -d"=" -f2`
			echo "[Tax ID $taxid is $organism]"
		fi 
	done
	if [[ ! -z ${organism} ]]; then 
		if [[ ${organism} == "Ec" ]]; then 
			echo "${CODE_DIR}/parsers/irefindex/parse_iref.py ${i} ${SRCDB}/iref/${organism} ${SRCDB} ${organism}.db 3,4"
			${CODE_DIR}/parsers/irefindex/parse_iref.py ${i} ${SRCDB}/iref/${organism} ${SRCDB} ${organism}.db 3,4
		else
			echo "${CODE_DIR}/parsers/irefindex/parse_iref.py ${i} ${SRCDB}/iref/${organism} ${SRCDB} ${organism}.db"
			${CODE_DIR}/parsers/irefindex/parse_iref.py ${i} ${SRCDB}/iref/${organism} ${SRCDB} ${organism}.db
		fi 
	fi 
done

pushd ${CODE_DIR}/loader
echo "[Importing iRefIndex]"
./r.sh import_iref ${SRCDB}/db.cfg ${SRCDB}/iref
wait
popd

stop=`date`

echo "Start: $start"
echo "Stop : $stop"
exit 0
