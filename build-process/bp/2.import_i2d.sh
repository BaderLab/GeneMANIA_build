#!/bin/bash


function i2d_notfound {
	echo ""
	echo "One or more I2D tab files were not found."
	echo "Download the I2D tab files and save them"
	echo "in a directory called ${RESOURCE_DIR}/i2d"
	echo ""
}

function get_version {
	# can only get the version after we unpack the zip files
	# as they're part of the file file name
	mkdir -p ${SRCDB}/version
	pushd $i2d
	for i in *.tab; do 
		# just get one and break out of the loop
		echo "$i" | awk -F'.' '{print $2}' | sed 's/_/./g' > ${SRCDB}/version/i2d.txt 
		break
	done
	
}

function download_data {
	echo "[Downloading current I2D data]"
	URL="http://ophid.utoronto.ca/ophidv2.204/DownloadServlet?type=database&format=tab&organism="
	for file in $I2D_ORG; do
		if [[ $file == "PLANT" ]]; then
			continue
		fi
		echo "[Downloading $file data]"
		# convert organism name to uppercase for download
		orgname=`echo $file | tr a-z A-Z`
		tmp=${orgname}"&version=2_9&ophid_group_id=1"

		# I2D always seems to return http code 200 regardless of whether the data is there or not,
		# so let's check the size of bytes downloaded instead
		recv=`curl -w "%{size_download}" "${URL}${tmp}" -o ${i2d}/i2d.${orgname}.tab.zip | tail -1`
		if [[ $recv -eq 0 ]]; then 
			echo "[Download failed]"
			return 1
		fi
	done
}


echo "Importing I2D."

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

i2d=${RESOURCE_DIR}/i2d
i2dbuild=${BUILD_DIR}/i2d

echo "[Removing old $i2dbuild]"
rm -rf $i2dbuild
#echo "[Removing old $i2d]"
#rm -rf $i2d

mkdir $i2dbuild
mkdir $i2d


download_data
if [[ $? -eq 1  ]]; then 
	echo "[Download site not working, checking for previously downloaded data]"
	for i in $I2D_ORG; do 
		if [[ $i == "PLANT" ]]; then 
			# I2D doesn't provide plant data
			continue
		fi
		echo "[Checking for ${i2d}/i2d.${i}.tab.zip]"
		if [[ ! -f ${i2d}/i2d.${i}.tab.zip ]]; then 
			echo "[Previously downloaded data incomplete]"
			exit 1
		fi
	done
	echo "[Using previously downloaded data]"
fi


echo "[Unpacking I2D zip files]"
for i in ${i2d}/*.zip; do 
	unzip -o $i -d ${i2d}
	if [[ $? -ne 0 ]]; then
		echo "[Error unzipping ID files]"
		exit 1
	fi
done

#get_version

cp ${CODE_DIR}/parsers/i2d/resources/*.csv $i2d
cp -r $i2d/* $i2dbuild

echo "[Separating source ID from the data files]"
mkdir -p ${i2dbuild}/sources 
echo "curr dir: `pwd`"
for i in ${i2dbuild}/*.tab; do 
	#maybe they changed the names of the file since the last build but the 5th word is tab
	#changed back to using the 4th word which is the organism ex: 12d.2_9.Public.FLY.tab
	organism=`echo $i | awk -F. '{print $4}'`
	#organism=`echo $i | awk -F. '{print $5}'`
	echo "[Organism: $organism]"
	${CODE_DIR}/parsers/i2d/geti2dsrc.sh $i > ${i2dbuild}/sources/${organism}.src
done

echo "[Parsing the source ID files]"
pushd ${i2dbuild}
for i in $I2D_ORG; do       
	if [[ -f ./sources/${i}.src ]]; then 
		echo "${CODE_DIR}/parsers/i2d/geti2dint.sh $i ./sources/${i}.src ./i2d.*${i}.tab"
		${CODE_DIR}/parsers/i2d/geti2dint.sh $i ./sources/${i}.src ./i2d.*${i}.tab ${CODE_DIR}/parsers/i2d/resources/i2d_all.csv ${CODE_DIR}/parsers/i2d
	fi
done
#${CODE_DIR}/parsers/i2d/geti2dint.sh 

echo "[Fix fly mappings]"

# make a list of all the fly files to re-map
if [[ -d fly ]]; then 
	pushd fly
	for i in *; do 
		if [[ ! -d $i ]]; then 
			list="$i $list "
		fi 
	done

	# special patch for FLY
	echo "${CODE_DIR}/parsers/i2d/fixi2dfly.py ${CODE_DIR}/parsers/i2d/idmapping.tab $list"
	${CODE_DIR}/parsers/i2d/fixi2dfly.py ${CODE_DIR}/parsers/i2d/idmapping.tab $list
	mv ${i2dbuild}/FLY ${i2dbuild}/FLY.old
	mv ${i2dbuild}/FLY.old/fly.mapped ${i2dbuild}/FLY
	rm -rf ${i2dbuild}/FLY.old
	popd
fi


echo "[Importing I2D]"
mkdir -p ${SRCDB}/i2d_import
#cp -rf ${i2dbuild}/fly/fly.mapped ${SRCDB}/i2d_import/fly
#cp -rf ${i2dbuild}/human ${SRCDB}/i2d_import/
#cp -rf ${i2dbuild}/mouse ${SRCDB}/i2d_import/
#cp -rf ${i2dbuild}/worm ${SRCDB}/i2d_import/
#cp -rf ${i2dbuild}/yeast ${SRCDB}/i2d_import/
#cp -rf ${i2dbuild}/rat ${SRCDB}/i2d_import/
#cp -f ${i2dbuild}/*.csv ${SRCDB}/i2d_import/

pushd $i2dbuild
for i in *; do 
	if [[ -d $i ]]; then
		echo "[Copying $i to ${SRCDB}/i2d_import"
		echo "[Converting $i to lowercase]"
		lwr=`echo $i | tr '[:upper:]' '[:lower:]'`
		echo "cp -rf $i ${SRCDB}/i2d_import/$lwr"
		cp -rf $i ${SRCDB}/i2d_import/$lwr
	fi
done

cp -f *.csv ${SRCDB}/i2d_import
popd

pushd ${CODE_DIR}/loader
./r.sh import_i2d ${SRCDB}/db.cfg ${SRCDB}/i2d_import
popd

stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
