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

./idmapper.pl $DATADIR/Work caenorhabditis_elegans Ce 1
./idmapper.pl $DATADIR/Work arabidopsis_thaliana At 3
./idmapper.pl $DATADIR/Work rattus_norvegicus Rn 5
./idmapper.pl $DATADIR/Work homo_sapiens Hs 7
./idmapper.pl $DATADIR/Work mus_musculus Mm 9
./idmapper.pl $DATADIR/Work drosophila_melanogaster Dm 11
./idmapper.pl $DATADIR/Work saccharomyces_cerevisiae Sc 13
./idmapper.pl $DATADIR/Work danio_rerio Dr 15
./idmapper.pl $DATADIR/Work escherichia_coli_k_12 Ec 17

#./idmapper.pl ~/Work escherichia_coli_str_k_12_substr_mg1655 Ec 17
#./idmapper.pl ~/Work escherichia_coli_str_k_12_substr_w3110 Ec 17

#add the protein domain download here so that we keep all perl dependcies together
./1.export_spd_from_ensembl.sh $ensembl_version spd.cfg 

#cp the shared protein domains to same place as the mapping directory
cp -r spd $DATADIR/Work/spd

cd $DATADIR/Work
#get the static Genemania network data from download.baderlab.org
wget http://download.baderlab.org/GeneMANIA/data_build/GeneMANIA_static.tar.gz 

tar -xzvf GeneMANIA_static.tar.gz

