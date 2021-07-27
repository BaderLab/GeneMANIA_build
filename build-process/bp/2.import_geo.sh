#!/bin/bash
function geo_notfound {
	echo ""
	echo "One or more GEO files were not found."
	echo "Download the GEOmetadb.sqlite.gz"
	echo "into a directory called ${RESOURCE_DIR}/geo"
	echo ""
}

function get_version {
	# geo uses release date instead of version
	mkdir -p ${SRCDB}/version
	#curl -s http://gbnci.abcc.ncifcrf.gov/geo/ | grep GEOmetadb.sqlite.gz | awk -F '(' '{print $2}' | awk -F "," '{print $2}'|awk '{print $1, $2, $3}' > ${SRCDB}/version/geo.txt
	curl -s https://gbnci-abcc.ncifcrf.gov/geo/ | grep GEOmetadb.sqlite.gz | awk -F '(' '{print $2}' | awk -F "," '{print $2}'|awk '{print $1, $2, $3}' > ${SRCDB}/version/geo.txt
	echo "[GEO version: `cat ${SRCDB}/version/geo.txt`]"
}

function download_data {
	echo "[Downloading latest GEOmetadb.sqlite.gz]"
	echo "[curl http://gbnci.abcc.ncifcrf.gov/geo/GEOmetadb.sqlite.gz -o ${geo}/GEOmetadb.sqlite.gz]"

	#URL="http://gbnci.abcc.ncifcrf.gov/geo/GEOmetadb.sqlite.gz"
	#URL="https://gbnci-abcc.ncifcrf.gov/geo/GEOmetadb.sqlite.gz"
	URL="http://starbuck1.s3.amazonaws.com/sradb/GEOmetadb.sqlite.gz"
	#recv=`curl -w %{http_code} "${URL}" -o ${geo}/GEOmetadb.sqlite.gz | tail -1`
	recv=`curl -w %{http_code} "${URL}" -o ${geo}/GEOmetadb.sqlite.gz | tail -1`
	if [[ $recv -ne 200 ]]; then 
		echo "[Download failed]"
		return 1
	fi 
}

echo "Importing GEO."

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


geo=${RESOURCE_DIR}/geo
mkdir -p ${geo}


download_data
if [[ $? -eq 1 ]]; then 
	echo "[Download site not working, checking for previously downloaded data]"
	if [[ -f "${geo}/GEOmetadb.sqlite.gz" || -f "${geo}/GEOmetadb.sqlite" ]]; then 
		echo "[Using previously downloaded data]"
	else
		echo "[No data for GEO]"
		exit 1
	fi
fi

get_version

start=`date`
echo "[Extracting GEOmetadb.sqlite]"
if [[ -e ${geo}/${GEODB}.gz ]]; then 
	gunzip -f -v ${geo}/${GEODB}.gz
fi

mkdir -p ${SRCDB}/geodb
cp $geo/${GEODB} ${SRCDB}/geodb

echo "[Retrieving platform files]"
pushd ${CODE_DIR}/loader
./r.sh download_platforms ${SRCDB}/db.cfg 2>&1 > download_platforms.log

mkdir -p ${SRCDB}/data/geo

echo "[Identifying microarray profile datasets]"
./r.sh identify_series ${SRCDB}/db.cfg 2>&1 > identify_series.log

echo "[Downloading series]"
./r.sh download_series ${SRCDB}/db.cfg 2>&1 > download_series.log

echo "[Applying geo metadata fixes]"
./fix_geo_cfg.sh ${SRCDB}/db.cfg ${SRCDB}

popd

stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
