#! /usr/bin/python
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

#
# for each organism, extract functional annotations from the Gene Ontology
#
# outputs are:
#  * db/GoCategories/ID.annos.txt
#
# a text file where ID is the genemania organism id, with columns
#
#    ancestor_name, ancestor_term_type, ancestor_acc,
#    descendent_name, descendent_type, descendent_acc,
#    gene_product_symbol,
#    xref_dbname, xref_key,
#    evidence_code,
#    graph_path_distance
#
# input is a mysql database instance of the GO assoc-db.
#
# see this reference on how to write sql queries to the GO db
#   http://wiki.geneontology.org/index.php/Example_Queries

import sys, datalib, os

try:
    import MySQLdb
except  ImportError:
    import pymysql as MySQLdb

DEBUG = 0
SEP_CHAR = '\t'

#db = MySQLdb.connect(host="ensembldb.ensembl.org", user="anonymous", db="ensembl_go_54", port=5306)

def exec_query(sql,db):
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


def get_db_info(db):
    sql = "select release_name, release_type, release_notes from instance_data"
    records = exec_query(sql,db)
    assert len(records) == 1 # surely never fails

    return records[0]
    
def get_all_annotations(db, ncbi_taxa_id, ignore_evidence_codes):

    sql = """
    select
    ancestor_term.name as ancestor_name, ancestor_term.term_type as ancestor_term_type, ancestor_term.acc as ancestor_acc,
    descendent_term.name as descendent_name, descendent_term.term_type as descendent_type, descendent_term.acc as descendent_acc,
    gene_product.symbol,
    dbxref.xref_dbname, dbxref.xref_key,
    evidence.code,
    graph_path.distance
    from association, term as ancestor_term, term as descendent_term, gene_product, species, evidence, graph_path, dbxref
    where species.ncbi_taxa_id = %s
    and species.id = gene_product.species_id
    and association.gene_product_id = gene_product.id
    and ancestor_term.id = graph_path.term1_id
    and descendent_term.id = graph_path.term2_id
    and evidence.association_id = association.id
    %s
    and association.term_id = descendent_term.id
    and gene_product.dbxref_id = dbxref.id
    and association.is_not = 0
    and descendent_term.is_obsolete = 0;
    """

    ignoring_clause = "and evidence.code not in (%s)"
    if ignore_evidence_codes:
        ignoring = ",".join("'%s'" % code for code in ignore_evidence_codes)
        ignoring = ignoring_clause % ignoring
    else:
        ignoring = ''

    sql = sql % (ncbi_taxa_id, ignoring)

    records = exec_query(sql, db)
    return records

def main(config):
    '''loop over all the organisms in the given master config
    and extract some per-organism data'''
    db = MySQLdb.connect(host=config['GoDatabase']['host'], user=config['GoDatabase']['user'],
        passwd=config['GoDatabase']['password'], db=config['GoDatabase']['db'])
    organisms = config['Organisms']['organisms']

    # can extract other config params here, eg:
    # dbname = datalib.get_location(config, 'geo_metadb_name')

    anno_dir = datalib.get_location(config, 'annotations_dir')

    if os.access(anno_dir,os.F_OK)== False:
        os.mkdir(anno_dir)
    if os.access(anno_dir,os.W_OK)== False:
        raise Exception("can not write to folder")
    
    for organism in organisms:
        id = config[organism]['gm_organism_id']
        organism_name = config[organism]['name']
        genus, species = organism_name.split(' ')
        ncbi_taxa_id = config[organism]['ncbi_taxonomy_id']

        organismId=id

        print "processing", organism_name
        records = get_all_annotations(db, ncbi_taxa_id, ('IEA', 'ND', 'RCA'))

        out_fn = "%s.annos.txt" % organismId
        out_fn = os.path.join(anno_dir, out_fn)
        print "writing %s" % out_fn
        output=open(out_fn, "w")
        dbinfo = get_db_info(db)
        output.write("# go db: %s %s %s" % dbinfo + "\n")
        output.write("# genus '%s' species '%s' taxonomy id %s" % (genus, species, ncbi_taxa_id) + "\n")

        for record in records:
            line = '\t'.join(str(field) for field in record) + '\n'
            output.write(line)

        output.close()
        
    print "done"
    
if __name__ == "__main__":
    '''first arg is the master config file'''

    config_file = sys.argv[1]

    # load config and run
    config = datalib.load_main_config(config_file)
   
    
    main(config)