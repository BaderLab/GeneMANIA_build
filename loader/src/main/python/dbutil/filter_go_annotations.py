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
# for each organism, filter go annotations from flat file 
# to produce files containing annotation data for both
# go based combining methods and enrichment analysis
#
# input file is produced by the script query_go_annotions.py,
# db/GoCategories/ID.annos.txt
# 
# outputs are:
#  * db/GoCategories/ID_BP.txt: category/gene pairs
#  * db/GoCategories/ID_MF.txt
#  * db/GoCategories/ID_CC.txt
#  * db/ontologies/processed/ID.annos-filtered.txt:list of categories 
#
# a mappings file must exist in db/mappings/processed/CODE_names.txt,
# and is used to clean/dedup the annotations. Size limit constraints
# on the go categories are applied. 
#
# evidence_code filtering is not applied here, and is assumed to have
# been already applied to the annotations input file

import sys, datalib, os
import pandas as pd

SEP_CHAR = '\t'

# these can be overridden by per-organism size ranges
# specified in the master config file
DEFAULT_ENRICHMENT_MIN_NUM_ANNOS = 10
DEFAULT_ENRICHMENT_MAX_NUM_ANNOS = 300

COMBINING_MIN_NUM_ANNOS = 3
COMBINING_MAX_NUM_ANNOS = 300

def main(config):
    organisms = config['Organisms']['organisms']

    processed_mapping_dir = datalib.get_location(config, 'processed_mappings_dir')
    anno_dir = datalib.get_location(config, 'annotations_dir')
    
    for organism in organisms:
        organismId = config[organism]['gm_organism_id']
        organism_name = config[organism]['name']
        short_id = config[organism]['short_id']
        try:
            enrichment_min_num_annos, enrichment_max_num_annos = config[organism]['ontology_size_limits']
            enrichment_min_num_annos, enrichment_max_num_annos = int(enrichment_min_num_annos), int(enrichment_max_num_annos)
        except:
            enrichment_min_num_annos, enrichment_max_num_annos = DEFAULT_ENRICHMENT_MIN_NUM_ANNOS, DEFAULT_ENRICHMENT_MAX_NUM_ANNOS  

        print "processing", organism_name

        # load identifiers & uppercase so comparisons don't depend on case
        mapping_file = "%s_names.txt" % short_id
        mapping_file = os.path.join(processed_mapping_dir, mapping_file)
        print "loading %s" % mapping_file
        mappings = pd.read_table(mapping_file, sep=SEP_CHAR, header=None, na_filter=False, names=['id', 'symbol', 'source'])
        mappings['symbol'] = mappings['symbol'].str.upper()
        
        # load annotations & uppercase gene symbol, keep a copy of the original case for writing
        annotations_file = "%s.annos.txt" % organismId
        annotations_file = os.path.join(anno_dir, annotations_file)        
        print "loading %s" % annotations_file        
        annos = pd.read_table(annotations_file, sep=SEP_CHAR, skiprows=8, header=None, na_filter=False,  
                              names=['name', 'branch', 'category', 'd', 'e', 'f', 'gene', 'h', 'i', 'k', 'l'])
        annos['gene_orig'] = annos['gene']
        annos['gene'] = annos['gene'].str.upper()
        
        # drop rows that don't belong to one of 3 main go branches (universal/root level annotations)
        # TODO

        # merge annotations with mappings, excluding entries that don't match up
        clean = pd.merge(annos, mappings, left_on = 'gene', right_on = 'symbol', how='inner')
        # get rid of duplicates
        clean.drop_duplicates(['category', 'id'], inplace=True)          
        # group by category
        grouped = clean.groupby("category")
        # count number of unique genes in each group
        counts = grouped['id'].nunique()
        counts.name = 'size'

        # determine categories for enrichment, and write to file of filtered annos
        wanted = counts[(counts >= enrichment_min_num_annos) & (counts <= enrichment_max_num_annos)]
        wanted = wanted.reset_index() # push category into a column
        
        all_names = annos.drop_duplicates(['name', 'category']);
        all_names = all_names.ix[:, ('name', 'category')]
        out = pd.merge(all_names, wanted, left_on = 'category', right_on = 'category', how='inner')
        out = out.ix[:, ('category', 'name')]
        #sort is deprecated.  Updated to use sort_values
        out.sort_values(by = 'category', inplace=True)
        
        masterConfig = datalib.MasterConfig(config.filename)
        processed_ontologies_dir = masterConfig.getProcessedOntologiesDir()
        if not os.path.exists(processed_ontologies_dir):
            os.makedirs(processed_ontologies_dir)
        
        filtered_filename = "%s.annos-filtered.txt" % (organismId)
        filtered_filename = os.path.join(processed_ontologies_dir, filtered_filename)  
        print "writing %s" % filtered_filename      
        
        out.to_csv(filtered_filename, sep=SEP_CHAR, index=False, header=False)

        # now write out annotations split out for go-based combining methods, filtered by 
        # possible different size constraints
        wanted = counts[(counts >= COMBINING_MIN_NUM_ANNOS) & (counts <= COMBINING_MAX_NUM_ANNOS)]
        wanted = wanted.reset_index() # push category into a column
        
        out = clean_for_branch(clean, wanted, "biological_process")
        branch_filename = os.path.join(anno_dir, "%s_BP.txt" % organismId)
        print "writing %s" % branch_filename
        out.to_csv(branch_filename, sep=SEP_CHAR, index=False, header=False)

        out = clean_for_branch(clean, wanted, "molecular_function")
        branch_filename = os.path.join(anno_dir, "%s_MF.txt" % organismId)
        print "writing %s" % branch_filename
        out.to_csv(branch_filename, sep=SEP_CHAR, index=False, header=False)
        
        out = clean_for_branch(clean, wanted, "cellular_component")
        branch_filename = os.path.join(anno_dir, "%s_CC.txt" % organismId)
        print "writing %s" % branch_filename
        out.to_csv(branch_filename, sep=SEP_CHAR, index=False, header=False)
        
        print "done"        
        
def clean_for_branch(clean, wanted, branch_name):
    
        # subset annotations extracting branch of interest
        branch = clean[clean['branch'] == branch_name]
        
        # only want annotations from among these that were
        # selected also satisfied size constraints
        out = pd.merge(branch, wanted, left_on = 'category', right_on = 'category', how='inner')
        out = out.ix[:, ('category', 'gene_orig')]
        #sort is deprecated.  update to sort_values
        out.sort_values(by=['category', 'gene_orig'], inplace=True)
        
        return out

if __name__ == "__main__":
    '''first arg is the master config file'''

    config_file = sys.argv[1]

    # load config and run
    config = datalib.load_main_config(config_file)    
    main(config)
