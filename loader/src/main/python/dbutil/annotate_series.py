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


import datalib, geolib, csv, sys, os

def load_annotation_file(filename):
    '''
    return a map from id -> some preferred column for GPL platform
    files downloaded from geo.

    the files have tab separated data after a line that says
    !platform_table_begin
    '''

    map = {}

    reader = csv.reader(open(filename, "rb"), delimiter='\t')
    header = None

    in_body = False
    header = None
    
    map = {}
    for rownum, row in enumerate(reader):

        # spin until we get to the data body
        if not in_body:
            if row[0] == '!platform_table_begin':
                in_body = True
        else:
            if row[0] == '!platform_table_end':
                break

            elif not header:
                header = row
                platform_annot_id_col = header.index('ID')
                title_col = header.index('Gene title')
                symbol_col = header.index('Gene symbol')
                gene_id_col = header.index('Gene ID') # entrez id

            else:
                platform_annot_id = row[platform_annot_id_col]
                gene_id = row[gene_id_col]
                title = row[title_col]
                symbol = row[symbol_col]

                # apparently we can have multiple gene ids in the mapping, delimited by '///'
                gene_id_list = gene_id.split('///')

                # TODO: instead of just skipping these,
                # load them into a blacklist, and log warnings when
                # processing the series giving the reason, eg
                # could not map probe x because it maps to multiple genes
                if len(gene_id_list) > 1:
                    print "skipping multiple genes", platform_annot_id, gene_id, title, symbol
                elif not gene_id:
                    print "skipping no gene id:", platform_annot_id, gene_id, title, symbol
                else:
                    map[platform_annot_id] = gene_id

    return map


def apply_platform_annotation(filename, id_map, output_filename, log_filename):
                    
    reader = csv.reader(open(filename, "rb"), delimiter='\t')
    header = None

    in_body = False
    header = None

    out = open(output_filename, 'w')
    log = open(log_filename, 'w')
    map = {}
    for rownum, row in enumerate(reader):

        # spin until we get to the data body
        if not row:
            continue # empty lines
        if not in_body:
            if row[0] == '!series_matrix_table_begin':
                in_body = True
        else:
            if row[0] == '!series_matrix_table_end':
                break
                
            elif not header:
                header = row
                id_col = header.index('ID_REF')
                
            else:
                id = row[id_col]
                try:
                    gene_id = id_map[id]
                    row[id_col] = gene_id
                    output_row = '\t'.join(row) + '\n'
                    out.write(output_row)
                except KeyError:
                    log.write("no mapping for %s, skipping\n" % id)

    out.close()
    log.close()
                    
    
def main(config):
    '''
    look through all the cfg files looking up the series_matrix
    and platform files that should be used in order to produce
    a profile file identified by gene ids.

    the new profile file is written, and the name of the profile
    file is added to the cfg.
    '''

    data_dir = datalib.get_location(config, 'data_dir')
    platforms_dir = datalib.get_location(config, 'platform_data_dir')
    raw_dir = config['FileLocations']['raw_dir']
    profile_dir = config['FileLocations']['profile_dir']
    
    enabled_organisms = config['Organisms']['organisms']

    
    network_cfgs = datalib.load_cfgs(data_dir)
    for cfg in network_cfgs:
        
        if cfg['dataset']['organism'] not in enabled_organisms:
            continue
        
        if cfg['dataset']['source'] != 'GEO' and cfg['dataset']['type'] != 'gse':
            continue
        print cfg.filename
        gse_id = cfg['gse']['gse_id']
        series_matrix_file = cfg['gse']['raw_data']
        if cfg['gse']['raw_type'] != 'unannotated_profile':
            print "unexpected raw type for geo gse series:", cfg['gse']['raw_type'], ", skipping microarray platform annotation"
            continue
        
        if series_matrix_file.strip() == '':
            print "no series matrix file for %s, skipping" % (gse_id)
            continue
            
        platform = cfg['gse']['platforms'] # there should only be one, right?
        platform_file = os.path.join(platforms_dir, geolib.get_platform_filename_for_id(platform))

        series_matrix_file = os.path.join(os.path.dirname(cfg.filename), raw_dir, series_matrix_file)
        
        # TODO: could keep a few maps in mem instead of rereading all the time, but
        # why waste time optimizing a non-critical path
        try:
            map = load_annotation_file(platform_file)
        except:
            exctype, value = sys.exc_info()[:2]
            print "failed to load annotation file %s for %s, cause:\n%s %s" % (platform_file, gse_id, exctype, value)
            continue

        # annotated file stored in the profile_dir folder
        dir = os.path.join(os.path.dirname(cfg.filename), profile_dir)
        if not os.path.exists(dir):
            os.mkdir(dir)

        annotated_file = os.path.join(dir, '%s_annotated.txt' % gse_id)
        log_file = os.path.join(dir, '%s_annotated.log' % gse_id)

        apply_platform_annotation(series_matrix_file, map, annotated_file, log_file)

        cfg['gse']['profile'] = os.path.basename(annotated_file)
        cfg.write()
        
def test():
    map = load_annotation_file('platforms/GPL71.annot')
    apply_platform_annotation('data/AT/GSE277_series_matrix.txt', map, 'blah')
    
if __name__ == '__main__':

    config_file = sys.argv[1]
    config = datalib.load_main_config(config_file)
    main(config)
