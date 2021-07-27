#!/bin/bash 

function get_version {
	version=`echo "${biogrid}/BIOGRID-ORGANISM-${BIOGRID_VERSION}.tab.zip" | awk -F'-' '{print $3}' | awk -F ".tab." '{print $1}'`
	mkdir -p ${SRCDB}/version
	echo "$version" > ${SRCDB}/version/biogrid.txt
	echo "[BioGRID version: $version]"
}

function biogrid_not_found {
	echo ""
	echo "One or more BioGRID files were not found."
	echo "Download the BioGRID files"
	echo "into a directory called ${RESOURCE_DIR}/biogrid."
	echo ""
}

function download_data {
	echo "[Downloading BioGRID]"

	#In the download directory of biogrid there is a current-release tag where filenames indicate the version.
        # If we want to be able to run the process with limited updating by the user we want to get rid of this.
	# There is also a directory called latest where the each file has the word latest instead of the version number

	URL="https://downloads.thebiogrid.org/Download/BioGRID/Latest-Release/BIOGRID-ORGANISM-LATEST.tab.zip"
	#URL="https://thebiogrid.org/downloads/archives/Release%20Archive/BIOGRID-${BIOGRID_VERSION}/BIOGRID-ORGANISM-${BIOGRID_VERSION}.tab.zip"
    #URL="https://thebiogrid.org/downloads/archives/Release%20Archive/BIOGRID-3.4.145/BIOGRID-ORGANISM-3.4.145.tab.zip"
    echo "URL: ${URL}"

	# we should get http code 200 if the download is successful
	recv=`curl -w %{http_code} "${URL}" -o ${biogrid}/BIOGRID-ORGANISM-${BIOGRID_VERSION}.tab.zip | tail -1`
	if [[ $recv -ne 200 ]]; then 
		echo "[Download failed]"
		return 1
	fi

#if [[ $? -eq 1 ]]; then 
#	echo "[Download site not working, checking for previously downloaded data]"
#	if [[ -f "${biogrid}/BIOGRID-ORGANISM-${BIOGRID_VERSION}.tab.zip" ]]; then 
#		echo "[Using previously downloaded data]"
#	else
#		echo "[No data for BioGRID]"
#		exit 1
#	fi
#fi
}

echo "Importing BioGRID."

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

biogrid=${RESOURCE_DIR}/biogrid
mkdir -p $biogrid

download_data
if [[ $? -eq 1 ]]; then 
	echo "[Download site not working, checking for previously downloaded data]"
	if [[ -f "${biogrid}/BIOGRID-ORGANISM-${BIOGRID_VERSION}.tab.zip" ]]; then 
		echo "[Using previously downloaded data]"
	else
		echo "[No data for BioGRID]"
		exit 1
	fi
fi

get_version

start=`date`

biogrid_build=${BUILD_DIR}/biogrid
mkdir -p ${biogrid_build}

pushd ${biogrid_build}
# create biogrid directory structure for parsing
echo "[Creating directory structure]"
${CODE_DIR}/parsers/biogrid/parsebiogrid.py makedir ${SRCDB}/db.cfg

cp -f ${biogrid}/BIOGRID-ORGANISM-${BIOGRID_VERSION}.tab.zip .
unzip -o BIOGRID-ORGANISM-${BIOGRID_VERSION}.tab.zip

# copy the raw files into their respective directories.
# Arabidopsis thaliana => At
# The files only have the long names of the organisms, so we need to 
# construct the shortname so we can copy it to the correct directory.
#for i in $BIOGRID_ORG; do
#    echo "[Importing ${i}]"
#
#	# get the short organism code. Eg: homo_sapiens => Hs
#    first_letter=`echo $i | cut -c1 | tr "[:lower:]" "[:upper:]"`
#    second_letter=`printf $i | cut -d '_' -f2 | cut -c1`
#    short_name="${first_letter}${second_letter}"
#    echo "[Organism code $short_name]"
#	cp -f ${biogrid_build}/*${i}* ${short_name}/raw
#done
#rm -f *.txt
#rm -f *.zip

# process biogrid files
mkdir -p ${SRCDB}/data/
${CODE_DIR}/parsers/biogrid/parsebiogrid.py process ${SRCDB}/db.cfg

# copy to srcdb import directory
echo "[Copying processed directories to $SRCDB/biogrid]"
rm -rf ${SRCDB}/biogrid
mkdir -p ${SRCDB}/biogrid

for i in *; do
	if [[ -d $i ]]; then
		echo "[Copying $i to ${SRCDB}/biogrid]"
		cp -rf $i ${SRCDB}/biogrid
	fi
done

popd


pushd ${CODE_DIR}/loader
echo "[Importing BioGRID]"
./r.sh import_biogrid ${SRCDB}/db.cfg ${SRCDB}/biogrid
wait
popd

stop=`date`

echo "Start: $start"
echo "Stop : $stop"
exit 0
