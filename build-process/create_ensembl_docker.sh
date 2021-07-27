#create a directory for the ensembl_data (if it doesn't exist)
if [ ! -d $HOME/ensembl_data ]
then
	mkdir $HOME/ensembl_data
fi

if [ ! -d $HOME/db_files ]
then
	mkdir $HOME/db_files
fi

if [ ! -d $HOME/gmbuild_code/genemania-private ]
then
	echo "genemania-private repo is missing.  Please clone before initiating build"
	exit
fi


#create ensembl docker and launch it
if [ ! "$(docker ps -q -f name=gmbuild_ensembl)" ]; then
	docker run -d -t -v $HOME/ensembl_data:/home/gmbuild/ensembl_data -v $HOME/gmbuild_code/genemania-private:/home/gmbuild/ensembl_code -v $HOME/gmbuild_code/genemania-private/Docker_containers/Ensembl_docker/custom_cnf:/etc/mysql/conf.d -v $HOME/db_files:/var/lib/mysql --name gmbuild_ensembl baderlab/gmbuild_ensembl 

	#unfortunately we are unable to update the docker image but it is 
	# missing a program we need install.  Install wget 
docker exec -t gmbuild_ensembl bash -c "apt-get install wget"
	
	#wait to make sure the container has started correctly before processing
	sleep 300
fi

#download the ensembl data - there is not requirement to run this script within the docker.
#
#TODO: (need to fix)have had some issues with rsync timing out for some of the organisms for some reason.  
# might be good idea to make sure all the species are downloaded before proceeding.
docker exec -t gmbuild_ensembl /home/gmbuild/ensembl_code/ensembl_mirror/get_ensembl.sh

#load ensembl data into database
docker exec gmbuild_ensembl /home/gmbuild/ensembl_code/ensembl_mirror/create_ensembl.sh

#create ensembl identifier mapping files
docker exec gmbuild_ensembl /home/gmbuild/ensembl_code/identifier-mapper-perl/runall.sh

#figure out which is the newest ensembl directory
dir_name=$(ls -td /home/gmbuild/ensembl_data/* | head -1)

#copy the static networks over to current ensembl directory
#
# TODO: need to host these networks somewhere we can pull them from
# TODO: not copying over because of permission issue.  manually chmod of Work dir and copied file. (next step won't run without these files)
#wget --verbose http://download.baderlab.org/GeneMANIA/data_build/GeneMANIA_static.tar.gz -o ${dirname}/Work/GeneMANIA_static.tar.gz

#cp -r $HOME/static_networks/GeneMANIA_static ${dir_name}/Work/

