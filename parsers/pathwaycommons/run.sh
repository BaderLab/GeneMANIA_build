#!/bin/bash 

function watch_processes {
	for job in `jobs -p`; do 
		wait $job || let "fail+=1"
	done
}
export PYTHONPATH=".:${HOME}/Development/trunk/loader/src/main/python/dbutil/"

# sample script that processes each file in the pubmed and source directories. Customize accordingly. 

# output dir for source files
out_srcid="out.source"

# output dir for pubmed files
out_pmid="out.pubmed"

# dir containing source input files
in_srcid="edges"

# dir containing pubmed input files
in_pmid="edges"

# nodes dir
nodes_dir="nodes"


trap exit INT

# save generated output into out.pubmed
rm -rf $out_pmid/edges
mkdir -p $out_pmid/edges
./parsepc.py pubmed ${in_pmid}/rattus-norvegicus-10116-edge-attributes.txt ${nodes_dir}/rattus-norvegicus-10116-node-attributes.txt $out_pmid ${HOME}/Development/db/small_srcdb/
#./parsepc.py pubmed ${in_pmid}/arabidopsis-thaliana-edge-attributes.txt ${nodes_dir}/arabidopsis-thaliana-node-attributes.txt $out_pmid 
#./parsepc.py pubmed ${in_pmid}/caenorhabditis-elegans-edge-attributes.txt ${nodes_dir}/caenorhabditis-elegans-node-attributes.txt $out_pmid 
#./parsepc.py pubmed ${in_pmid}/drosophila-melanogaster-edge-attributes.txt ${nodes_dir}/drosophila-melanogaster-node-attributes.txt $out_pmid & 
#./parsepc.py pubmed ${in_pmid}/homo-sapiens-edge-attributes.txt ${nodes_dir}/homo-sapiens-node-attributes.txt $out_pmid &
#./parsepc.py pubmed ${in_pmid}/mus-musculus-edge-attributes.txt ${nodes_dir}/mus-musculus-node-attributes.txt $out_pmid & 
#./parsepc.py pubmed ${in_pmid}/saccharomyces-cerevisiae-edge-attributes.txt ${nodes_dir}/saccharomyces-cerevisiae-node-attributes.txt $out_pmid & 


# save generated output into out.source
rm -rf $out_srcdi/edges
mkdir -p $out_srcid/edges
./parsepc.py source ${in_srcid}/rattus-norvegicus-10116-edge-attributes.txt ${nodes_dir}/rattus-norvegicus-10116-node-attributes.txt $out_srcid ${HOME}/Development/db/small_srcdb/
#./parsepc.py source ${in_srcid}/arabidopsis-thaliana-edge-attributes.txt ${nodes_dir}/arabidopsis-thaliana-node-attributes.txt $out_srcid 
#./parsepc.py source ${in_srcid}/caenorhabditis-elegans-edge-attributes.txt ${nodes_dir}/caenorhabditis-elegans-node-attributes.txt $out_srcid 
#./parsepc.py source ${in_srcid}/drosophila-melanogaster-edge-attributes.txt ${nodes_dir}/drosophila-melanogaster-node-attributes.txt $out_srcid & 
#./parsepc.py source ${in_srcid}/homo-sapiens-edge-attributes.txt ${nodes_dir}/homo-sapiens-node-attributes.txt $out_srcid &
#./parsepc.py source ${in_srcid}/mus-musculus-edge-attributes.txt ${nodes_dir}/mus-musculus-node-attributes.txt $out_srcid & 
#./parsepc.py source ${in_srcid}/saccharomyces-cerevisiae-edge-attributes.txt ${nodes_dir}/saccharomyces-cerevisiae-node-attributes.txt $out_srcid & 

fail=0
watch_processes

if [[ $fail -ne 0 ]]; then 
	echo "[AN ERROR OCCURRED DURING PARSING]"
	exit 1
else
	echo "[PARSING PATHWAYCOMMONS COMPLETED]"
fi
exit 0
