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
#    graph_path_distance - distance between the ancestor and descendant term
#
# builds the same file but uses python library goatools (goatools.org)
#

import sys, datalib, os

from goatools.base import get_godag
from goatools.obo_parser import GODag
from goatools.associations import read_gaf, get_gaf_hdr
from goatools.anno.gaf_reader import GafReader
from goatools.semantic import semantic_distance
import wget, datalib

DEBUG = 0
SEP_CHAR = '\t'
    
def main(config):
    
    #get the resource dir
    go_resource_dir = os.path.join(config['BuildScriptsConfig']['resource_dir'] ,"go")
    
    '''loop over all the organisms in the given master config
    and extract some per-organism data'''
    organisms = config['Organisms']['organisms']

    url = "http://current.geneontology.org/annotations/"
    
    anno_dir = datalib.get_location(config, 'annotations_dir')

    if os.access(anno_dir,os.F_OK)== False:
        os.mkdir(anno_dir)
    if os.access(anno_dir,os.W_OK)== False:
        raise Exception("can not write to folder")
    
    #get the GO Hierarchy
    go_fn = wget.download('http://geneontology.org/ontology/go-basic.obo', out =go_resource_dir )
    go = GODag(go_fn, optional_attrs=['relationship'])
   
    for organism in organisms:
        id = config[organism]['gm_organism_id']
        organism_name = config[organism]['name']
        genus, species = organism_name.split(' ')
        ncbi_taxa_id = config[organism]['ncbi_taxonomy_id']

        organismId=id
        
        gaf_filename = config[organism]['go_species_filename'] + ".gaf.gz"

        gaf_zipped = wget.download(url+gaf_filename, out = go_resource_dir)

        #unzip the gaf file
        gaf_current = datalib.gunzip(os.path.join(go_resource_dir,gaf_filename))

        #get the GO gaf file - 
        #create a gaf reader object
        gafreader = GafReader(gaf_current,prt=sys.stdout)
        #id2gos = gafreader.read_gaf()  # Read associations
        associations = gafreader.associations
        print "number of associations {R}".format(R=len(associations))

        #read the gaf file and get all the mappings from goids to genes. 
        # only use the goids that genes associated with them
        go2ids = read_gaf(gaf_current, go2geneids=True)
        goids_with_annots = set(go2ids.keys())
        print "There are {R} go terms in the ontology but only {S} go terms with annotations".format(R=len(go),S=len(goids_with_annots))
        print "processing", organism_name

        out_fn = "%s.annos.txt" % organismId
        out_fn = os.path.join(anno_dir, out_fn)
        print "writing %s" % out_fn
        output=open(out_fn, "w")
        gafheader = get_gaf_hdr(gaf_current)
        output.write("#Header from {GAF}: {HDR}\n".format(GAF=gaf_current, HDR=gafheader.replace('\n','\n#')))
        output.write("# genus '%s' species '%s' taxonomy id %s" % (genus, species, ncbi_taxa_id) + "\n")
        
        #go though all the annotations and format results to genemania format
        for ntgaf in associations:
            
            #if this association has one of the below evidence codes, skip it
            if ntgaf.Evidence_Code in ("IEA","ND","RCA"):
                continue

            #get the go info
            current_term = go[ntgaf.GO_ID]
            #get the current depth of the given term - used to figure out the graph_path which was in the db but is not in obo or gaf files
            current_depth = current_term.depth

            #looked through the code to figure out the name of the attributes in the returned object.  We need to go through each parent (and then add the parents of each parent until the list is empty)
            #parents is a set
            #parents = current_term.parents.copy()
            
            #changed method that we get parents as goatools was only following is_a.  By using their method
            # get_all_upper all relationships are followed.  ***This might add extra connections ***
            # unfortunately I can't see a way to just add part_of but there is a bug reported entered in their
            # github discussing the issue. - Might have to revisit
            # https://github.com/tanghaibao/goatools/issues/92
            parents = current_term.get_all_upper()
            
            #only include parents that are terms that have annotations associated with them
            parents.intersection(goids_with_annots)
            
            #go thruogh each parent
              # output row with current parent
            while True:

                #check to see if parents are empty.  They shouldn't be but we need to record them.  Check for errors
                if len(parents) == 0:
                    #print current_term, "\n"
                    print "no_parent","no parent", "no parents",current_term.id, current_term.name, current_term.namespace ,ntgaf.DB, ntgaf.DB_ID, ntgaf.DB_Symbol,ntgaf.Evidence_Code,"\n"
                    break
                
                current_parent = parents.pop()
                current_parent_id = current_parent
                current_parent = go[current_parent_id]
  
                #alternately use goatools and calculate semantic distance
                mock_graph_path_v2 = semantic_distance(ntgaf.GO_ID,current_parent_id,go)

                #print out a line
                record = [current_parent.name,current_parent.namespace, current_parent.id,current_term.name, current_term.namespace, current_term.id ,ntgaf.DB_Symbol, ntgaf.DB, ntgaf.DB_ID,ntgaf.Evidence_Code,mock_graph_path_v2]
                line = '\t'.join(str(field) for field in record) + '\n'
                #print line
                output.write(line)

                #only break out the loop
                if len(parents) <= 0:
                    break

        output.close()
        
    print "done"
    
if __name__ == "__main__":
    '''first arg is the master config file'''

    config_file = sys.argv[1]

    # load config and run
    config = datalib.load_main_config(config_file)
   
    
    main(config)
