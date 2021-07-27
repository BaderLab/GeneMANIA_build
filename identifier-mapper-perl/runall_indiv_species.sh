#!/bin/bash
DATADIR=$(ls -td /home/gmbuild/ensembl_data/* | head -1)

echo $DATADIR

#check the ensembl version
cd $DATADIR
for f in `ls -d */`
do
	current_ensembl_version=$(echo $f | awk '{n=split($0,a,"_");  print a[n-1]}')	
	if [ -z "$ensembl_version" ];
	then
		ensembl_version=$current_ensembl_version;
	fi;
	
	if [ "$ensembl_version" != "$current_ensembl_version" ];
	then
		echo "There are multiple ensembl versions present in the data file.  Can not parse files with the same ensembl library\n";
		echo "$current_ensembl_version and $ensembl_version";
		exit;
	fi;

	#echo $ensembl_version
done

echo "Using ensembl version $ensembl_version"
git clone https://github.com/Ensembl/ensembl.git --branch release/$ensembl_version --single-branch $HOMEDIR/ensembl_$ensembl_version
export PERL5LIB=$HOMEDIR/ensembl_$ensembl_version/modules

mkdir $DATADIR/Work

cd /home/gmbuild/ensembl_code/identifier-mapper-perl

./idmapper.pl $DATADIR/Work tetrahymena_thermophila Tt 19

#add the protein domain download here so that we keep all perl dependcies together
./1.export_spd_from_ensembl.sh $ensembl_version spd_tetra.cfg

#cp the shared protein domains to same place as the mapping directory
cp -r spd $DATADIR/Work/spd

#If you are using any of the species present in main GeneMANIA you might want to upcomment the below.  It downloades static networks for Human, Mouse, Fly, ... present in GeneMANIA - it requires wget which unfortunately was not installed on the docker.

#cd $DATADIR/Work

#apt update && apt upgrade
#apt install wget

#get the static Genemania network data from download.baderlab.org
#wget http://download.baderlab.org/GeneMANIA/data_build/GeneMANIA_static.tar.gz 

#tar -xzvf GeneMANIA_static.tar.gz

