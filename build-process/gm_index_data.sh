#!/bin/bash

if [[ -z $1 ]]; then
    echo "Need to provide genemania data version"
    exit
fi
version=${1}

if [ ! -d $HOME/gm_pipeline_snakemake_${version} ]
then
	mkdir $HOME/gm_pipeline_snakemake_${version}
fi

if [ ! -d $HOME/db_build ]
then
	echo "missing data build directory"
	exit 1
fi

if [ ! -d $HOME/gm_data ]
then
	echo "missing data build directory"
	exit 1
fi



#create the gmbuild docker and launch it. - remember to update the version
#
# can not launch container without /bin/bash or the -it command.  
# The container will simply stop without those options
# (I think it has to do with the entryscript that is run)
docker run -dit -v $HOME/gm_data:/home/gmbuild/dev \
	-v $HOME/db_build:/gm/db_build \
	-v $HOME/gm_pipeline_snakemake_${version}:/home/gmbuild/sm_build_org \
  --name gmbuild_snakemake_index_data_${version} baderlab/gmbuild_snakemake_index_data /bin/bash  

sleep 30

#copy over the slack webhook - need to generate if it hasn't been done already 
# Can not be checked into github as the webhoook will be invalidated the second it is.
# create a file in the same directory as the gm_index_data.sh and place the webhook into it.
#For info on setting slack up for this see:https://api.slack.com/tutorials/slack-apps-hello-world
cp slack_webhook ~/gm_pipeline_snakemake_${version}/


#Throws classpath error if the jar is missing or not in the write spot.  
#If it crashes with that error make sure it is able to fine the jar.
docker exec  gmbuild_snakemake_index_data_${version} /bin/bash -c "cd /home/gmbuild/sm_build_org && ./all.sh /home/gmbuild/dev/${version}/db ${version}"



