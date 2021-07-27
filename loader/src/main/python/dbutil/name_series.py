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

import sys, datalib

def format_author_info(authors_list, year):

    if not authors_list and not year:
        return None
    
    if len(authors_list) == 0:
        authors = ''
    elif len(authors_list) == 1:
        authors = authors_list[0]
    else:
        authors = "%s-%s" % (authors_list[0], authors_list[-1])

    if year:
        authors = "%s-%s" % (authors, year)
        
    return authors

def make_reference_id(cfg):
    '''
    we usually put a reference id in the title, like a 
    pubmed id or geo id
    '''

    refcode = None

    # pull out geo specific reference codes,
    # otherwise pubmed id,
    # otherwise, return None
    try:
        refcode = cfg['gse']['gse_id']
    except KeyError:
        pass

    try:
        if not refcode:
            refcode = cfg['gse']['gse_id']
    except KeyError:
        pass

    try:
        if not refcode:
            refcode = cfg['gse']['pubmed_id']
            if refcode:
                refcode = "PMED%s" % refcode
    except KeyError:
        pass

    # we had some weird junk in some of the old
    # metadata, handle here ... TODO: this can go away eventually
    if refcode == 'N/A':
        refcode = None
        
    return refcode

def get_processing_type(masterConfig, cfg):
    '''
    pull out the processing type corresponding to the
    networks processing recipe from the master config file
    '''
    
    data_dir = masterConfig.getDataDir()
    collection = datalib.get_data_collection(data_dir, cfg.filename)

    # look up processing instructions for the collection
    try:
        processing = masterConfig.config['processing'][collection]
    except KeyError:
        # no collection level config, try file level
        try:
            processing = cfg['processing']
        except KeyError:
            print "no processing instructions for cfg %s, returning empty processing code" % cfg.filename
            processing = None

    processing_type = None
    
    if processing:
        try:
            processing_type = processing['processing_type']
        except KeyError:
            pass

    return processing_type

def make_name(masterConfig, cfg):
    '''
    creates names with authors and year, eg:

        Popescu-Dinesh-Kumar-2007

    this comes via pubmed info, if we don't have then
    put in source and refernce info

    '''
   # pull out pmed info
    try:
        pmed_id = cfg['gse']['pubmed_id']
    except KeyError:
        pmed_id = ''

    if pmed_id:
        try:
            pmed_year = cfg['gse']['pubmed_year']
        except KeyError:
            pmed_year = None

        try:
            pmed_authors = cfg['gse']['pubmed_authors']
        except KeyError:
            pmed_authors = []

        #if there are no authors then use the pmed in the name
        # This is to make figuring out more easily
        # networks that were being called for example -2011
        if len(pmed_authors) == 0:
            pmed_authors = ["NoAuthors_pmid" + pmed_id]

        name = format_author_info(pmed_authors, pmed_year)
    # what to do if we don't have a pubmed? fall back to source?
    # put in source/ref infor
    else:
        name = cfg['dataset']['source']

        # sometimes we have a subsource, like i2d
        try:
            subsource = cfg['dataset']['subsource']
        except KeyError:
            subsource = None

        if subsource:
            name = "%s-%s" % (name, subsource)


        ref_id = make_reference_id(cfg)
        if ref_id:
            name = '%s-%s' % (name, ref_id)

    return name

def process(config):
    '''
    read in all the cfg files and figure out what
    nice auto-generated name to give each network
    '''

    masterConfig = datalib.MasterConfig(config.filename)

    data_dir = datalib.get_location(config, 'data_dir')
    network_cfgs = datalib.load_cfgs(data_dir)
    
    for cfg in network_cfgs:
        name = make_name(masterConfig, cfg)
        cfg['dataset']['auto_name'] = name

        processing_type = get_processing_type(masterConfig, cfg)
        if processing_type:
            cfg['dataset']['processing_type'] = processing_type
                    
        msg = "%s %s %s" % (name, processing_type, cfg.filename)
        print msg.encode('utf8')
        cfg.write()

def main(args):

    config_file = args[0]
    config = datalib.load_main_config(config_file)

    process(config)

if __name__ == '__main__':
    main(sys.argv[1:])
