#!/bin/bash
#
# For testing pathway commons parsing scripts
#
#

export PYTHONPATH=".:${HOME}/Development/trunk/loader/src/main/python/dbutil/"

function watch_processes {
	for job in `jobs -p`; do
		wait $job || let "fail+=1"
	done
}

function proc_pmid {
	./do_pmid.py edges/${1}-edge-attributes.txt nodes/${1}-node-attributes.txt out.pubmed.3 .
}

function proc_source {
	./do_source.py edges/${1}-edge-attributes.txt nodes/${1}-node-attributes.txt out.source.3 .
}

for i in arabidopsis-thaliana-mouse-ear-cress-3702 caenorhabditis-elegans-6239 drosophila-melanogaster-fruit-fly-7227 homo-sapiens-9606 mus-musculus-10090 rattus-norvegicus-10116 saccharomyces-cerevisiae-4932; do 


#for i in caenorhabditis-elegans-6239; do 
#for i in drosophila-melanogaster-fruit-fly-7227; do 
#for i in rattus-norvegicus-10116; do 
#for i in mus-musculus-10090; do 
#for i in homo-sapiens-9606; do 
	proc_pmid $i &
	proc_source $i &
done
fail=0
watch_processes
