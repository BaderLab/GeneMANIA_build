#!/bin/bash

if [[ -z $1 ]]; then
    echo "Need to provide genemania data version"
    exit
fi
version=${1}

if [ ! -d $HOME/gm_data ]
then
	mkdir $HOME/gm_data
fi

if [ ! -d $HOME/db_build ]
then
	mkdir $HOME/db_build
fi

dir_name=$(ls -td /home/gmbuild/ensembl_data/* | head -1)

#create the gmbuild docker and launch it. - remember to update the version
#
# can not launch container without /bin/bash or the -it command.  The container will simply stop without those options
# (I think it has to do with the entryscript that is run)
#TODO: add version as a parameter to run this file
docker run -d -it  -v ${dir_name}/Work:/home/gmbuild/ensembl_data -v $HOME/gm_data:/home/gmbuild/dev -v $HOME/db_build:/gm/db_build -e VERSION=${version} --name genemania_build_${version} baderlab/genemania_databuild_base /bin/bash  

sleep 300

#TODO: update the version in the path with the specified version from command line when implemented
docker exec  genemania_build_${version} /bin/bash -c "cd /home/gmbuild/dev/${version}/src/build-process/bp && ./runbp.py db.cfg 1 2 3 4 5 6"



