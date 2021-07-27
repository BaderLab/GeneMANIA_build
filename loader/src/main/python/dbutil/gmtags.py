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

def load_mesh2gmtag_map(filename):
    '''
    load the 'all_selected_terms' worksheet exported as
    a csv from: https://spreadsheets.google.com/ccc?key=pTX2vgjAbNQ03USmAtMLofQ&hl=en
    (the all_selected_terms worksheet)

    returns a map with key the mesh descriptor, and value a list of 
    suggeted internal genemania tags for the term
    '''

    reader = csv.reader(open(filename, "rb"), delimiter=',')
    header = None

    term_col = 0
    tag_col = 3

    map = {}
    for rownum, row in enumerate(reader):
        if not header: 
            header = row
            assert header[term_col] == 'Term'
            assert header[tag_col].startswith('Suggested Tag')
        else:
            term = row[term_col]
            tags = row[tag_col]

            tag_list = tags.split(',')
            # seems to be some surrounding whitespace from spreadsheet, clean up
            tag_list = [element.strip() for element in tag_list]
            term = term.strip()
            map[term] = tag_list

    return map

def apply_tags_to_file(filename, gse_col, term_col, tag_map):
    '''
    given a file with mesh term in some column, apply tags
    '''

    all_gse = set()
    tagged_gse = set()

    for line in open(filename):
        line = line.strip()
        fields = line.split('\t')
        gse = fields[gse_col]
        term = fields[term_col]

        all_gse.add(gse)

        if term in tag_map:
            tags = tag_map[term]
            fields.append(','.join(tags))
            if tags > 0:
                tagged_gse.add(gse)

        print '\t'.join(fields)
    return all_gse

def apply_tags(terms, tag_map):
    all_tags = set()
    for term in terms:
        if term in tag_map:
            tags = tag_map[term]
            all_tags.update(tags)
    return all_tags

def test():
    m = load_mesh2gmtag_map('mesh2gmtags.csv')
    print m
    all_gse = apply_tags_to_file('../../mesh_descriptors.txt', 1, 3, m)
    print 'all gse:', len(all_gse) # what was this next bit about?: , 'tagged gse:', len(tagged_gse)
   
def main(config):
    '''
    extract the full set (propagated) mesh descriptors from
    the series config files, look up the corresponding genemania tags,
    and update the config files with these genemania tags
    '''

    mesh_to_gmtag_filename = datalib.get_location(config, 'mesh_to_gmtag_filename')
    mesh_to_tag_map = load_mesh2gmtag_map(mesh_to_gmtag_filename)
    data_dir = datalib.get_location(config, 'data_dir')
    network_cfgs = datalib.load_cfgs(data_dir)
    for cfg in network_cfgs:
        print cfg.filename
        try:
            mesh_terms = cfg['gse']['propagated_mesh_descriptors']
        except KeyError:
            print "no propagated mesh descriptors for %s, skipping" % cfg.filename
            continue
        tags = apply_tags(mesh_terms, mesh_to_tag_map)
        cfg['gse']['genemania_tags'] = list(tags)
        cfg.write()
    
if __name__ == '__main__':
    #test()

    config_file = sys.argv[1]
    config = datalib.load_main_config(config_file)
    main(config)
