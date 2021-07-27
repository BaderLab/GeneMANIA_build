#!/bin/bash


function id_notfound {
	echo ""
	echo "The database files required to build"
	echo "the data warehouse were not found."
	echo "The following directories are required:"
	echo "  ${RESOURCE_DIR}/id/schema"
	echo "  ${BUILD_DIR}/id/GMDW"
	echo "  ${BUILD_DIR}/id/scripts"
	echo "These are part of the identifer-mapper"
	echo "directory in the SVN repository."
	echo ""
}

function get_version {
	mkdir -p ${SRCDB}/version
	echo $ENSEMBL_CORE_RELEASE > ${SRCDB}/version/ensembl_core.txt
	echo $ENSEMBL_PLANTS_RELEASE > ${SRCDB}/version/ensembl_plants.txt

	# entrez doesn't have any version, and release date isn't 
	# really announced, so just get it from the folder name that 
	# we mirrored
	ls -l ${DBMIRROR}/${ENTREZ_FILES} | awk '{print $NF}' > ${SRCDB}/version/entrez_gene.txt
}

echo "Building identifier data."

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

#on the first run of this script it complains about mising 
# db.cfg file in the db directory.  Every time a db.cfg file 
# is provided make sure it is refreshed in the db directory
cp $1 ${SRCDB}/

dw=${RESOURCE_DIR}/id
dwbuild=${BUILD_DIR}/id

mkdir -p $dw
mkdir -p $dwbuild
mkdir -p ${SRCDB}/mappings/raw 
mkdir -p ${SRCDB}/mappings/processed 
#mkdir -p ${SRCDB}/mappings/reverse 

#The subsequent scripts look for the Ensembl mapping files in the ./mappings/raw directory
# but they haven't been put there.  Copy those files over from the Dbmirror
cp ${DBMIRROR}/ENSEMBL_ENTREZ_* ${SRCDB}/mappings/raw/

#for two runs of this build we have had issues with encodigs in the ENSEMBL_ENTREZ_Dr 
# make sure the file is utf-8
iconv -f utf-8 -t utf-8 -c ${DBMIRROR}/ENSEMBL_ENTREZ_Dr > ${SRCDB}/mappings/raw/ENSEMBL_ENTREZ_Dr 

echo "[Resource dir: $dw]"
echo "[Build dir: $dwbuild]"

echo "[Normalizing identifiers]"
pushd ${CODE_DIR}/loader

# generate a set of mappings from entrez
#./r.sh build_reverse_id_map ${SRCDB}/db.cfg $MYSQL_H 3306 $MYSQL_U $MYSQL_P Entrez

# apply identifier cleaning
./r.sh normalize_mappings ${SRCDB}/db.cfg
popd

echo "DONE NORMALIZING MAPPINGS"


# create sqlite db for each processed mapping file
for i in ${ORG_DIR}/*.properties; do 
	organism_short="`grep ^organism $i | cut -d"=" -f2`"
	echo "[Deleting old ${SRCDB}/${organism_short}.db]"
	rm -f ${SRCDB}/${organism_short}.db
	echo "[Creating ${SRCDB}/${organism_short}.db]"
	echo "[Command: idstosqlite.py ${SRCDB}/mappings/processed/${organism_short}_names.txt ${SRCDB}/${organism_short}.db]"
	pushd ${CODE_DIR}/loader
	./r.sh idstosqlite ${SRCDB}/mappings/processed/${organism_short}_names.txt ${SRCDB}/${organism_short}.db
	popd
done

stop=`date`
echo "Start: $start"
echo "Stop : $stop"
