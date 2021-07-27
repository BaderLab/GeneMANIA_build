#!/usr/bin/env python

import sys, signal, os

mapping = {}

def handler(signum, frame):
	print 'Caught signal', signum
	sys.exit(0)

def create_mapping(mapfile):
	print 'creating mapping'
	for line in open(mapfile):
		tmp = line.split('\t')
		uniprot_id = tmp[0].strip()
		ensembl_id = tmp[1].strip()

		if len(ensembl_id) > 1:
			if ensembl_id.find(';'):
				ensembl_id = ensembl_id.split(';')[0]

			mapping[uniprot_id] = ensembl_id
			#print 'mapping %s to %s' % (uniprot_id, ensembl_id)

def main(argv):

	if len(argv) < 2:
		print 'usage: fixi2dfly.py idmapping.tab file1...fileN'
		sys.exit(0)

	signal.signal(signal.SIGINT, handler)

	create_mapping(argv[0])
	if not os.path.exists('fly.mapped'): 
		os.mkdir('fly.mapped')


	file_list = argv[1:]

	for infile in file_list:
		print 'processing', infile

		outfile = open('fly.mapped/' + infile, 'w')

		for line in open(infile):
			gene_a = None
			gene_b = None
			tmp = line.split('\t')

			#print 'uniprot gene_a: %s , gene_b: %s' % (tmp[0], tmp[1])
			if mapping.has_key(tmp[0]):
				gene_a = mapping[tmp[0]]

			if mapping.has_key(tmp[1]):
				gene_b = mapping[tmp[1]]

			if gene_a != None and gene_b != None:
				#print 'writing %s\t%s\t1' % (gene_a, gene_b)
				outfile.write(gene_a + '\t' + gene_b + '\t1\n')
				outfile.flush()
				os.fsync(outfile)

		outfile.close()

if __name__ == '__main__':
	main(sys.argv[1:])
