#!/bin/bash

function get_version {
	echo "[Getting BaderLab GMT version]"
	curl -s http://download.baderlab.org/EM_Genesets/${version}/Human/*_versions.txt > ${SRCDB}/version/attributes_baderlab_gmt.txt

    echo "[Version and release]"
    cat ${SRCDB}/version/attributes_baderlab_gmt.txt
}


function download_data {
	echo "[Downloading current gmt data]"
	URL="http://download.baderlab.org/EM_Genesets/${version}/Human/symbol"
	echo "URL: [$URL]"

	# get the release date
	for gmt_src in ${GMT_DIR}; do 
		#list the files that are available in this directoy.
		# only get the gmt files from this directory
		GMT_FILES=`curl -s ${URL}/${gmt_src}/ | grep gmt |sed -e 's/<[^>]*>//g' | awk '{print $1}'`

		echo ${GMT_FILES}
		for gmt in ${GMT_FILES}; do
                
			echo ${gmt}
			echo "curl -w \"%{http_code}\" ${URL}/${gmt_src}/${gmt} -o ${attr_dir}/${gmt} | tail -1"
		#recv=`curl -w "%{http_code}" ${URL}/${file}.mitab.${release}.txt.zip -o ${iref}/${file}.mitab.${release}.txt.zip | tail -1`

			echo "wget --verbose ${URL}/${gmt_src}/${gmt} -O ${attr_dir}/${gmt}"
			wget --verbose ${URL}/${gmt_src}/${gmt} -O ${attr_dir}/${gmt} 
		done 
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

version="June_01_2020"
attr_dir=${SRCDB}/attributes/import/Hs
mkdir -p ${attr_dir}

get_version
download_data

#copy over the static attribute-metadata over to the working dir
cp attribute-metadata_2020.cfg ${SRCDB}/attributes/import/


#change into the directory with new attribute files so we can process them
echo "changing to ${attr_dir}"
cd ${attr_dir}

for gmt_file_to_process in `ls Human*.gmt`; do
	
	echo "[processing ${gmt_file_to_process}]"

	#Create the meta file - maps the set IDs to their names
	awk -F'\t' '{print $1}' ${gmt_file_to_process} | awk -F'%' '{print $2":"$3"\t"$1"\t"$2" "$3" "$1}' > cleaned.${gmt_file_to_process}.meta 

	#create a file with genes in each set
	awk -F'\t' '{for (i = 3; i <= NF; i++) printf $i "\t"; print ""}'  ${gmt_file_to_process} > ${gmt_file_to_process}.genes

        #create a file with the set name and description in the correct format
	awk -F'\t' '{print $1}' ${gmt_file_to_process} | awk -F'%' '{print $2":"$3"\t"$2" "$3}' > ${gmt_file_to_process}.names 	
      
	paste ${gmt_file_to_process}.names ${gmt_file_to_process}.genes > cleaned.${gmt_file_to_process}

	#remove the temporary files
	rm ${gmt_file_to_process}.names
	rm ${gmt_file_to_process}.genes
done

#merge the config files
#TODO add better way to merge the cfg files so that we can add new files in the future.  
cd ${attr_dir}
cd ..
cat attribute-metadata* > temp.cfg
mv temp.cfg attribute-metadata.cfg
#genemania snake make grabs all config files so can't leave a duplicate cfg file in directory.
mv attribute-metadata_2020.cfg attribute-metatdata_2020.cfg.tmp

echo "Start: $start"
echo "Stop : $stop"
exit 0
