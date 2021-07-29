#!/bin/bash
#  
# repair problems in geo metadata

if [[ -z $1 && -z $2 ]]; then 
	echo "usage: `basename $0` db.cfg dbdir"
	exit 0
fi

dbcfg=$1
dbdir=$2

# in r6b8 we had human co-expression from GEO GSE16446 being assigned one pubmed id,
# and in r7 a different one. it has multiple pubmed citations recorded in geo, but
# geometadb captures only one of these (and it seems to change over time).
# override to the one we had in r6 so the network name stays consistent

echo "./r3.sh updater $dbcfg -f gse.gse_id=GSE16446 -s gse.pubmed_id=20098429"
./r3.sh updater $dbcfg -f gse.gse_id=GSE16446 -s gse.pubmed_id=20098429

