#!/usr/bin/env python

'''
Parse the contents of the file and create an output file containing:
GENE_A     GENE_B     1

If GENE_SYMBOL_A is missing from the edges file, look it up in the nodes file using 
CPATH_RECORD_ID_A as the key. Same thing for GENE_SYMBOL_B => CPATH_RECORD_ID_B. We're 
interested in the UNIPROT_ACCESSION and ENTREZ_GENE_ID from the nodes file.
'''

import sys
from check_mapping import CheckMapping
import os
from time import strftime
from datetime import datetime


THRESHOLD = 100
UNDER_THRESHOLD_FILE = 'under-threshold.txt'

# columns in the node file. 
GENE_SYMBOL = 'GENE_SYMBOL'
ENTREZ_GENE_ID = 'ENTREZ_GENE_ID'
UNIPROT_ACCESSION = 'UNIPROT_ACCESSION'

# columns in the edge file.
CPATH_RECORD_ID_A = 'CPATH_RECORD_ID_A'
CPATH_RECORD_ID_B = 'CPATH_RECORD_ID_B'
GENE_SYMBOL_A = 'GENE_SYMBOL_A'
GENE_SYMBOL_B = 'GENE_SYMBOL_B'
INTERACTION_PUBMED_ID = 'INTERACTION_PUBMED_ID'
INTERACTION_DATA_SOURCE = 'INTERACTION_DATA_SOURCE'

NOT_SPECIFIED = 'NOT_SPECIFIED'
RECORD = 'RECORD'

COUNT = 'COUNT'
TYPE_PUBMED = 'pubmed'
TYPE_SOURCE = 'source'


nodeMap = {} # contains the cpath record and gene symbol records
pubmedRaw = {} # columns we need from the edge file
pubmedSummary = {} # contains the number of times a pubmed ID appears
sourceRaw = {} # columns we need from the edge file
sourceSummary = {} # contains the number of times a data source ID appears
nomapping = {} # used to keep track of gene mappings we don't have
alreadyRecorded = [] # used to filter out duplicates
alreadyFiltered = [] # used to filter out duplicates
type = ''


'''
Look for the gene symbol in the node file that corresponds with the 
CPATH_RECORD_ID in the edge file. Return 3 possible values, in the 
order of preference: ENTREZ_GENE_ID, UNIPROT_ACCESSION, and GENE_SYMBOL. 
'''
def findSymbol(cpathRecord):
	retSymbol = None
	if nodeMap.has_key(cpathRecord):
		if nodeMap[cpathRecord][ENTREZ_GENE_ID] != NOT_SPECIFIED:
			retSymbol = nodeMap[cpathRecord][ENTREZ_GENE_ID]

		elif nodeMap[cpathRecord][UNIPROT_ACCESSION] != NOT_SPECIFIED:
			retSymbol = nodeMap[cpathRecord][UNIPROT_ACCESSION]

		elif nodeMap[cpathRecord][GENE_SYMBOL] != NOT_SPECIFIED:
			retSymbol = nodeMap[cpathRecord][GENE_SYMBOL]
	else:
		print '\t\t[ERROR] nodeMap has no key', cpathRecord

	if retSymbol == "protein":
		retSymbol = None
	return retSymbol

'''
Go through each source record and determine whether it should be 
written to the UNDER_THRESHOLD_FILE or a source file.
'''
def analyzeSource(outPath): 
	for key in sourceRaw:
		dataSource = sourceRaw[key][INTERACTION_DATA_SOURCE]
		record = sourceRaw[key][RECORD]

		filename = ''.join([outPath, dataSource, '.txt'])
		try:
			outFile = open(filename, 'a')
			outFile.write(record)
			outFile.close()
		except IOError, e:
			print e


'''
Go through each pubmed record and determine whether it should be 
written to the UNDER_THRESHOLD_FILE or a pubmed ID file.
'''
def analyzePubmed(outPath):
	for key in pubmedRaw:
		pubmedId = pubmedRaw[key][INTERACTION_PUBMED_ID]
		record = pubmedRaw[key][RECORD]
		filename = ''

		if pubmedSummary[pubmedId][COUNT] > THRESHOLD:
			filename = ''.join([outPath, pubmedId, '.txt'])
		else:
			filename = ''.join([outPath, UNDER_THRESHOLD_FILE])

		try:
			outFile = open(filename, 'a')
			outFile.write(record)
			outFile.close()
		except IOError, e:
			print e


'''
For source records. 
Search for missing gene symbol A/B. Save the record only if it hasn't 
been saved before and if both gene symbol A/B were found.
'''
def filterSource(mappingsdb):
	check = CheckMapping(mappingsdb)
	for key in sourceRaw:
		dataSource = sourceRaw[key][INTERACTION_DATA_SOURCE]

		cpathRecordA = sourceRaw[key][CPATH_RECORD_ID_A]
		cpathRecordB = sourceRaw[key][CPATH_RECORD_ID_B]
		geneSymbolA = sourceRaw[key][GENE_SYMBOL_A]
		geneSymbolB = sourceRaw[key][GENE_SYMBOL_B]

		if geneSymbolA == NOT_SPECIFIED:
			geneSymbolA = findSymbol(cpathRecordA)

		if geneSymbolB == NOT_SPECIFIED:
			geneSymbolB = findSymbol(cpathRecordB)

		record = '%s\t%s\t1\n' % (geneSymbolA, geneSymbolB)
		inv_record = '%s\t%s\t1\n' % (geneSymbolB, geneSymbolA)

		# don't write duplicates to the output file.
		if record not in alreadyFiltered and inv_record not in alreadyFiltered:
			# append record and inverse record to filtered list
			alreadyFiltered.append(record)
			alreadyFiltered.append(inv_record)

			checkA = geneSymbolA
			checkB = geneSymbolB

			# have we already determined that this gene symbol has no
			# mapping?
			if nomapping.has_key(geneSymbolA):
				geneSymbolA = None
			if nomapping.has_key(geneSymbolB):
				geneSymbolB = None

			# gene symbol not yet checked against mappings
			if not check.has_mapping(checkA):
				nomapping[checkA] = 1
				geneSymbolA = None

			if not check.has_mapping(checkB):
				nomapping[checkB] = 1
				geneSymbolB = None

			if not geneSymbolA or not geneSymbolB:
				sourceSummary[dataSource][COUNT] -= 1
			else:
				sourceRaw[key][RECORD] = record
		else:
			sourceSummary[dataSource][COUNT] -= 1


'''
For pubmed records.
Search for missing gene symbol A/B. Save the record only if it hasn't 
been saved before and if both gene symbol A/B were found.
'''
def filterPubmed(mappingsdb):
	check = CheckMapping(mappingsdb)
	for key in pubmedRaw:
		pubmedId = pubmedRaw[key][INTERACTION_PUBMED_ID]

		cpathRecordA = pubmedRaw[key][CPATH_RECORD_ID_A]
		cpathRecordB = pubmedRaw[key][CPATH_RECORD_ID_B]
		geneSymbolA = pubmedRaw[key][GENE_SYMBOL_A]
		geneSymbolB = pubmedRaw[key][GENE_SYMBOL_B]

		if geneSymbolA == NOT_SPECIFIED:
			geneSymbolA = findSymbol(cpathRecordA)

		if geneSymbolB == NOT_SPECIFIED:
			geneSymbolB = findSymbol(cpathRecordB)

		record = '%s\t%s\t1\n' % (geneSymbolA, geneSymbolB)
		inv_record = '%s\t%s\t1\n' % (geneSymbolB, geneSymbolA)

		# don't write duplicates to the output file.
		if record not in alreadyFiltered and inv_record not in alreadyFiltered:
			# append record and inverse record to filtered list
			alreadyFiltered.append(record)
			alreadyFiltered.append(inv_record)

			checkA = geneSymbolA
			checkB = geneSymbolB

			# have we already determined that this gene symbol has no
			# mapping?
			if nomapping.has_key(geneSymbolA):
				geneSymbolA = None
			if nomapping.has_key(geneSymbolB):
				geneSymbolB = None

			# gene symbol not yet checked against mappings
			if not check.has_mapping(checkA):
				nomapping[checkA] = 1
				geneSymbolA = None
			if not check.has_mapping(checkB):
				nomapping[checkB] = 1
				geneSymbolB = None

			# mapping succeeded
			if not geneSymbolA or not geneSymbolB:
				pubmedSummary[pubmedId][COUNT] -= 1
			else:
				pubmedRaw[key][RECORD] = record
		else:
			pubmedSummary[pubmedId][COUNT] -= 1


'''
Record and count the number of data source records in the file. 
'''
def countSourceRecords(edgeFile): 
	try:
		inFile = open(edgeFile, 'r')
		firstLine = True

		counter = 0
		for line in inFile:
			if len(line.strip()) < 1:
				continue
	
			if firstLine:
				firstLine = False
				continue
	
			tokens = line.split('\t')

			if len(tokens) > 0:
				dataSource = tokens[-2]
				cpathRecordA = tokens[0]
				cpathRecordB = tokens[2]
				geneSymbolA = tokens[3]
				geneSymbolB = tokens[4]

				# record the raw record using counter as the unique key. This is necessary because there could be
				# more than one data source ID with different values in the other columns.
				sourceRaw[counter] = {
					INTERACTION_DATA_SOURCE: dataSource, 
					CPATH_RECORD_ID_A: cpathRecordA, 
					CPATH_RECORD_ID_B: cpathRecordB, 
					GENE_SYMBOL_A: geneSymbolA, 
					GENE_SYMBOL_B: geneSymbolB, 
					RECORD: ''}
				counter += 1

				# record the total number of times a data source ID appears in the file. This is used to determine
				# whether the data source is above the threshold. 
				if sourceSummary.has_key(dataSource):
					sourceSummary[dataSource][COUNT] += 1
				else:
					sourceSummary[dataSource] = {COUNT: 1}

		inFile.close()
	except IOError, e:
		print e


'''
Record and count the number of pubmed ID records in the file. 
'''
def countPubmedRecords(edgeFile):
	try:
		inFile = open(edgeFile, 'r')
		firstLine = True

		counter = 0
		for line in inFile:
			if len(line.strip()) < 1:
				continue
	
			if firstLine:
				firstLine = False
				continue
	
			tokens = line.split('\t')
	
			if len(tokens) > 0:
				cpathRecordA = tokens[0]
				cpathRecordB = tokens[2]
				geneSymbolA = tokens[3]
				geneSymbolB = tokens[4]

				# there could be more than one pubmed ID, each separated by a 
				# semi-colon. Split that up into a separate list for processing.
				idList = tokens[-1].split(';')
				for pubmedId in idList:
					if pubmedId != '':
						currId = pubmedId[pubmedId.find(':') + 1:]

						if len(currId) > 0 and currId.isdigit():
							# record the raw record using counter as the unique key. This is necessary because there could be
							# more than one pubmed ID with different values in the other columns.
							pubmedRaw[counter] = {
								INTERACTION_PUBMED_ID: currId, 
								CPATH_RECORD_ID_A: cpathRecordA, 
								CPATH_RECORD_ID_B: cpathRecordB, 
								GENE_SYMBOL_A: geneSymbolA, 
								GENE_SYMBOL_B: geneSymbolB, 
								RECORD: ''}
							counter += 1

							# record the total number of times a pubmed ID appears in the file. This is used to determine
							# whether the pubmed is above the threshold. 
							if pubmedSummary.has_key(currId):
								pubmedSummary[currId][COUNT] += 1
							else:
								pubmedSummary[currId] = {COUNT: 1}
		inFile.close()
	except IOError, e:
		print e


'''
Load the contents of the node file into nodeMap, using the CPATH_RECORD_ID as the 
key and a nested dict to contain GENE_SYMBOL, UNIPROT_ACCESSION and ENTREZ_GENE_ID.
'''
def loadNodeFile(nodeFile):
	inFile = open(nodeFile, 'r')

	for line in inFile:
		tokens = line.split('\t')
		cpathRecordId = tokens[0]
		nodeMap[cpathRecordId] = { GENE_SYMBOL: tokens[1], UNIPROT_ACCESSION: tokens[2], ENTREZ_GENE_ID: tokens[-3] }

	inFile.close()


def main(argv = sys.argv):
	if len(argv) < 5:
		print 'Usage: %s [pubmed|source] edges_dir nodes_dir output_dir mappings.db' % (argv[0])
		print 'Files to be processed should end with .txt'
		sys.exit(0)

	try:
		global type
		type = argv[1]

		edgeFile = argv[2]
		nodeFile = argv[3]
		outPath = ''.join([argv[4], '/'])

		# determine what the organism is based on the filename.
		organism = ''.join([edgeFile.split('-')[0],  '-', edgeFile.split('-')[1]])
		organism = organism.split('/')[-1]

		tmp = organism.split('-')
		if tmp[1] == 'edge':
			organism = tmp[0]

		# get the organism short code so we can determine which mapping file to use
		# eg: homo-sapiens -> Hs means use Hs.db
		organism_short = organism.split('-')[0][0].upper() + organism.split('-')[1][0]
		mappingsdb = ''.join([argv[5], '/', organism_short, '.db'])

		currOutPath = ''.join([outPath, organism, '/'])

		if not os.path.exists(currOutPath):
			os.mkdir(currOutPath)

		print 'Edge file:', edgeFile
		print 'Node file:', nodeFile
		print 'Out path:', currOutPath
		print 'Organism:', organism
		print 'Threshold:', THRESHOLD
		print 'Mapping file:', mappingsdb

		loadNodeFile(nodeFile)
		if type.lower() == TYPE_PUBMED:
			print 'Counting Pubmed records...'
			countPubmedRecords(edgeFile)
			#print "pubmedRaw len:", len(pubmedRaw)
			#print "pubmedSummary len:", len(pubmedSummary)
			#sys.exit(0)

			print 'Filtering invalid records...'
			filterPubmed(mappingsdb)

			print 'Analyzing Pubmed records...'
			analyzePubmed(currOutPath)

		elif type.lower() == TYPE_SOURCE:
			print 'Counting source records...'
			countSourceRecords(edgeFile)

			print 'Filtering invalid records...'
			filterSource(mappingsdb)

			print 'Analyzing source records...'
			analyzeSource(currOutPath)
		else:
			print '[ERROR] unknown type:', type
			sys.exit(0)

		print 'Script completed'
	except OSError, e:
		print e


if __name__ == '__main__':
	sys.exit(main())
