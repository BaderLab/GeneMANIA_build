#!/bin/bash

function get_version {
	# pathway commons uses a release date instead of a version
	mkdir -p ${SRCDB}/version
	curl -s http://www.pathwaycommons.org/pc-snapshot/ | grep "current-release" | awk '{print $6}' > ${SRCDB}/version/pathwaycommons.txt
}

function pc_notfound {
	echo ""
	echo "One or more Pathway Commons files were not found."
	echo "Download the Pathway Commons edges and nodes files" 
	echo "into a directory called ${RESOURCE_DIR}/pathwaycommons/edges"
	echo "and ${RESOURCE_DIR}/pathwaycommons/nodes"
	echo ""
}

function download_data {
	echo "[Downloading current Pathway Commons data]"
	#URL="http://www.pathwaycommons.org/pc-snapshot/current-release/tab_delim_network/by_species/"
	#URL="http://www.pathwaycommons.org/pc-snapshot/september-2010-release/tab_delim_network/by_species/"
    URL="http://www.pathwaycommons.org/archives/PC1/last_release-2011/tab_delim_network/by_species/"

	for file in $PC_ORG; do 
		recv1=`curl -w %{http_code} ${URL}/${file}-edge-attributes.txt.zip -o ${pc}/edges/${file}-edge-attributes.txt.zip | tail -1`
		recv2=`curl -w %{http_code} ${URL}/${file}-node-attributes.txt.zip -o ${pc}/nodes/${file}-node-attributes.txt.zip | tail -1`
		echo "recv1: curl -w %{http_code} ${URL}/${file}-edge-attributes.txt.zip -o ${pc}/edges/${file}-edge-attributes.txt.zip | tail -1"
		echo "recv2: curl -w %{http_code} ${URL}/${file}-node-attributes.txt.zip -o ${pc}/nodes/${file}-node-attributes.txt.zip | tail -1"

		if [[ $recv1 -ne 200 && $recv2 -ne 200 ]]; then 
			echo "[Download failed]"
			return 1
		fi
	done
}

function watch_processes {
	for job in `jobs -p`; do 
		wait $job || let "fail+=1"
	done
}

echo "Importing PathwayCommons."

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

#echo "[Removing old Pathway Commons resource]"
#rm -rf ${RESOURCE_DIR}/pathwaycommons/
mkdir -p ${RESOURCE_DIR}/pathwaycommons/edges
mkdir -p ${RESOURCE_DIR}/pathwaycommons/nodes
pc=${RESOURCE_DIR}/pathwaycommons

download_data
if [[ $? -eq 1 ]]; then 
	echo "[Download site not working, checking for previously downloaded data]"
	for i in $PC_ORG; do 
		echo "[Checking for ${pc}/nodes/${i}-node-attributes.txt.zip]"
		echo "[Checking for ${pc}/edges/${i}-edge-attributes.txt.zip]"

		if [[ ! -f ${pc}/nodes/${i}-node-attributes.txt.zip \
			|| ! -f ${pc}/edges/${i}-edge-attributes.txt.zip ]]; then 
			echo "[Previously downloaded data incomplete]"
			exit 1
		fi
	done
	echo "[Using previously downloaded data]"
fi
get_version

start=`date`

pcbuild=${BUILD_DIR}/pathwaycommons
echo "[Removing old Pathway Commons build]"
rm -rf ${pcbuild}
mkdir -p ${pcbuild}/pubmed
mkdir -p ${pcbuild}/source
mkdir -p ${pcbuild}/pubmed_out
mkdir -p ${pcbuild}/source_out

edge="-edge-attributes.txt"
node="-node-attributes.txt"

for species in $PC_ORG; do 
	echo "[Unpacking ${species}]"
	unzip -o ${pc}/edges/${species}${edge}.zip -d ${pc}/edges
	unzip -o ${pc}/nodes/${species}${node}.zip -d ${pc}/nodes
done
nodes_dir=${pc}/nodes

export PYTHONPATH=".:${CODE_DIR}/loader/src/main/python/dbutil/"
echo "[PYTHONPATH: $PYTHONPATH]"

for species in $PC_ORG; do 

### 
# PMID interactions fall into physical interaction networks. Temporarily comment this out so 
# pathwaycommons only fall into the path group
###
#	echo "[Parsing ${species} by PMID]"
#	${CODE_DIR}/parsers/pathwaycommons/do_pmid.py ${pc}/edges/${species}${edge} ${nodes_dir}/${species}${node} ${pcbuild}/pubmed_out ${SRCDB} ${pcbuild} & 

	echo "[Parsing ${species} by source]"
	${CODE_DIR}/parsers/pathwaycommons/do_source.py ${pc}/edges/${species}${edge} ${nodes_dir}/${species}${node} ${pcbuild}/source_out ${SRCDB} ${pcbuild} &

done

fail=0
watch_processes

if [[ $fail -ne 0 ]]; then 
	echo "[An error occurred while parsing pathway commons]"
	exit 1
fi

echo "[Deleting old Pathway Commons data]"
rm -rf ${SRCDB}/pathwaycommons_import
rm -rf ${SRCDB}/data/pathwaycommons_direct

echo "[Copying new Pathway Commons data]"
mkdir -p ${SRCDB}/pathwaycommons_import
cp -r ${pcbuild}/pubmed_out ${SRCDB}/pathwaycommons_import
cp -r ${pcbuild}/source_out ${SRCDB}/pathwaycommons_import

pushd ${CODE_DIR}/loader
echo "[Importing Pathway Commons]"
./r.sh import_pathwaycommons ${SRCDB}/db.cfg ${SRCDB}/pathwaycommons_import
wait
popd

stop=`date`

echo "Start: $start"
echo "Stop : $stop"
exit 0
