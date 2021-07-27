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


'''
This file is used for pre-computed network cache, nor for gene prediction
'''

import sys, os, MySQLdb

DEBUG = 0
MIN_POS_SIZE = 3
MAX_POS_SIZE = 300
SEP_CHAR = '\t'

db = MySQLdb.connect(host="localhost", user="genemania", passwd="password", db="go200904")
#db = MySQLdb.connect(host="ensembldb.ensembl.org", user="anonymous", db="ensembl_go_54", port=5306)

def exec_query(sql):
	if DEBUG:
		print '============'
		print sql

	cursor = db.cursor()
	cursor.execute(sql)
	records = cursor.fetchall()
	cursor.close()

	if DEBUG:
		for record in records:
			print record

	return records


def get_db_info():
	sql = "select release_name, release_type, release_notes from instance_data"
	records = exec_query(sql)
	assert len(records) == 1 # surely never fails

	return records[0]
	
def get_direct_genes_for_terms(genus, species, term_accs):
	sql = """
	select distinct(gene_product.symbol) 
	from term, association, gene_product, evidence, species
	where term.is_root = 0
	and term.is_obsolete = 0
	and term.acc in %s
	and term.id = association.term_id
	and association.gene_product_id = gene_product.id
	and evidence.association_id = association.id
	and association.is_not != 1
	and evidence.code != 'IEA'
	and evidence.code != 'ND'
	and gene_product.species_id = species.id
	and species.genus = '%s' and species.species = '%s'
	;
	"""

	sql = sql % ("('" + "','".join(term_accs) + "')", genus, species)

	records = exec_query(sql)
	return set((record[0] for record in records))

def get_direct_genes_for_term(genus, species, term_acc):
	return get_direct_genes_for_terms(genus, species, [term_acc])


def get_all_genes_for_term(genus, species, term_acc):
	sql = """
	select distinct(gene_product.symbol) 
	from term as ancestor, term as descendant, graph_path, association, gene_product, evidence, species
	where graph_path.term1_id = ancestor.id
	and ancestor.is_root = 0
	and ancestor.is_obsolete = 0
	and ancestor.acc = '%s'
	and graph_path.term2_id = descendant.id
	and descendant.id = association.term_id
	and association.gene_product_id = gene_product.id
	and evidence.association_id = association.id
	and association.is_not != 1
	and evidence.code != 'IEA'
	and evidence.code != 'ND'
	and gene_product.species_id = species.id
	and species.genus = '%s' and species.species = '%s'
	order by ancestor.id, assocdate;
	"""

	sql = sql % (term_acc, genus, species)
	records = exec_query(sql)
	return set((record[0] for record in records))

def get_direct_iea_genes_for_term(genus, species, term_acc):
	sql = """
	select distinct(gene_product.symbol) 
	from term as ancestor, term as descendant, graph_path, association, gene_product, evidence, species
	where graph_path.term1_id = ancestor.id
	and ancestor.is_root = 0
	and ancestor.is_obsolete = 0
	and ancestor.acc = '%s'
	and graph_path.term2_id = descendant.id
	and graph_path.distance = 1
	and descendant.id = association.term_id
	and association.gene_product_id = gene_product.id
	and evidence.association_id = association.id
	and association.is_not != 1
	and evidence.code = 'IEA'
	and gene_product.species_id = species.id
	and species.genus = '%s' and species.species = '%s'
	order by ancestor.id, assocdate;
	"""

	sql = sql % (term_acc, genus, species)
	records = exec_query(sql)
	return set((record[0] for record in records))

def get_all_nd_iea_genes_for_term(genus, species, term_acc):
	sql = """
	select distinct(gene_product.symbol) 
	from term as ancestor, term as descendant, graph_path, association, gene_product, evidence, species
	where graph_path.term1_id = ancestor.id
	and ancestor.is_root = 0
	and ancestor.is_obsolete = 0
	and ancestor.acc = '%s'
	and graph_path.term2_id = descendant.id
	and descendant.id = association.term_id
	and association.gene_product_id = gene_product.id
	and evidence.association_id = association.id
	and association.is_not != 1
	and evidence.code in ('IEA', 'ND')
	and gene_product.species_id = species.id
	and species.genus = '%s' and species.species = '%s'
	order by ancestor.id, assocdate;
	"""

	sql = sql % (term_acc, genus, species)
	records = exec_query(sql)
	return set((record[0] for record in records))
	
def get_all_not_genes_for_term(genus, species, term_acc):
	sql = """
	select distinct(gene_product.symbol) 
	from term as ancestor, term as descendant, graph_path, association, gene_product, evidence, species
	where graph_path.term1_id = ancestor.id
	and ancestor.is_root = 0
	and ancestor.is_obsolete = 0
	and ancestor.acc = '%s'
	and graph_path.term2_id = descendant.id
	and descendant.id = association.term_id
	and association.gene_product_id = gene_product.id
	and evidence.association_id = association.id
	and association.is_not != 0
	and evidence.code != 'IEA'
	and evidence.code != 'ND'
	and gene_product.species_id = species.id
	and species.genus = '%s' and species.species = '%s'
	order by ancestor.id, assocdate;
	"""	

	sql = sql % (term_acc, genus, species)

	records = exec_query(sql)
	return set((record[0] for record in records))

def get_ancestor_terms(term_acc):
	'''
	return's accession ids. does not include the query term itself
	'''

	sql = """
	select ancestor.acc
	from term as ancestor, term as descendant, graph_path
	where descendant.acc = '%s'
	and descendant.id = graph_path.term2_id
	and ancestor.id = graph_path.term1_id
	and ancestor.is_root = 0
	and ancestor.is_obsolete = 0
	and ancestor.acc != descendant.acc
	;
	"""

	sql = sql % term_acc
	records = exec_query(sql)
	return set((record[0] for record in records))


def get_main_terms(term_acc):

	sql = """
	select ancestor.acc
	from term as ancestor, term as descendant, graph_path
	where descendant.acc = '%s'
	and descendant.id = graph_path.term2_id
	and ancestor.id = graph_path.term1_id
	and ancestor.is_root = 0
	and ancestor.is_obsolete = 0
	and ancestor.acc != descendant.acc
	;
	"""

	sql = sql % term_acc
	records = exec_query(sql)
	return set((record[0] for record in records))

def get_all_terms_for_organism(genus, species):
	'''all go terms that have at least one gene-product annotation
	for a given organism
	'''

	sql = """
	select distinct(term.acc) 
	from association, gene_product, species, term, evidence
	where association.gene_product_id = gene_product.id
	and gene_product.species_id = species.id
	and species.genus = '%s' 
	and species.species = '%s'
	and association.term_id = term.id
	and evidence.association_id = association.id
	and association.is_not != 1
	and evidence.code != 'IEA'
	and evidence.code != 'ND'
	and term.is_obsolete != 1;
	;
	"""

	sql = sql % (genus, species)
	records = exec_query(sql)
	return set((record[0] for record in records))

def get_all_terms_for_organism_from_term(genus, species, term_acc):
	'''all go terms that have at least one gene-product annotation
	for a given organism that are descended from the given base term
	'''

	sql = """

	select distinct(term.acc) 
	from association, gene_product, species, term, graph_path, term as base_term, evidence
	where association.gene_product_id = gene_product.id
	and gene_product.species_id = species.id
	and species.genus = '%s' 
	and species.species = '%s'
	and association.term_id = term.id
	and graph_path.term2_id = term.id
	and graph_path.term1_id = base_term.id
	and base_term.acc = '%s'
	and evidence.association_id = association.id
	and association.is_not != 1
	and evidence.code != 'IEA'
	and evidence.code != 'ND'
	;
	"""

	sql = sql % (genus, species, term_acc)
	records = exec_query(sql)
	return set((record[0] for record in records))

def get_base_terms():
	'''returns a dict mapping go accession ids to names for the direct descendents
	of the root term ... this should be the bp, mf, cc terms.
	'''

	sql = """
	select child.acc, child.name from term as root, term as child, term2term
	where term2term.term1_id = root.id
	and term2term.term2_id = child.id
	and root.is_root = 1
	and root.is_obsolete = 0
	and child.is_obsolete != 1;
	"""

	records = exec_query(sql)

	# this will return a dict of acc:name pairs since
	# records has the form ((acc, name), (acc, name), ...)
	return dict(records)

def make_query(go_acc, pos, neg, neutral, noise):
	query = [go_acc, '+'] + list(pos) + ['-'] + list(neg) + ['%'] + list(neutral) + ['*'] + list(noise)
	query = SEP_CHAR.join(query)
	return query
	
def make_pos_query(go_acc, pos):
	query = [go_acc, '+'] + list(pos)
	query = SEP_CHAR.join(query)
	return query

def main():
	if len(sys.argv) > 1:
		genus = sys.argv[1]
		species = sys.argv[2]
		organismId = sys.argv[3]
	else:
		genus = 'saccharomyces'
		species = 'cerevisiae'
		organismId= 6
	output=open("\\GoCategories\\" + str(organismId) + ".txt")
	dbinfo = get_db_info()
	print "# go db: %s %s %s" % dbinfo
	print "# genus '%s' species '%s'" % (genus, species)
	
	base_accs = get_base_terms()
	assert len(base_accs) == 3

	# for each base term, load all genes annotated
	genes_for_bases = {}
	for acc in base_accs:
		name = base_accs[acc]
		genes = get_all_genes_for_term(genus, species, acc)
		genes_for_bases[acc] = genes
		print "# total genes annotated for this species in %s is %s" % (name, len(genes))

	# for each root term, load list of child terms with at least
	# one annotated gene product for the species of interest
	total_from_bases = 0
	terms_from_bases = {}
	for acc in base_accs:
		name = base_accs[acc]
		sub_terms = get_all_terms_for_organism_from_term(genus, species, acc)
		terms_from_bases[acc] = sub_terms
		total_from_bases += len(sub_terms)
		print "# total annotated terms for this species in %s is %s" % (name, len(sub_terms))
	
	# get all terms with annotations with our species of interest
	all_terms = get_all_terms_for_organism(genus, species)
	print "# total number of annotated terms for this species: ", len(all_terms)

	# sanity check
	if total_from_bases != len(all_terms):
		raise Exception("sum of annotated terms from base terms does not equal the number of annotated terms from root ... something wrong!")

	
	for base_acc in base_accs:
	
		base_name = base_accs[base_acc]
		sub_terms = terms_from_bases[base_acc]
		# pool = genes_for_bases[base_acc]

		print "# processing terms for %s" % base_name

		branch_pos = get_all_genes_for_term(genus, species, base_acc)

		print "# term: %s, positives: %s" % (base_acc, len(branch_pos))
		query = make_pos_query(base_acc, branch_pos)
		print query

		for term in sub_terms:
		
			positives = get_all_genes_for_term(genus, species, term)
			
			if len(positives) < MIN_POS_SIZE:
				# print "#  %d positives for %s, too few, skipping" % (len(positives), term)
				continue
			elif len(positives) > MAX_POS_SIZE:
				# print "#  %d positives for %s, too many, skipping" % (len(positives), term)
				continue			
				
			# ancestors = get_ancestor_terms(term)
			# direct_from_ancestors = get_direct_genes_for_terms(genus, species, ancestors)
			
			output.write("# term: %s, positives: %s" % (term, len(positives)) )

			query = make_pos_query(term, positives)
			output.write(query + "\n")

if __name__ == '__main__':
	main()

