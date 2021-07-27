#!/bin/bash


function mesh_not_found {
	echo ""
	echo "One or more required mesh files were not found."
	echo "Download the mesh files into a directory called"
	echo "${RESOURCE_DIR}/mesh"
	echo ""
}

function download_data {
	echo "[Downloading mesh trees]"
	curl ftp://nlmpubs.nlm.nih.gov/online/mesh/.meshtrees/${MESHDB} -o ${mesh}/${MESHDB}
}

echo "Building networks metadata."

# if db.cfg is provided as the first argument, assume the user
# wants to refresh db.cfg
if [[ ! -z $1 ]]; then 
	python create_config.py $1
fi 

./check.sh
if [[ $? -eq 1 ]]; then
    exit 1
fi

source bp.cfg
start=`date`

mesh=${RESOURCE_DIR}/mesh

mkdir -p ${mesh}
download_data
echo "Download complete."

# check to make sure the mesh resource files are available
if [[ ! -e ${mesh}/${MESHDB} || ! -e ${mesh}/selected_terms.csv ]]; then 
	mesh_not_found
	exit 1
fi

mkdir -p ${SRCDB}/mesh_data
cp ${mesh}/${MESHDB} ${SRCDB}/mesh_data
cp ${mesh}/selected_terms.csv ${SRCDB}/mesh_data

pushd ${CODE_DIR}/loader

echo  "[Fetch mesh]"
./r.sh get_mesh ${SRCDB}/db.cfg

echo "[Propagate mesh identifiers]"
./r.sh prop_mesh ${SRCDB}/db.cfg

echo "[Add GeneMANIA tags]"
./r.sh gmtags ${SRCDB}/db.cfg

echo "[Generate network names: name_series]"
./r.sh name_series ${SRCDB}/db.cfg

echo "[Generate network names: name_dedup]"
./r.sh name_dedup ${SRCDB}/db.cfg

popd

stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
