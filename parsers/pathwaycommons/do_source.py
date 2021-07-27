#!/usr/bin/env python
import sys, os
import sqlite3, datetime, traceback
from check_mapping import CheckMapping

class PathwayCommonsSourceParser:
	def create_source_files(self):
		for i in self.to_write:
			filename = self.output_dir + "/" \
				+ self.organism_short + "/" + i[0] + ".txt"
			try:
				outf = open(filename, "a")
				outf.write(i[1])
				outf.close()
			except Exception, e:
				traceback.print_tb(None)


	def find_symbol(self, cpath_record):
		ret = None
		gene_symbol = 0 # index in query results
		uniprot_acc = 1 # index in query results
		entrez_gene = 2 # index in query results
		try:
			dbfile = self.build_dir + "/" + self.organism_short + "_nodes.db"
			conn = sqlite3.connect(dbfile)
			cursor = conn.cursor()
			cursor.execute("pragma synchronous = off")
			t = (cpath_record,)
			cursor.execute("select gene_symbol, uniprot_acc, entrez_gene " \
				"from nodes where cpath_record=?", t)
			results = cursor.fetchall()
			for row in results:
				if row[entrez_gene] not in self.INVALID_MAPPING:
					return row[entrez_gene]
				if row[uniprot_acc] not in self.INVALID_MAPPING:
					return row[uniprot_acc]
				if row[gene_symbol] not in self.INVALID_MAPPING:
					return row[gene_symbol]
		except Exception, e:
			traceback.print_tb(None)
		finally:
			conn.close()

		return ret


	def filter_source_records(self):
		print "filtering source records"
		check = CheckMapping(self.mappings_dir + "/" + self.mapping_file)
		try:
			dbfile = self.build_dir + "/" + self.organism_short + "_source_raw_records.db"
			conn = sqlite3.connect(dbfile)
			cursor = conn.cursor()
			cursor.execute("pragma synchronous = off")
			i = 0

			for i in range(self.total_records):
				t = (i,)
				cursor.execute("select interaction_data_source, " \
					"cpath_record_a, cpath_record_b, gene_symbol_a, " \
					"gene_symbol_b from raw where counter=?", t)
				results = cursor.fetchall()
				for row in results:
					#print "counter:", i
					#print "interaction_data_source:", row[0]
					#print "cpath_record_a:", row[1]
					#print "cpath_record_b:", row[2]
					#print "gene_symbol_a:", row[3]
					#print "gene_symbol_b:", row[4]
					#print "================================="
					(data_source, cpath_record_a, cpath_record_b, \
						gene_symbol_a, gene_symbol_b) = \
					(row[0], row[1], row[2], row[3], row[4])

					if gene_symbol_a == self.NOT_SPECIFIED:
						gene_symbol_a = self.find_symbol(cpath_record_a)

					if gene_symbol_b == self.NOT_SPECIFIED:
						gene_symbol_b = self.find_symbol(cpath_record_b)

					if not gene_symbol_a or not gene_symbol_b:
						# no point doing any further checks if either symbols 
						# are set to None. decrement interactions for 
						# this source
						continue

					# symbols have valid values, check if we have them in 
					# our nomapping list. if they're there, then they have 
					# no valid mappings and we can decrement 
					# interactions for this source
					if self.no_mapping.has_key(gene_symbol_a) or \
						self.no_mapping.has_key(gene_symbol_b):
						continue

					# create a string of the record to save to a file:
					# record: symbol_a symbol_b 1
					# inverse: symbol_b symbol_a 1
					record = "%s\t%s\t1\n" % (gene_symbol_a, gene_symbol_b)
					inv_record = "%s\t%s\t1\n" % (gene_symbol_b, gene_symbol_a)

					# we have a valid record, process it only if we 
					# haven't already
					#if record not in self.already_filtered and \
					#	inv_record not in self.already_filtered:

					if not self.already_filtered.has_key(record) \
						and not self.already_filtered.has_key(inv_record):

						#self.already_filtered.append(record)
						#self.already_filtered.append(inv_record)
						self.already_filtered[record] = 1
						self.already_filtered[inv_record] = 1

						# no mapping, decrement this source
						if not check.has_mapping(gene_symbol_a):
							self.no_mapping[gene_symbol_a] = 1
							continue

						# no mapping, decrement this source
						if not check.has_mapping(gene_symbol_b):
							self.no_mapping[gene_symbol_b] = 1
							continue

						# everything looks good, save the record to file
						#print "saving record:", record.strip()

						# TODO: this gets called repeatedly, see if we can 
						# force it to be called only once
						#self.create_source_files(data_source, record)
						self.to_write.append([data_source, record])
		except Exception, e:
			print e
		finally:
			conn.close()
				

	def count_source_records(self):
		try:
			print "counting source records"
			header_skipped = False
			counter = 0

			# create sqlite db to store raw records
			dbfile = self.build_dir + "/" + self.organism_short + "_source_raw_records.db"
			conn = sqlite3.connect(dbfile)
			sql = """
			drop table if exists raw; 
			create table raw (counter, interaction_data_source, \
				cpath_record_a, cpath_record_b, gene_symbol_a, gene_symbol_b);
			create index ix_raw_counter on raw (counter); 
			"""
			conn.executescript(sql)

			records = []
			for line in open(self.edges_file):
				if len(line.strip()) < 1:
					continue
				if not header_skipped:
					header_skipped = True
					continue

				tokens = line.split("\t")
				if len(tokens) > 0:
					records.append([counter, tokens[-2], tokens[0], 
						tokens[2], tokens[3], tokens[4]])

					counter += 1
			conn.executemany("insert into raw " \
				+ "(counter, interaction_data_source, " \
				+ "cpath_record_a, cpath_record_b, " \
				+ "gene_symbol_a, gene_symbol_b) " \
				+ "values (?,?,?,?,?,?);", records)
			conn.commit()
			self.total_records = counter
		except Exception, e:
			traceback.print_tb(None)
		finally:
			conn.close()
			print "created raw db", dbfile
			print "total records:", self.total_records


	def create_nodes_db(self):
		print "create nodes db"
		try:
			# create a slimmed down version of the node file containing only 4
			# columns: cpath_record, gene_symbol, uniprot_acc, and entrez_gene
			# save it to a file that will be processed to a sqlite db
			outf = open(self.build_dir + "/" + self.organism_short + "_nodes.txt", "w")
			header_skipped = False
			for line in open(self.nodes_file):
				if not header_skipped:
					header_skipped = True
					continue
				tokens = line.split("\t")
				cpath_record = tokens[0]
				gene_symbol = tokens[1]
				uniprot_acc = tokens[2]
				entrez_gene = tokens[-3]
				#print "cpath record:", cpath_record
				#print "gene symbol:", gene_symbol
				#print "uniprot acc:", uniprot_acc
				#print "entrez gene:", entrez_gene
				#print "-------------------------"
				outf.write(cpath_record + "\t" + gene_symbol + "\t" \
					+ uniprot_acc + "\t" + entrez_gene + "\n")
		except Exception, e:
			traceback.print_tb(None)
		finally:
			outf.close()

		# create sqlite db out of the slimmed nodes file
		dbfile = self.build_dir + "/" + self.organism_short + "_nodes.db"
		conn = sqlite3.connect(dbfile)

		try:
			sql = """
			drop table if exists nodes; 
			create table nodes (cpath_record,gene_symbol,uniprot_acc,entrez_gene);
			create index ix_nodes_cpath_record on nodes (cpath_record); 
			"""
			conn.executescript(sql)

			records = []
			for line in open(self.build_dir + "/" + self.organism_short + "_nodes.txt"):
				line = line.strip()
				tokens = line.split("\t")
				records.append(tokens)

			# batch insert
			conn.executemany("insert into nodes " \
				+ "(cpath_record,gene_symbol,uniprot_acc,entrez_gene) " \
				+ "values (?,?,?,?);", records)
			conn.commit()

		except Exception, e:
			traceback.print_tb(None)
		finally:
			conn.close()
			print "created nodes db", dbfile


	def __init__(self, edges_file, nodes_file, output_dir, mappings_dir, build_dir):
		# if the gene symbol is mapped to one of these, set it to None 
		self.INVALID_MAPPING = ["NOT_SPECIFIED", "protein"]
		self.INTERACTION_DATA_SOURCE = "INTERACTION_DATA_SOURCE"
		self.CPATH_RECORD_ID_A = "CPATH_RECORD_ID_A"
		self.CPATH_RECORD_ID_B = "CPATH_RECORD_ID_B"
		self.GENE_SYMBOL_A = "GENE_SYMBOL_A"
		self.GENE_SYMBOL_B = "GENE_SYMBOL_B"
		self.INTERACTION_DATA_SOURCE = "INTERACTION_DATA_SOURCE"
		self.NOT_SPECIFIED = "NOT_SPECIFIED"

		self.THRESHOLD = 100
		self.UNDER_THRESHOLD_FILE = "under-threshold.txt"
		self.source_raw_records = {}
		self.source_count = {}
		self.no_mapping = {}
		#self.already_filtered = []
		self.already_filtered = {}

		self.edges_file = edges_file
		self.nodes_file = nodes_file
		self.output_dir = output_dir
		self.mappings_dir = mappings_dir
		self.build_dir = build_dir

		self.total_records = 0
		self.to_write = []

		print "edges file:", self.edges_file
		print "nodes file:", self.nodes_file
		print "output dir:", self.output_dir
		print "mappings dir:", self.mappings_dir

		# get organism name from the file
		self.organism = \
			(self.edges_file.split("-")[0] + "-" + \
			self.edges_file.split("-")[1]) \
			.split("/")[-1]
		print "organism:", self.organism

		# get organism short code so we know which mapping file to use
		self.organism_short = \
			self.organism.split("-")[0][0].upper() + \
			self.organism.split("-")[1][0]
		print "organism short:", self.organism_short

		self.mapping_file = self.organism_short + ".db"
		print "mapping file:", self.mapping_file

		self.organism_outdir = self.output_dir + "/" + self.organism_short + "/"
		print "organism out dir:", self.organism_outdir
		try:
			os.makedirs(self.organism_outdir)
		except Exception, e:
			traceback.print_tb(None)


if __name__ == "__main__":
	pcp = PathwayCommonsSourceParser(
		sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
	print "---[processing source files]---"

	s = datetime.datetime.now()
	pcp.create_nodes_db()
	d = datetime.datetime.now() - s
	print "time taken for create_nodes_db: s: %d ms: %d" % (d.seconds, d.microseconds)

	s = datetime.datetime.now()
	pcp.count_source_records()
	d = datetime.datetime.now() - s
	print "time taken for count_source_records: s: %d ms: %d" % (d.seconds, d.microseconds)

	s = datetime.datetime.now()
	pcp.filter_source_records()
	d = datetime.datetime.now() - s
	print "time taken for filter_source_records: s: %d ms: %d" % (d.seconds, d.microseconds)

	s = datetime.datetime.now()
	pcp.create_source_files()
	d = datetime.datetime.now() - s
	print "time taken for create_source_files: s: %d ms: %d" % (d.seconds, d.microseconds)
