#!/bin/bash

# set this to -t to use test mode, leave blank otherwise
#TESTMODE="-t"
TESTMODE=""

function watch_processes {
	for job in `jobs -p`; do 
		wait $job || let "fail+=1"
	done
}

function check_defaults {
	echo "[Checking if all default networks were properly set]"
	while read line; do 
		passed=0

		# ignore comments
		if [[ "${line:0:1}" == "#" ]]; then 
			continue
		fi

		echo "[Checking $line using auto_name]"
		result=`./r3.sh updater ${SRCDB}/db.cfg -f dataset.auto_name="$line" -f dataset.default_selected=1 $TESTMODE`
		if [[ ! -z $result ]]; then 
			passed=1
		else
			# try checking using name
			result=`./r3.sh updater ${SRCDB}/db.cfg -f dataset.name="$line" -f dataset.default_selected=1 $TESTMODE`
			if [[ ! -z $result ]]; then
				passed=1
			fi
		fi
		if [[ $passed -eq 0 ]]; then
			echo "[Failed to set: $line ]"
		fi
	done < $1
}


function set_coexp {
	echo "[Resetting co-expression default networks to not selected]"
	./r3.sh updater ${SRCDB}/db.cfg -f dataset.group=coexp -s dataset.default_selected=0 $TESTMODE 

	echo "[Setting co-expression default networks]"
	while read line; do 
		# ignore comments
		if [[ "${line:0:1}" == "#" ]]; then 
			continue
		fi 

		echo ""
		echo "[Setting: $line using auto_name]"
		echo "./r3.sh updater ${SRCDB}/db.cfg -f dataset.auto_name=\"$line\" -s dataset.default_selected=1 $TESTMODE"
		result=`./r3.sh updater ${SRCDB}/db.cfg -f dataset.auto_name="$line" -s dataset.default_selected=1 $TESTMODE`

		if [[ -z $result ]]; then 
			echo "    [Trying again using name]"
			echo "    ./r3.sh updater ${SRCDB}/db.cfg -f dataset.name=\"$line\" -s dataset.default_selected=1 $TESTMODE"
			result=`./r3.sh updater ${SRCDB}/db.cfg -f dataset.name="$line" -s dataset.default_selected=1 $TESTMODE`

			if [[ -z $result ]]; then 
				echo "[Error setting $line]"
			fi
		fi
	done < $1
}

function set_gi {
	echo "[Setting genetic interaction default networks]"
	./r3.sh updater ${SRCDB}/db.cfg -f dataset.group=gi -s dataset.default_selected=1 $TESTMODE 
}

function set_coloc {
	echo "[Setting co-localization default networks]"
	./r3.sh updater ${SRCDB}/db.cfg -f dataset.group=coloc -s dataset.default_selected=1 $TESTMODE 
}

function set_pi {
	echo "[Setting genetic interaction default networks]"
	./r3.sh updater ${SRCDB}/db.cfg -f dataset.group=pi -s dataset.default_selected=1 $TESTMODE 
}

function set_other {
	echo "[Setting other default networks]"
	./r3.sh updater ${SRCDB}/db.cfg -f dataset.group=other -s dataset.default_selected=1 $TESTMODE
}

function set_path {
	echo "[Setting other default networks]"
	./r3.sh updater ${SRCDB}/db.cfg -f dataset.group=path -s dataset.default_selected=1 $TESTMODE
}

function set_pred {
	echo "[Setting all predicted default networks]"
	./r3.sh updater ${SRCDB}/db.cfg -f dataset.group=predict -s dataset.default_selected=1 $TESTMODE

	echo "[Unsetting blacklisted predicted networks]"
	while read line; do 
		echo "[Unsetting $line]"
		./r3.sh updater ${SRCDB}/db.cfg -f dataset.auto_name="$line" -f dataset.group=predict -s dataset.default_selected=0 $TESTMODE 
		./r3.sh updater ${SRCDB}/db.cfg -f dataset.name="$line" -f dataset.group=predict -s dataset.default_selected=0 $TESTMODE
	done < $1
}

function set_spd {
	echo "[Setting all shared protein domain default networks]"
	./r3.sh updater ${SRCDB}/db.cfg -f dataset.group=spd -s dataset.default_selected=1 $TESTMODE
}


function onkill {
	echo "[Terminating script]"
	exit 1
}


trap 'onkill' INT

# if db.cfg is provided as the first argument, assume the user
# wants to refresh bp.cfg
if [[ ! -z $1 ]]; then 
	python create_config.py $1
fi

./check.sh
if [[ $? -eq 1 ]]; then 
	exit 1
fi

source ./bp.cfg
start=`date`

pushd ${CODE_DIR}/loader/

set_coexp ${CODE_DIR}/build-process/default_networks/coexp_defaults.txt 
set_coloc
set_gi 
set_pi 
set_other 
set_path 
set_pred ${CODE_DIR}/build-process/default_networks/pred_unselected.txt 
set_spd 

#fail=0
#watch_processes
#if [[ $fail -ne 0 ]]; then 
#	echo "[An error occurred while setting default networks]"
#	exit 1
#fi

echo "[Applying post edits]"
./post_edit_cfg.sh ${SRCDB}/db.cfg ${SRCDB}

#check_defaults ${CODE_DIR}/build-process/default_networks/coexp_defaults.txt

popd

stop=`date`
echo "Start: $start"
echo "Stop : $stop"
exit 0
