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


import csv, sys
import datalib

def load_mesh_tree(fn):
    id_to_term = {}
    term_to_ids = {} # can be more than 1 id for a term name, so keep values in a set

    for line in open(fn):
        line = line.strip()
        if line: # silly file ends with a blank line
            term, id = line.split(';')
            id_to_term[id] = term
            if term in term_to_ids:
                ids = term_to_ids[term]
                ids.add(id)
            else:
                ids = set([id])
                term_to_ids[term] = ids

    return id_to_term, term_to_ids

# where is this in the mesh db? hopefully
# it doesn't change often, hardcoded here for now
root_terms=  {
'A': 'Anatomy',
'B': 'Organisms',
'C': 'Diseases',
'D': 'Chemicals and Drugs',
'E': 'Analytical, Diagnostic and Therapeutic Techniques and Equipment',
'F': 'Psychiatry and Psychology',
'G': 'Phenomena and Processes',
'H': 'Disciplines and Occupations',
'I': 'Anthropology, Education, Sociology and Social Phenomena',
'J': 'Technology, Industry, Agriculture',
'K': 'Humanities',
'L': 'Information Science',
'M': 'Named Groups',
'N': 'Health Care',
'V': 'Publication Characteristics',
'Z': 'Geographicals',
}

def propagate_term(id, id_to_term):
    '''
    return a list of terms from the given id, 
    including ancestor terms
    '''

    # root_term comes from that first letter, eg 'A' for Anatomy
    root_term = root_terms[id[0]]
    all_terms = [root_term]

    id_parts = id.split('.')
    for i in range(len(id_parts)):
        sub_id = '.'.join(id_parts[0:i+1])
        ancestor_term = id_to_term[sub_id]
        all_terms.append(ancestor_term)

    return all_terms

def propagate_terms_from_file(fn, delim, col, id_to_term, term_to_ids):
    '''
    read in mesh terms from a column of a file, figure out all the mesh ids
    that match that term, then up-propagate to get all the ancestor terms.
    '''
    
    reader = csv.reader(open(fn, "rb"), delimiter=delim)
    for row in reader:
        if row:
            term = row[col]
            organism = row[2]
            suggested = row[3]
        else:
            continue

        try:
            ids = term_to_ids[term]
        except:
            print >> sys.stderr, "skipping", term
            continue

        for id in ids:
            ancestors = propagate_term(id, id_to_term)
            print '\t'.join([term, organism, suggested, id,] +  ancestors)


def main(config):
    '''
    for each mesh desciptor, look up associated ids (can be more than one),
    and for eachof these, propate to all ancestors, accumulating results in a set.
    update the series config file with all the resulting terms.
    '''
    mesh_tree_file = datalib.get_location(config, 'mesh_tree_file')
    id_to_term, term_to_ids = load_mesh_tree(mesh_tree_file)

    data_dir = datalib.get_location(config, 'data_dir')
    network_cfgs = datalib.load_cfgs(data_dir)
    for cfg in network_cfgs:
        print cfg.filename
        try:
            mesh_descriptors = cfg['gse']['mesh_descriptors']
        except KeyError:
            #print "no mesh descriptors for %s, skipping" % cfg.filename
            mesh_descriptors = []

        all_mesh = set()
        for descriptor in mesh_descriptors:
            try:
                ids = term_to_ids[descriptor]
            except KeyError:
                print "failed to find mesh descriptor '%s' in mesh tree, ignoring" % descriptor
                continue
                
            for id in ids:
                propagated_terms = propagate_term(id, id_to_term)
                all_mesh.update(propagated_terms)
        cfg['gse']['propagated_mesh_descriptors'] = list(all_mesh)
        cfg.write()
        
def test():
    id_to_term, term_to_ids = load_mesh_tree('mesh_data/mtrees2009.bin')
    propagate_terms_from_file('mesh_data/selected_terms.csv', ',', 0, id_to_term, term_to_ids)

if __name__ == '__main__':
    #test()

    config_file = sys.argv[1]
    config = datalib.load_main_config(config_file)
    main(config)
