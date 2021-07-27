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


# load interactions from pathway commons, processed via
# Harold's scripts

import sys, os, shutil, datalib, jobqueue
from optparse import OptionParser

def process(config_file, input_folder, collection_subdir = 'pathwaycommons'):
    '''
    loop through all the preprocessed network data files and perform
    the import into our source tree
    '''

    masterConfig = datalib.MasterConfig(config_file)
    data_dir = masterConfig.getDataDir()

    dir = os.path.join(input_folder, 'pubmed_out')
    import_pubmed(masterConfig, dir, collection_subdir)

    dir = os.path.join(input_folder, 'source_out')
    import_source(masterConfig, dir, collection_subdir)

def import_pubmed(config, dir, collection_subdir):

    for root, dirs, files in os.walk(dir):
        #print root, dirs, files
        organism = os.path.basename(root)

        # strip off timestamp, which is after the last hyphen
        #organism = organism[:organism.rfind('-')]

        organism = organism.replace('-', ' ')
        print organism, files
        
        if files:
            for filename in files:
                if not filename.endswith('.txt'):
                    continue
                fullname = os.path.join(root, filename)
                print '   ', fullname

                pubmed_id = filename[:filename.find('.')]
                print '   ', pubmed_id
                if pubmed_id == 'under-threshold':
                    print 'yeah!'
                import_pathwaycommons_data(config, collection_subdir+'_direct',
                organism, fullname, 'Direct', pubmed_id=pubmed_id)

                #import_pathwaycommons_data(config, collection_subdir+'_sharedneighbor',
                #organism, fullname, 'Shared Neighbor', pubmed_id=pubmed_id)

def import_source(config, dir, collection_subdir):
    for root, dirs, files in os.walk(dir):
        #print root, dirs, files
        organism = os.path.basename(root)

        # strip off timestamp, which is after the last hyphen
        #organism = organism[:organism.rfind('-')]

        organism = organism.replace('-', ' ')
        print 'organism', organism

        if files:
            for filename in files:
                if not filename.endswith('.txt'):
                    continue
                fullname = os.path.join(root, filename)
                print '   ', fullname

                source = filename[:filename.find('.')]
                print '   ', source
                import_pathwaycommons_data(config, collection_subdir+'_direct',
                organism, fullname, 'Direct', source=source)
                #import_pathwaycommons_data(config, collection_subdir+'_sharedneighbor',
                #organism, fullname, 'Shared neighbor', source=source)

def import_pathwaycommons_data(config, collection_subdir, organism, data_file,
    processing_type, source=None, pubmed_id=None):
    '''
    create a newtork metadata file, and copy the interaction file into
    the raw folder of the given collection subdir

    note that for each data file, we import it both as a direct and a
    shared neighbor network
    '''

    if source and pubmed_id:
        raise Exception("wait, pwc import with both source and pubmed id?")

    # for use in filenames, get rid of spaces and case in the processing type
    processing_type_simple = processing_type.lower()
    processing_type_simple = processing_type_simple.replace(' ', '-')
    
    if source:
        cfg_filename = 'pwc_%s_%s.cfg' % (source, processing_type_simple)
    elif pubmed_id:
        cfg_filename = 'pwc_%s_%s.cfg' % (pubmed_id, processing_type_simple)
    else:
        raise Exception("don't know how to make cfg filename: %s" % data_file)

    data_dir = config.getDataDir()
    collection_dir = os.path.join(data_dir, collection_subdir)


    #try:
    #    print "organism: [%s]" % (organism)
    #    organism_code = config.getOrganismCodeForName(organism)
    #except KeyError:
    #    print "organism not known, skipping:", organism
    #    return
    print "organism: [%s]" % (organism)
    organism_code = organism

    dir = os.path.join(collection_dir, organism_code)
    if not os.path.exists(dir):
        os.makedirs(dir)

    cfg_filename = os.path.join(dir, cfg_filename)

    print "importing", cfg_filename, organism_code, data_file

    cfg = datalib.make_empty_config()
    cfg.filename = cfg_filename
    
    cfg['gse']['raw_data'] = os.path.basename(data_file)
    cfg['gse']['raw_type'] = 'BINARY_NETWORK'
    cfg['dataset']['processing_type'] =  processing_type

    if pubmed_id:
        #cfg['dataset']['group'] = 'pi'
        pass
    else:
        cfg['dataset']['group'] = 'path'

    raw_dir = config.config['FileLocations']['raw_dir']

    target = os.path.join(os.path.dirname(cfg.filename), raw_dir)
    if not os.path.exists(target):
        os.mkdir(target)

    target = os.path.join(target, os.path.basename(data_file))
    print "copying %s to %s" % (data_file, target)
    shutil.copyfile(data_file, target)

    cfg['dataset']['organism'] = organism_code
    cfg['dataset']['source'] = 'PATHWAYCOMMONS'

    if pubmed_id:
        if pubmed_id != 'under-threshold':
            cfg['gse']['pubmed_id'] = pubmed_id
        else:
            cfg['dataset']['keywords'] = 'Small-scale studies'
            cfg['dataset']['name'] = 'PATHWAYCOMMONS-SMALL-SCALE-STUDIES'

    # set the source to pathway commons, and use the source field if given
    # as the subsource
    if source:
        cfg['dataset']['subsource'] = source


    cfg.write()
    

def main(args):
    '''
    parse args & call process()
    '''

    usage = "usage: %prog [options] master_config_file.cfg input_folder"
    description = "load interactions from pathway commons, processed via some intermediate scripts"
    parser = OptionParser(usage=usage, description=description)

    #parser.add_option('-f', '--filter',
    #help='network metadata filter expression',
    #action='append', type='string', dest='filter')

    (options, args) = parser.parse_args(args)

    if len(args) != 2:
        parser.error("require one master config file")

    config_file = args[0]
    input_folder = args[1]

    process(config_file, input_folder)

if __name__ == '__main__':
    main(sys.argv[1:])

