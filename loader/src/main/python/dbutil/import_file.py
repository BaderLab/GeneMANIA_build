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


# import a data file into a given collection, used for
# ad-hoc imports (eg data files from collaborators etc


import sys, os, shutil, datalib
from optparse import OptionParser

def process(config_file, collection, organism_code, data, group_code,
    source=None, subsource=None, pubmed_id=None, name=None, comment=None,
    keywords=None, description=None, default=None):
    '''
    create a new network metadata file, and copy the corresonding raw file
    into a data collection for processing
    '''

    masterConfig = datalib.MasterConfig(config_file)
    
    # if we have a dir, import all files inside    
    if os.path.isdir(data):
        data_files = os.listdir(data)
        data_files = [os.path.join(data, data_file) for data_file in data_files if os.path.isfile(os.path.join(data, data_file))]
        if len(data_files) == 0:
            raise Exception("input folder given but no files found: %s" % data)       
    # check if the data file exists
    elif os.path.isfile(data):
        data_files = [data]
    else:
        raise Exception("failed to find data file or directory '%s'" % data)
    
    # check if the collection exists in our config
    try:
        masterConfig.config['processing'][collection]
    except KeyError:
        raise Exception("the given collection '%s' is not defined in the master config file, please update" % collection)

    # check organism and group codes
    try:
        masterConfig.config[organism_code]
    except:
        raise Exception("there is no organism with the code '%s' defined in the master config file" % organism_code)

    try:
        masterConfig.config['NetworkGroups'][group_code]
    except:
        raise Exception("there is no network group with the code '%s' defined in the master config file" % group_code)
    
    # create organism and raw_data folders if necessary
    data_dir = masterConfig.getDataDir()
    collection_dir = os.path.join(data_dir, collection)

    dir = os.path.join(collection_dir, organism_code)
    if not os.path.exists(dir):
        os.makedirs(dir)

    raw_dir = masterConfig.config['FileLocations']['raw_dir']

    target_dir = os.path.join(dir, raw_dir)
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    for data_file in data_files:
        target = os.path.join(target_dir, os.path.basename(data_file))
        print "copying %s to %s" % (data_file, target)
        shutil.copyfile(data_file, target)
    
        # build up the config
        cfg_filename = os.path.basename(data_file)
        cfg_filename = cfg_filename.replace(' ', '_')
        cfg_filename = cfg_filename.replace('.', '_')
        cfg_filename = '%s.cfg' % (cfg_filename)
        cfg_filename = os.path.join(dir, cfg_filename)
    
        cfg = datalib.make_empty_config()
        cfg.filename = cfg_filename
    
        cfg['dataset']['organism'] = organism_code
        cfg['dataset']['group'] = group_code
        
        cfg['gse']['raw_data'] = os.path.basename(data_file)
    
        if pubmed_id:
            cfg['gse']['pubmed_id'] = pubmed_id
        if comment:
            cfg['dataset']['comment'] = comment
        
        if name:
            if name.upper() == 'USE_FILE_NAME':
                cfg['dataset']['name'] = os.path.splitext(os.path.basename(data_file))[0]
            else:
                cfg['dataset']['name'] = name
    
        if description:
            cfg['dataset']['description'] = description
        if source:
            cfg['dataset']['source'] = source
    
        if subsource:
            cfg['dataset']['subsource'] = subsource
    
        if keywords:
            cfg['dataset']['keywords'] = keywords
    
        if default:
            cfg['dataset']['default_selected'] = '1'
    
        cfg.write()


def main(args):
    '''
    parse args & call process()
    '''

    usage = "usage: %prog [options] master_config_file.cfg"
    description = "import data file"
    parser = OptionParser(usage=usage, description=description)

    parser.add_option('-c', '--collection',
    help='collection in which to drop the data',
    action="store", dest="collection")

    parser.add_option('-r', '--raw',
    help='raw file to import, or entire directory of raw files',
    action="store", dest="raw_file")

    parser.add_option('-o', '--organism',
    help='organism code, eg Hs, Mm',
    action="store", dest="organism_code")

    parser.add_option('-g', '--group',
    help='network group code, eg coexp, cocomp',
    action="store", dest="group_code")

    parser.add_option('-s', '--source',
    help='source of data',
    action="store", dest="source")

    parser.add_option('--subsource',
    help='subsource of data, eg a specific collaborators name, or something that specifies the data from the larger source name',
    action="store", dest="subsource")

    parser.add_option('-n', '--name',
    help='name, or USE_FILE_NAME to just use the file name without extension as the network name',
    action="store", dest="name")

    parser.add_option('-d', '--description',
    help='description',
    action="store", dest="description")

    parser.add_option('--default',
    help='should this network be used as a default network, false if not given, any given value means true',
    action="store", dest="default")

    parser.add_option('-p', '--pmid',
    help='pubmed id',
    action="store", dest="pubmed_id")

    parser.add_option('--comment',
    help='comment',
    action="store", dest="comment")

    parser.add_option('-k', '--keywords',
    help='keywords',
    action="store", dest="keywords")

    (options, args) = parser.parse_args(args)

    if len(args) != 1:
        parser.error("require master config file, input_folder")

    if not options.collection:
        parser.error("must specify collection")

    if not options.raw_file:
        parser.error("must specify raw data file")

    if not options.source:
        parser.error("must specify source for data, eg GEO, PFAM, COLLABORATOR, please something ...")

    if not options.organism_code:
        parser.error("must specify organism code, eg Hs, Mm")

    if not options.group_code:
        parser.error("must specify network group code, eg cocomp, coexp, other")

    config_file = args[0]

    process(config_file, options.collection, options.organism_code, options.raw_file,
    options.group_code,
    source=options.source, subsource=options.subsource,
    name=options.name, comment=options.comment, pubmed_id=options.pubmed_id,
    keywords=options.keywords, description=options.description, default=options.default)

if __name__ == '__main__':
    main(sys.argv[1:])

