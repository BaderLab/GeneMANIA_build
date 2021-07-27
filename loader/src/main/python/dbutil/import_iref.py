#!/usr/bin/env python

import sys, os, shutil, datalib, jobqueue
from optparse import OptionParser


def process(config_file, input_folder, collection_subdir = "iref"):
	masterConfig = datalib.MasterConfig(config_file)
	data_dir = masterConfig.getDataDir()

	import_iref(masterConfig, input_folder, collection_subdir)


def import_iref(config, dir, collection_subdir):
	for root, dirs, files in os.walk(dir):
		organism = os.path.basename(root)
		if files:
			for filename in files:
				if not filename.endswith(".txt"):
					continue
				fullname = os.path.join(root, filename)
				print "   ", fullname
				pubmed_id = filename[:filename.find(".")]
				print "   ", pubmed_id
				import_iref_data(config, collection_subdir + "_direct", organism, fullname, "Direct", pubmed_id=pubmed_id)


def import_iref_data(config, collection_subdir, organism, data_file, processing_type, pubmed_id): 
	processing_type_simple = processing_type.lower()
	processing_type_simple = processing_type_simple.replace(" ", "-")

	cfg_filename = "%s_%s.cfg" % (pubmed_id, processing_type_simple)
	data_dir = config.getDataDir()
	collection_dir = os.path.join(data_dir, collection_subdir)
	print "organism: %s" % (organism)
	organism_code = organism

	dir = os.path.join(collection_dir, organism_code)
	if not os.path.exists(dir):
		os.makedirs(dir)

	cfg_filename = os.path.join(dir, cfg_filename)
	print "importing", cfg_filename, organism_code, data_file

	cfg = datalib.make_empty_config()
	cfg.filename = cfg_filename

	cfg["gse"]["raw_data"] = os.path.basename(data_file)
	cfg["gse"]["raw_type"] = "BINARY_NETWORK"
	cfg["dataset"]["processing_type"] = processing_type

	# handle genetic interactions in iref properly
	if "_GI" in data_file:
		cfg["dataset"]["group"] = "gi"
	else:
		cfg["dataset"]["group"] = "pi"

	raw_dir = config.config["FileLocations"]["raw_dir"]
	target = os.path.join(os.path.dirname(cfg.filename), raw_dir)
	if not os.path.exists(target):
		os.mkdir(target)

	target = os.path.join(target, os.path.basename(data_file))
	print "copying %s to %s" % (data_file, target)
	shutil.copyfile(data_file, target)

	cfg["dataset"]["organism"] = organism_code
	cfg["dataset"]["source"] = "IREF"

	if pubmed_id == "under_threshold" or pubmed_id == "under_threshold_GI":
		cfg["dataset"]["keywords"] = "Small-scale studies"
		cfg["dataset"]["name"] = "IREF-SMALL-SCALE-STUDIES"
	elif pubmed_id.isdigit() or "_GI" in pubmed_id:
		if "_GI" in pubmed_id:
			print "pubmed_id is", pubmed_id
			pubmed_id = pubmed_id.replace("_GI","")
		print "pubmed_id is", pubmed_id
		cfg["gse"]["pubmed_id"] = pubmed_id
	else:
		cfg["dataset"]["name"] = "IREF-%s" % (pubmed_id.replace("_", "-"))

	cfg.write()


def main(args):
	usage = "usage: %prog [options] master_config_file.cfg input_folder"
	description = "load interactions from iref index, processed via some intermediate scripts"
	parser = OptionParser(usage=usage, description=description)

	(options, args) = parser.parse_args(args)

	if len(args) != 2:
		parser.error("require one master config file")

	config_file = args[0]
	input_folder = args[1]
	process(config_file, input_folder)


if __name__ == "__main__":
	main(sys.argv[1:])
