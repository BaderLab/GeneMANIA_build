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


# load interactions from i2d, processed via
# Harold's scripts, along with additional metadata from
# a local csv export of the sheets from:
#
#   http://spreadsheets.google.com/ccc?key=0AtfLNC1Xh4m7dGJSS2xnQVk0YUJ0aF9GUEpEUlpIM1E&hl=en
#
# description of the parsing process in:
#
#   http://baderlab.org/genemania/GeneManiaOperationalDb/ParsingI2D

import sys, os, shutil, csv, datalib
from optparse import OptionParser

# map their organism  naming to our codes
#organism_names = {'fly':'Dm', 'human':'Hs', 'mouse':'Mm', 'worm':'Ce', 'yeast':'Sc', }
organism_names = {}

SPREADSHEET_FILE_NAME = "i2d_all.csv"

#spreadsheet column indexes we want
EXPECTED_HEADER = "Organism,Datasource,Use,Processing Notes,Pubmed ID,Network Name Prefix,Comment".split(',')
ORGANISM_COL=0
DATASET_COL=1
USE_FLAG_COL=2
PUBMED_ID_COL=4
NETWORK_NAME_COL=5
NAME_COL=5
COMMENT_COL=6

def process_organism(config_file, organism_name, organism_code, data_folder, spreadsheet_file, collection_subdir = 'i2d'):
    '''
    loop through all the preprocessed network data files and perform
    the import into our source tree
    '''

    masterConfig = datalib.MasterConfig(config_file)
    data_dir = masterConfig.getDataDir()


    # process by iterating throug spreadsheet, and pulling
    # in the corresponding data files and metadata
    reader = csv.reader(open(spreadsheet_file, "rb"), delimiter=',')
    header = None

    for rownum, row in enumerate(reader):
        #print row
        if not header:
            header = row
            assert header == EXPECTED_HEADER
        else:
            if len(row) == 0:
                continue

            organism = row[ORGANISM_COL]
            dataset = row[DATASET_COL]
            use_flag = row[USE_FLAG_COL]

            if use_flag != 'TRUE':
                continue
            
            # source not predicted, skip
            if organism == organism_name:
                print "skipping source data", dataset
                continue

            network_name = row[NETWORK_NAME_COL]
            
            # append destination organism Y to network name, so it reads SomeName_X2Y, except
            # for the small scale studies network (under_threshold dataset).
            if dataset != 'under_threshold':
                network_name = network_name + organism_name
            
            # these next two are optional
            try:
                pubmed_id = row[PUBMED_ID_COL]
            except IndexError:
                pubmed_id = ''
            try:
                comment = row[COMMENT_COL]
            except IndexError:
                comment = ''

            #print 'importing', dataset
            
            # check if we have the corresponding data file
            data_file = os.path.join(data_folder, dataset)
            if not os.path.isfile(data_file):
                # missing data files are probably those under threshold
                print "can't find data file '%s', skipping" % data_file
                continue
            
            print "processing '%s'" % data_file
			# Harold 09Dec2009: removed creation of 
			# shared networks as instructed in ticket #786
			# --------------------------------------------
            #import_i2d_data(masterConfig, collection_subdir+'_sharedneighbor',
            #organism_code, data_file, dataset, 'Shared neighbor', source='I2D',
            #pubmed_id=pubmed_id, comment=comment, name=network_name)

            import_i2d_data(masterConfig, collection_subdir+'_direct',
            organism_code, data_file, dataset, 'Direct', source='I2D',
            pubmed_id=pubmed_id, comment=comment, name=network_name)

            
def import_i2d_data(config, collection_subdir, organism_code, data_file, dataset,
    processing_type, source=None, pubmed_id=None, name=None, comment=None):
    '''
    create a newtork metadata file, and copy the interaction file into
    the raw folder of the given collection subdir

    note that for each data file, we import it both as a direct and a
    shared neighbor network
    '''

    # for use in filenames, get rid of spaces and case in the processing type
    processing_type_simple = processing_type.lower()
    processing_type_simple = processing_type_simple.replace(' ', '-')


    cfg_filename = 'i2d_%s_%s.cfg' % (dataset, processing_type_simple)

    data_dir = config.getDataDir()
    collection_dir = os.path.join(data_dir, collection_subdir)


    dir = os.path.join(collection_dir, organism_code)
    if not os.path.exists(dir):
        os.makedirs(dir)

    cfg_filename = os.path.join(dir, cfg_filename)

    #print "importing", cfg_filename, organism_code, data_file

    cfg = datalib.make_empty_config()
    cfg.filename = cfg_filename

    cfg['gse']['raw_data'] = os.path.basename(data_file)
    cfg['gse']['raw_type'] = 'BINARY_NETWORK'
    cfg['dataset']['processing_type'] =  processing_type
    cfg['dataset']['group'] = 'predict' # Harold 9Dec2009: changed from 'other' to 'predict' - ticket #786
    raw_dir = config.config['FileLocations']['raw_dir']

    target = os.path.join(os.path.dirname(cfg.filename), raw_dir)
    print target
    if not os.path.exists(target):
        os.mkdir(target)

    target = os.path.join(target, os.path.basename(data_file))
    #print "copying %s to %s" % (data_file, target)
    shutil.copyfile(data_file, target)

    cfg['dataset']['organism'] = organism_code

    if pubmed_id:
        if pubmed_id != 'under-threshold':
            cfg['gse']['pubmed_id'] = pubmed_id
        else:
            cfg['dataset']['keywords'] = 'Small-scale studies'

    cfg['dataset']['source'] = source
    cfg['dataset']['subsource'] = dataset

    if pubmed_id:
        cfg['gse']['pubmed_id'] = pubmed_id
    if comment:
        cfg['dataset']['comment'] = comment
    if name:
        cfg['dataset']['name'] = name.replace("_", "-")

    cfg.write()

def process(config_file, input_folder):
    global organism_names
    tmp = datalib.load_main_config(config_file)
    i2d_org_list = datalib.lookup_field(tmp, "BuildScriptsConfig")["i2d_org"]
    organism_codes = datalib.lookup_field(tmp, "Organisms")["organisms"]

    print "i2d_org:", i2d_org_list
    print "organism_codes:", organism_codes
    print "input_folder:", input_folder

    organism_names = dict(zip(i2d_org_list.lower().split(), organism_codes))
    print "organism_names:", organism_names
    all_spreadsheet_file = os.path.join(input_folder, SPREADSHEET_FILE_NAME)
    for name, code in organism_names.items():
        print "loading %s" % code
        name_with_nice_case = name[0].upper() + name[1:].lower()

        if not os.path.exists(all_spreadsheet_file):
            raise Exception('network classification spreadsheet missing: ' + all_spreadsheet_file)
        
        org_input_folder = os.path.join(input_folder, name)
        process_organism(config_file, name_with_nice_case, code, org_input_folder, all_spreadsheet_file)    

def main(args):
    '''
    parse args & call process()
    '''

    usage = "usage: %prog [options] master_config_file.cfg input_folder"
    description = "load interactions from i2d, processed via some intermediate scripts"
    parser = OptionParser(usage=usage, description=description)

    (options, args) = parser.parse_args(args)

    if len(args) != 2:
        parser.error("require master config file, input_folder")

    config_file = args[0]
    input_folder = args[1]

    process(config_file, input_folder)
    
    print 'done'

if __name__ == '__main__':
    main(sys.argv[1:])

