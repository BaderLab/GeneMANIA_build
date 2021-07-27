#!/bin/bash

function download_data {
	echo "[Downloading current legacy attribute data]"
	URL="http://download.baderlab.org/GeneMANIA/data_build/"
	file=import.tar.gz
	echo "URL: [$URL]"
	
	echo "wget --verbose ${URL}/${gmt_src}/${file} -O ${attr_dir}/${file}"
	wget --verbose ${URL}/${gmt_src}/${file} -O ${attr_dir}/${file} 

}

function watch_processes {
	for job in `jobs -p`; do 
		wait $job || let "fail+=1"
	done
}

echo "Importing GMT Attribute files"

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

attr_dir=${SRCDB}/attributes/import
mkdir -p ${attr_dir}

download_data

#change into the directory with new attribute files so we can process them
echo "changing to ${attr_dir}"
cd ${attr_dir}

tar -xvzf import.tar.gz

echo "Start: $start"
echo "Stop : $stop"
exit 0
