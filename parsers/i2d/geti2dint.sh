#!/bin/bash

THRESHOLD=100

function applyThreshold {
	pushd $outdir

	# combine WranaLow, WranaMedium and WranaHigh into one group:
	cat Wrana* > WranaGroup
	rm -f WranaLow WranaMedium WranaHigh

	# combine StelzlLow, StelzlMedium into one group:
	cat StelzlLow StelzlMedium > StelzlLowMed
	rm -f StelzlLow StelzlMedium

	for file in *; do 
		printf "Checking $file... "
		if [[ -e $file && ! -d $file && $file != "WranaGroup" && $file != "StelzlLowMed" ]]; then
			lines=`wc -l $file | awk '{print $1}'`
			printf "lines: $lines\n"
			if [[ $lines -lt $THRESHOLD ]]; then 
				printf "Copying to under_threshold.txt and deleting file.\n"
				cat $file >> under_threshold
				rm -f $file
			fi
		else
			echo "ignoring."
		fi
	done
	popd	
}

function getInteractions {
	outdir=$1
	sourcefile=$2
	datafile=$3
	spreadsheet=$4
	pypath=$5
	maxlines=`wc -l $sourcefile | awk '{print $1}'`
	counter=1
	currline=''

	# need this for calling the python script when this script is 
	# called from the build scripts
	if [[ -z $pypath ]]; then 
		pypath="."
	fi

	maxlines=$(($maxlines + 1))
	rm -rf $outdir
	mkdir -p $outdir
	while [[ $counter -ne $maxlines ]]; do
		currline=`head -$counter $sourcefile | tail -1`

		# !!! space after ^{currline} is a TAB: ctrl-v tab
		grep "^${currline}	" $datafile | sort -u | awk '{print $2 "\t" $3 "\t" 1}' >> ${outdir}/${currline}

		counter=$((counter + 1))
	done

        # the 3 args to classify_i2d.py are organsim name, output dir, and spreadsheet file
	#python /Users/harold/Development/trunk/parsers/i2d/classify_i2d.py $outdir $outdir $spreadsheet
	echo "python ${pypath}/classify_i2d.py $outdir $outdir $spreadsheet"
	python ${pypath}/classify_i2d.py $outdir $outdir $spreadsheet
exit
	applyThreshold $outdir
}


if [[ -z $1 && -z $2 && -z $3 && -z $4 ]]; then 
	echo "usage: `basename $0` organism source tabfile spreadsheet [pypath]"
	exit 0
fi


echo "getting interaction for $1 , source: $2 , tab: $3, spreadsheet: $4, pypath (optional): $5"
getInteractions $1 $2 $3 $4 $5
