#!/usr/bin/env python
#
# This file is part of GeneMANIA.
# Copyright (C) 2010 University of Toronto.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#

import sys, os, shutil, datalib, jobqueue
from optparse import OptionParser
from configobj import ConfigObj

# output directory, typically db/srcdb/data/biogrid_direct
output_dir = ''

# input directory, typically db/srcdb/biogrid
input_dir = ''

# master config file, typically db/srcdb/db.cfg
config_file = ''
#master_config = ''

#organism_list = ['At', 'Ce', 'Dm', 'Hs', 'Mm', 'Sc']
organism_list = []

# map the experiment type to the group:
experiment = {
	# Co-localization:
	'Co-localization': 'coloc', 

	# Genetic Interactions:
	'Dosage Growth Defect': 'gi',
	'Dosage Lethality': 'gi',
	'Dosage Rescue': 'gi',
	'Negative Genetic': 'gi',
	'Phenotypic Enhancement': 'gi', 
	'Phenotypic Suppression': 'gi',
	'Positive Genetic': 'gi',  
	'Synthetic Growth Defect': 'gi',
	'Synthetic Haploinsufficiency': 'gi', 
	'Synthetic Lethality': 'gi', 
	'Synthetic Rescue': 'gi', 

	# Physical Interactions:
	'Affinity Capture-Luminescence': 'pi', 
	'Affinity Capture-MS': 'pi', 
	'Affinity Capture-Western': 'pi', 
	'Biochemical Activity': 'pi', 
	'Co-crystal Structure': 'pi', 
	'Co-fractionation': 'pi', 
	'Co-purification': 'pi', 
	'Far Western': 'pi', 
	'FRET': 'pi', 
	'PCA': 'pi', 
	'Protein-peptide': 'pi', 
	'Reconstituted Complex': 'pi', 
	'Two-hybrid': 'pi'
}

def create_output_dir(data_dir, collection_subdir='biogrid_direct'):
	'''
	Set up the output directories for biogrid organisms.
	'''
	global output_dir
	output_dir = os.path.join(data_dir, collection_subdir)
	print 'output_dir dir:', output_dir

	# trash the existing output_dir so we start with fresh data
	if os.path.exists(output_dir):
		shutil.rmtree(output_dir)

	# create root output directory
	print 'creating', output_dir
	os.mkdir(output_dir)

	# create organism directories
	input_org_dir = os.listdir(input_dir)
	for i in input_org_dir:
		if i in organism_list:
			org_dir = os.path.join(output_dir, i)
			print 'creating', org_dir
			os.mkdir(org_dir)

			# create raw dir
			input_raw_dir = os.path.join(input_dir, i, 'raw')
			output_raw_dir = os.path.join(org_dir, 'raw')

			print 'Copying %s to %s' % (input_raw_dir, output_raw_dir)
			shutil.copytree(input_raw_dir, output_raw_dir)

def process():
	'''
	Go through each file in the input directory and process them
	'''
	# get the contents of the input directory
	input_organisms = os.listdir(input_dir)
	print 'Processing for', input_organisms	

	# process the direct files under the organism/processed/direct directory
	for i in input_organisms:
		if i in organism_list:
			file_dir = os.path.join(input_dir, i, 'processed', 'direct')
			print 'Checking file_dir:', file_dir

			if os.path.exists(file_dir):
				# get contents of file directory
				file_list = os.listdir(file_dir)
				for j in file_list:
					print 'Copying %s to raw directory' % j
					srcpath = os.path.join(file_dir, j)
					dstpath = os.path.join(output_dir, i, 'raw', j)
					print 'Source:', srcpath
					print 'Dest  :', dstpath
					shutil.copyfile(srcpath, dstpath)

					print 'Processing', j
					process_biogrid(file_dir=file_dir, file_name=j, organism=i)

def process_biogrid(file_dir, file_name, organism):
	'''
	This creates the configuration files
	'''
	file = os.path.join(file_dir, file_name)
	print 'file to parse:', file

	# [dataset]
	type = 'DIRECT'
	default_selected = '0'
	name = ''
	description = ''
	keywords = ''
	group = ''
	source = 'BIOGRID'

	# [gse]
	gse_id = 'N/A'
	title = 'N/A'
	contributor = 'N/A'
	num_samples = '0'
	platforms = 'N/A'	
	raw_data = file_name
	pubmed_id = ''

	mapping_found = False

	# process small-scale networks first. a lot of the information we need
	# is included in the file name, such as 'small scale', 'organism', and 'group'
	if file.find('_ss_') != -1:
		print 'Small-scale studies::', file_name

		keywords = 'Small-scale studies'

		# get the group. a small-scale file looks like this:
		# BIOGRID-ORGANISM-Homo_sapiens-2.0.63._ss_PPI-flat_file.txt
		# the group is between '_ss_' and '-flat_file', extract it.
		tmp = file_name[file_name.find('_ss_') + len('_ss_'):]
		tmp = tmp[:tmp.find('-')]
		group = tmp.lower()

		# for PPI, shorten it to PI
		if group == 'ppi':
			group = 'pi'

		mapping_found = True

	# process non-small-scale networks. information included in the file name
	# are pubmed ID and experiment
	else:
		print 'File:', file_name

		# non-small-scale files look like this:
		# BIOGRID-ORGANISM-Saccharomyces_cerevisiae-2.0.63.PID_20093466_Positive Genetic-flat_file.txt

		# let's grab the pubmed id first, this is PID_NNNNNNNN
		tmp = file_name[file_name.find('PID_') + len('PID_'):]
		pubmed_id = tmp[:tmp.find('_')]

		# now grab the keywords, which is the experiment type. right now tmp should be:
		# 20093466_Positive Genetic-flat_file.txt
		# start at length of pubmed id + 1 (for the underscore), and end at the first 
		# index of '-flat_file' to get the experiment type
		tmp = tmp[len(pubmed_id) + 1:tmp.find('-flat_file')]
		keywords = tmp
		print '\tTmp:', tmp

		# determine the group based on the experiment type. 
		try:
			group = experiment[keywords]
			mapping_found = True
		except:
			print 'No mapping for %s in %s' % (keywords, file)
			mapping_found = False

	# print the results of our parsing
	print '\tType:', type
	print '\tOrganism:', organism
	print '\tDefault:', default_selected
	print '\tName:', name
	print '\tDescription:', description
	print '\tKeywords:', keywords
	print '\tGroup:', group
	print '\tSource:', source
	print '\tPubmed:', pubmed_id
	print '\tRaw data:', raw_data

	# write to text file only if we have a valid mapping 
	print 'Write to file:', mapping_found
	if mapping_found:
		write_to_config(organism, keywords, group, pubmed_id, raw_data, file_dir, file_name)

def write_to_config(organism, keywords, group, pubmed_id, raw_data, file_dir, file_name):
	'''
	Write the configuration data to file
	'''
	organism_data_dir = os.path.join(output_dir, organism)

	cfg = datalib.make_empty_config() 
	cfg.filename = os.path.join(organism_data_dir, file_name) + '.cfg'
	print 'Creating config', cfg.filename

	cfg['dataset']['type'] = 'DIRECT'
	cfg['dataset']['organism'] = organism
	
	# search the master config to determine if default_selected should be set to 0 or 1. 
	master_cfg = datalib.load_main_config(config_file)
	default_network_list = datalib.lookup_field(master_cfg, 'processing.biogrid_default_networks')[organism]
	for item in default_network_list:
		# if item is in the file name, then set default_selected to 1. item will either be GI, PPI, or 
		# the pubmed ID: 
		if item in file_name:
			print 'Setting default network for', file_name
			cfg['dataset']['default_selected'] = '1'
			break
	else:
		cfg['dataset']['default_selected'] = '0'

	cfg['dataset']['name'] = ''
	cfg['dataset']['description'] = ''
	cfg['dataset']['keywords'] = keywords
	cfg['dataset']['group'] = group
	cfg['dataset']['source'] = 'BIOGRID'

	cfg['gse']['raw_data'] = raw_data
	cfg['gse']['pubmed_id'] = pubmed_id

	if keywords == 'Small-scale studies': 
		cfg['dataset']['name'] = 'BIOGRID-SMALL-SCALE-STUDIES'

	cfg.write()

def init_organisms(dbcfg):
	# get the organisms we want to import from the config file and 
	# put their shortname form in the organism_list
	config = ConfigObj(dbcfg)
	org_longnames = config['BuildScriptsConfig']['biogrid_org'].split()
	for longname in org_longnames:
		shortname = longname.split('_')[0][0] + longname.split('_')[1][0]
		print 'Appending %s to organism list' % (shortname)
		organism_list.append(shortname)
		

def main(args):
	global input_dir
	global config_file
	usage = 'usage %prog master_config_file.cfg input_dir'
	description = 'load interactions from biogrid, processed by some intermediate scripts'
	parser = OptionParser(usage=usage, description=description)
	(options, args) = parser.parse_args(args)

	if len(args) != 2: 
		parser.error('require one master config file')

	config_file = args[0]
	input_dir = args[1]

	print 'config_file:', config_file
	init_organisms(config_file)

	master_config = datalib.MasterConfig(config_file)
	data_dir = master_config.getDataDir()

	create_output_dir(data_dir)
	process()

if __name__ == '__main__':
	main(sys.argv[1:])
