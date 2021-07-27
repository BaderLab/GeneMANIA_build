#!/bin/bash
# We're obtaining interpro IDs for Arabidopsis from Ensembl Plant. 
# For some reason the gene IDs are stored with the suffix -TAIR-G which 
# causes our mapping to fail. This may be because our ID mappings are
# still using Ensembl 55. As a temporary patch, this script removes the
# suffix from the raw At file before processing it. 

if [[ $# -ne 2 ]]; then 
	echo "usage: `basename $0` path_to_raw_At_file raw_At_file"
	echo "example: `basename $0` db/srcdb/data/interpro/At/raw all.txt"
	exit 0
fi

pushd $1
sed 's/-TAIR-G//g' $2 > $2.new
mv $2.new $2
popd
