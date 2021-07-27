#!/usr/bin/env python

import os, sys
from configobj import ConfigObj

threshold = 100
config = None

org_names = []
full_org_names = []
genemania_org_mappings = {}


#org_names = ['At', 'Hs', 'Mm', 'Dm', 'Ce', 'Sc']
#full_org_names = ['Arabidopsis_thaliana', 'Homo_sapiens', 'Mus_musculus', 'Drosophila_melanogaster', 'Caenorhabditis_elegans', 'Saccharomyces_cerevisiae']

#genemania_org_mappings = {
#	'Arabidopsis_thaliana': 'At',
#	'Homo_sapiens': 'Hs',
#	'Mus_musculus': 'Mm',
#	'Drosophila_melanogaster': 'Dm', 
#	'Caenorhabditis_elegans': 'Ce', 
#	'Saccharomyces_cerevisiae': 'Sc'
#}

list_of_data_file = 'data_processed.txt'

def write_flat_file_by_pubmed(lines, pub_exp, output_name, output_dir):
	'''
	takes lines of biogrid and makes a separate flat file for a 
	given pubmedID-experimentType
	'''
	tid = pub_exp.find(':')

	output_file =  output_name + 'PID_' + pub_exp[0:tid] + '_' + pub_exp[tid + 1:] + '-flat_file.txt'
	print 'Output file:', output_file

	out = open(os.path.join(output_dir, output_file), 'w')
	out.write('Gene_A' + '\t' + 'Gene_B' + '\t' + 'Score' + '\t' + 
		'Evidence_code' + '\t' + 'Experiment_type' + '\n')

	skipped_headers = False
	for line in lines:
		if not skipped_headers:
			if line.startswith('INTERACTOR_A'):
				skipped_headers = True
			continue
		tmp_line = line.strip().split('\t')
		unique_id = tmp_line[8] + ':' + tmp_line[6]

		if pub_exp.find(unique_id) > -1:
			to_write = tmp_line[2] + '\t' + tmp_line[3] + '\t' + \
				'1' + '\t' + 'PUBMED:'+ tmp_line[8] + '\t' + tmp_line[6] + '\n'

			out.write(to_write)
	out.close()

def write_flat_file_ss(lines, small_scale, output_name, output_dir):
	'''
	lines is a list with lines[i] the line i in biogrid file.
	small_scale is unique pubmedId_experimentType dictionary which had less
	than threshold associated interactions.

	This makes two types of files: small scale GI and small scale PPI files.
	GI in biogrid starts with Phenotypic enhancement, Synthetic or Dosage. 
	The rest are PPIs.

	Output file names start with output_name and are either output_name+ss_GI
	or output_name+ss_PPI.

	Assumption: 
	1. line[i][0] = gene name 1, and line[i][1] = gene name 2.
	2. line[i][8] = pubmed ID
	3. line[i][6] = experiment type.
	'''

	gi = ['Phenotypic', 'Synthetic', 'Dosage']

	gi_file_path = os.path.join(output_dir, output_name + '_ss_GI-flat_file.txt')
	ppi_file_path = os.path.join(output_dir, output_name + '_ss_PPI-flat_file.txt')

	output_gi = open(gi_file_path, 'w')
	output_ppi = open(ppi_file_path, 'w')

	output_gi.write('Gene_A' + '\t' + 'Gene_B' + '\t' + 'Score' + '\t' + 
		'Evidence_code' + '\t' + 'Experiment_type' + '\n')

	output_ppi.write('Gene_A' + '\t' + 'Gene_B' + '\t' + 'Score' + '\t' + 
		'Evidence_code' + '\t' + 'Experiment_type' + '\n')


	# keep a counter to keep track of how many lines are in each file
	lines_in_gi = 0
	lines_in_ppi = 0

	skipped_headers = False
	for line in lines:
		if not skipped_headers:
			if line.startswith('INTERACTOR_A'):
				skipped_headers = True
			continue
		tmp_line = line.strip().split('\t')
		unique_id = tmp_line[8] + ':' + tmp_line[6]

		if small_scale.has_key(unique_id):
			p = small_scale[unique_id]
			flag = 0

			for item in gi:
				if item in tmp_line[6]:
					output_gi.write(tmp_line[2] + '\t' + tmp_line[3] + '\t' 
						+ '1' + '\t' + 'PUBMED:' + tmp_line[8] + '\t' + tmp_line[6] + '\n')
					lines_in_gi += 1
					break
			else:
				if tmp_line[8] != 'PUBMED_ID':
					output_ppi.write(tmp_line[2] + '\t' + tmp_line[3] + '\t' + 
						'1' + '\t' +'PUBMED:' +  tmp_line[8] + '\t' + tmp_line[6] + '\n')
					lines_in_ppi += 1

	output_gi.close()
	output_ppi.close()

	print 'GI saved in', gi_file_path
	print 'PPI saved in', ppi_file_path

	if (lines_in_gi < 50):
		to_delete = os.path.join(output_dir, output_name + '_ss_GI-flat_file.txt')
		print 'Removing because under threshold:', to_delete
		os.remove(to_delete)

	if (lines_in_ppi < 50): 
		to_delete = os.path.join(output_dir, output_name + '_ss_PPI-flat_file.txt')
		print 'Removing because under threshold:', to_delete
		os.remove(to_delete)

def process_biogrid_file(file_name, output_dir):
	'''
	takes a file and creates separate gene \t gene \t score files.
	There is a separate file for each unique pubmedID-experiment type that has
	more than 100 interactions. Otherwise it groups interactions together by 
	experiment type.
	The files are put in the organism_name/direct directory.
	'''

	print 'Processing %s -> %s' % (file_name, output_dir)

	dict_pub_exp = {}
	dict_pub_exp_genes = {}
	list_ss = {}
	list_pub = []

	tmp_file_name = file_name.split('/')[-1]
	output_name = tmp_file_name[:tmp_file_name.find('tab') ]

	# make unique id dictionary from id+experiment type and store 
	# how many types each unique id is present
	print 'opening file:', file_name
	f = open(file_name)
	lines = f.readlines()
	f.close()

	skipped_headers = False
	for line in lines:
		if not skipped_headers:
			if line.startswith('INTERACTOR_A'):
				skipped_headers = True
			continue

		tmp_line = line.strip().split('\t')
		#print tmp_line
		unique_id = tmp_line[8] + ':' + tmp_line[6]

		if dict_pub_exp.has_key(unique_id):
			dict_pub_exp[unique_id] += 1
		else:
			dict_pub_exp[unique_id] = 1

	# find all entries with more than 100 interactions and 
	# make separate files for them
	for item in dict_pub_exp.keys():
		if dict_pub_exp[item] >= threshold:
			list_pub.append(item)
		elif item != 'PUBMED_ID':
			list_ss[item] = 1

	for item in list_pub:
		write_flat_file_by_pubmed(lines, item, output_name, output_dir)

	write_flat_file_ss(lines, list_ss, output_name, output_dir)

def process():
	for org in org_names:
		if os.path.exists(os.path.join(org, 'raw')):
			raw_files = os.listdir(os.path.join(org, 'raw'))

			if len(raw_files) == 0:
				print '[WARNING] No raw file found for', org

			for rfile in raw_files:
				if rfile.find('BIOGRID') != -1:
					file_name = os.path.join(org, 'raw', rfile)
					output_dir = os.path.join(org, 'processed', 'direct')
					process_biogrid_file(file_name, output_dir)
					break
		else:
			print 'No files to process for', org


def prepare_files():
	global full_org_names 
	print "in prepare_files()"
	curr_dir_list = os.listdir('.')
	print "curr_dir_list:", curr_dir_list
	print "full_org_names:", full_org_names

	for org in full_org_names: 
		for in_file in curr_dir_list:
			print "Checking if org %s is in filename %s" % (org, in_file)
			if org in in_file:
				print "Found %s in %s" % (org, in_file)

				# copy file to the organism/raw directory without the headers
				output_file = os.path.join(genemania_org_mappings[org], 'raw', in_file)
				out = open(output_file, 'w')

				currline = 0
				for line in open(in_file):
					# the first 35 lines are headers, ignore them
					if currline >= 35:
						out.write(line)
					else:
						currline += 1
				break


def make_data_folders():
	sub_dir = ['raw', 'processed']
	sub_sub_dir = ['direct', 'shared_neighbour']
	curr_dir_list = os.listdir('.')

	for org in org_names:
		try:
			print 'Creating directories for', org
			os.mkdir(org)
			os.mkdir(os.path.join(org, 'raw'))
			os.mkdir(os.path.join(org, 'processed'))
			os.mkdir(os.path.join(org, 'processed', 'direct'))
			os.mkdir(os.path.join(org, 'processed', 'shared_neighbor'))
		except Exception, e:
			print e

def usage(name):
	print 'usage: %s [makedir|process] db.cfg' % name
	print 'create directory structures: %s makedir db.cfg' % name
	print 'process biogrid files      : %s process db.cfg' % name

def init_organisms(dbcfg): 
	global full_org_names

	# populate the organism lists and mappings with the organisms we 
	# want to import
	config = ConfigObj(dbcfg)

	full_org_names = config['BuildScriptsConfig']['biogrid_org'].split()
	for fullname in full_org_names: 
		shortname = fullname.split('_')[0][0] + fullname.split('_')[1][0]	
		org_names.append(shortname)
		genemania_org_mappings[fullname] = shortname


if __name__ == '__main__':
	if len(sys.argv) == 2:
		usage(sys.argv[0])
		sys.exit(0)

	init_organisms(sys.argv[2])

	if sys.argv[1] == 'makedir':
		make_data_folders()
	elif sys.argv[1] == 'process':
		prepare_files()
		process()	
	else:
		usage(sys.argv[0])
		sys.exit(0)
