#!/bin/bash

#./check.sh
source bp.cfg
start=`date`

confirm=0

if [[ ${1} == "confirm" ]]; then 
    confirm=1
fi

for org in At Ce Dm Dr Ec Hs Mm Rn Sc; do 
#for org in At Ce Dm Dr Mm Rn Sc; do 
#for org in Hs; do 
	irefp="${SRCDB}/iref/${org}"
	biogridp="${SRCDB}/biogrid/${org}/processed/direct"

	#irefp="/home/gmbuild/dev/r12.test/db/iref/$org"
	#biogridp="/home/gmbuild/dev/r12.test/db/biogrid/$org/processed/direct"

	#irefp="/home/gmbuild/dev/r14/db/iref/$org"
	#biogridp="/home/gmbuild/dev/r14/db/biogrid/$org/processed/direct"


	# find duplicates by pubmed id
	pushd $irefp >/dev/null
	for i in *; do  
		pmid=`echo $i | cut -d. -f1`

		# not a pubmed, move to the next one
		if [[ ! $pmid =~ ^[0-9]+$ ]]; then 
			continue
		fi


		# try to find a duplicate in biogrid, however biogrid sometimes
		# has two datasets with the same pubmed id. in that case, we 
		# sum the total of the two datasets
		biogrid_cnt=0
		biogrid_dups=`ls -m1 "${biogridp}" | grep $pmid | wc -l`

		biogrid_fname=""
		biogrid_fname1=""
		biogrid_fname2=""
		twofound=0				# set to 1 if two biogrid dataset duplicates are found

		delete_biogrid=0		# set to 1 if we delete biogrid
		delete_iref=0			# set to 1 if we delete iref

		if [[ $biogrid_dups -eq 1 ]]; then 
			# 1 dataset duplicate found
			biogrid_fname=`ls -m1 "${biogridp}" | grep $pmid`
			echo "[+] 1 dataset found for $pmid"
			echo "    [+] biogrid_fname $biogridp/$biogrid_fname"
			biogrid_cnt=`wc -l "$biogridp/${biogrid_fname}" | cut -d" " -f1`
			echo "    [+] biogrid interactions: $biogrid_cnt"
		elif [[ $biogrid_dups -eq 2 ]]; then 
			# 2 dataset duplicates found
			echo "[+] 2 datasets found for $pmid"
			twofound=1
			biogrid_fname1=`ls -m1 "${biogridp}" | grep $pmid | head -1`
			biogrid_fname2=`ls -m1 "${biogridp}" | grep $pmid | tail -1`
			echo "    [+] dataset1 $biogrid_fname1"
			echo "    [+] dataset2 $biogrid_fname2"
			cnt1=`wc -l "$biogridp/${biogrid_fname1}" | cut -d" " -f1`
			cnt2=`wc -l "$biogridp/${biogrid_fname2}" | cut -d" " -f1`
			biogrid_cnt=$(($cnt1+$cnt2))
			echo "    [+] biogrid interactions1: $cnt1"
			echo "    [+] biogrid interactions2: $cnt2"
			echo "    [+] biogrid total interactions: $biogrid_cnt"
		else
			# no duplicate
			continue
		fi 

		# get iref interactions
		iref_cnt=`wc -l "$irefp/${pmid}.txt" | cut -d" " -f1`
		echo "    [+] iref interactions: $iref_cnt"


		# is biogrid > iref by at least 100 interactions? 
		if [[ $biogrid_cnt -gt $iref_cnt ]]; then 
			diffr=$(($biogrid_cnt-$iref_cnt))
			if [[ $diffr -ge 100 ]]; then  
				delete_iref=1
			else
				delete_biogrid=1
			fi
		else
			delete_biogrid=1
		fi


		# is biogrid > iref by at least 100 interactions? 
		if [[ $delete_iref -eq 1 ]]; then 
				echo "    [+] prefer biogrid for pmid $pmid"
				echo "    [!] deleting $irefp/${pmid}.txt"
				echo "    [!] deleting $irefp/../../data/iref_direct/$org/${pmid}_direct.cfg"
				rm -f "$irefp/${pmid}.txt"
				rm -f "$irefp/../../data/iref_direct/$org/${pmid}_direct.cfg"
		fi 

		if [[ $delete_biogrid -eq 1 ]]; then 
			# delete biogrid duplicate
			echo "    [+] prefer iref for pmid $pmid"

			if [[ $twofound -eq 1 ]]; then 
				echo "    [!] deleting $biogridp/$biogrid_fname1"
				echo "    [!] deleting $biogridp/$biogrid_fname2"

				echo "    [!] deleting $biogridp/../../../../data/biogrid_direct/$org/${biogrid_fname1}.cfg"
				echo "    [!] deleting $biogridp/../../../../data/biogrid_direct/$org/${biogrid_fname2}.cfg"

                if [[ confirm -eq 1 ]]; then
                    rm -f "$biogridp/../../../../data/biogrid_direct/$org/${biogrid_fname1}.cfg"
                    rm -f "$biogridp/../../../../data/biogrid_direct/$org/${biogrid_fname2}.cfg"
                fi
			else
				echo "    [!] deleting $biogridp/$biogrid_fname"
				echo "    [!] deleting $biogridp/../../../../data/biogrid_direct/$org/${biogrid_fname}.cfg"

                if [[ confirm -eq 1 ]]; then 
                    rm -f "$biogridp/${biogrid_fname}"
                    rm -f "$biogridp/../../../../data/biogrid_direct/$org/${biogrid_fname}.cfg"
                fi 
			fi 
		fi 

		echo "" 
	done
	popd >/dev/null
done

if [[ confirm -ne 1 ]]; then
    echo "[+] Test run completed. Run with 'confirm' arg to delete duplicates."
fi

stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
