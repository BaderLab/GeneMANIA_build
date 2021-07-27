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

import os.path

# datawarehouse id-mapping file import utility

# the input file is tab delimited, with each unique gene
# represended by exactly one row in the file. 

import sys
from optparse import OptionParser
import datalib
from identifiers import identifier_merger

def get_raw_files(raw_dir):
    '''
    return list of (organism_id, filename) tuples
    '''

    mappings = os.listdir(raw_dir)

    result = []
    for file in mappings:
        full = os.path.join(raw_dir, file)
        if os.path.isdir(full):
            continue
        parts = file.split('_')
        organism_id = parts[-1]
        result.append( (organism_id, os.path.join(raw_dir, file)) )

    return result

def make_new_filenames(org_prefix, normalized_dir):
    '''
    apply some naming conventions to
    generate normalized mapping file names
    '''
    
    norm_file = '%s_names.txt' % org_prefix
    norm_file = os.path.join(normalized_dir, norm_file)

    log_file = 'log_%s.txt' % org_prefix
    log_file = os.path.join(normalized_dir, log_file)

    return norm_file, log_file

def get_reverse_mapping_file(org_prefix, reverse_dir):
    '''
    return reverse mapping file, or None if it doesn't exist
    '''
    reverse_file = "ENTREZ_TO_ENSEMBL_%s" % org_prefix
    reverse_file = os.path.join(reverse_dir, reverse_file)
    
    if not os.path.exists(reverse_file):
        reverse_file = None
        
    return reverse_file
    
def process_mapping(org_prefix, raw_file, reverse_file, normalized_file, log_file, temp_dir, biotypes, filters, merge_names):
    '''
    normalize mappings from the given raw file into the specified
    output file.
    '''

    identifier_merger.raw_to_processed(raw_file, reverse_file, normalized_file, log_file, org_prefix, temp_dir, biotypes, filters, merge_names)
   
def process(config):

    raw = get_raw_files(config.getRawMappingDir())
    temp_dir = None # can write to a file for debugging, e.g. use: = '/tmp'

    for org_prefix, raw_file in raw:
        if datalib.is_organism_enabled(config.config, org_prefix):
            print "processing", org_prefix
            merge_names = datalib.is_merging_enabled(config.config, org_prefix)
            biotypes = datalib.get_biotypes(config.config, org_prefix)
            filters = datalib.get_filters(config.config, org_prefix)
            
            print "merge names:", merge_names
            print "biotypes:", biotypes
            print "source filters:", filters
            
            reverse_file = get_reverse_mapping_file(org_prefix, config.getReverseMappingDir())
            normalized_file, log_file = make_new_filenames(org_prefix, config.getProcessedMappingDir())
            print org_prefix, raw_file, reverse_file, normalized_file, log_file
    
            process_mapping(org_prefix, raw_file, reverse_file, normalized_file, log_file, temp_dir, biotypes, filters, merge_names)

def main(args):
    '''extract args and execute
    normalization
    '''

    usage = "usage: %prog master_config_file.cfg"
    description = "normalize raw mapping files"
    parser = OptionParser(usage=usage, description=description)
    
    (options, args) = parser.parse_args(args)

    if len(args) != 1:
        parser.error("require one master config file")
        
    config_file = args[0]
    config = datalib.MasterConfig(config_file)
    process(config)
    print 'done'
    
if __name__ == '__main__':
    main(sys.argv[1:])

