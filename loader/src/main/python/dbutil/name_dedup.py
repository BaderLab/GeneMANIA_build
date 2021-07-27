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


import sys, os, datalib
from optparse import OptionParser
import unittest, tempfile, shutil, StringIO
from configobj import ConfigObj

# its possible for our auto name generation tool to produce the same
# name for multiple data sets (eg when different data sets are produced
# from the same publication
#
# this script resolves names by appending 'A', 'B', etc to networks that
# collide within the same organism and network group. networks with the same
# name but in different groups are allowed

DEDUP_DISCLAIMER = 'One of %s datasets produced from this publication.'

def process(config_file, test=False):
    config = datalib.load_main_config(config_file)
    organisms = config['Organisms']['organisms']

    for organism in organisms:
        organism_name = config[organism]['name']
        short_name = config[organism]['short_name']
        common_name = config[organism]['common_name']
        short_id = config[organism]['short_id']
        organism_id = config[organism]['gm_organism_id']

        process_organism(config, short_id, test)

def process_organism(config, short_id, test=False):
    
    filter = ['dataset.organism', short_id]
    filters = [filter]

    network_cfgs = datalib.get_filtered_configs(config, filters)


    # this dict contains a group name key, with value a dict name->list of configs
    grps = {}

    # build up map containing collisions
    for cfg in network_cfgs:
        print cfg.filename
        group = cfg['dataset']['group']        

        # names is a dict contains an auto_name key, with value a list of cfg objects that have that name
        # only at the group level
        try:
            names = grps[group]
        except KeyError:
            print "new group for", group
            names = {}
            grps[group] = names
        
        try:
            name = cfg['dataset']['name']
            if name.strip() == '':
                name = None
        except KeyError:
            name = None

        # if this network has a name override, ignore the dedup
        if name:
            continue
        try:
            auto_name = cfg['dataset']['auto_name']
            if auto_name.strip() == '':
                auto_name = None
        except KeyError:
            auto_name = None
            
        if auto_name:
            if names.has_key(auto_name):
                cfg_list = names[auto_name]
                cfg_list.append(cfg)
            else:
                cfg_list = [cfg]
                names[auto_name]= cfg_list

    # now loop over and dedup
    for group in grps:
        print "deduping group %s" % group
        names = grps[group]
        
        for auto_name in names:
            cfg_list = names[auto_name]

            if len(cfg_list) == 0:
                raise Exception('internal error, no configs for an auto name???')
            elif len(cfg_list) == 1:
                continue
            elif len(cfg_list) > 26:
                raise Exception('more collisions for a dataset than we have letters for dedup! check if somethings gone wrong here')
            else:
                # we need to dedup!

                pmid_counts = count_pmids(cfg_list)
                
                endings = 'abcdefghijklmnopqrstuvwxyz'
                endings = endings.upper()

                for i, cfg in enumerate(cfg_list):
                    newname = '%s %s' % (auto_name, endings[i])
                    print ('setting name to %s' % newname).encode('utf8')
                    cfg['dataset']['auto_name'] = newname
                    
                    # only apply dedup disclaimer if data is from same publication
                    pmid = get_pmid(cfg)
                    if pmid and pmid_counts[pmid] > 1: 
                        cfg['dataset']['aux_description'] = DEDUP_DISCLAIMER % pmid_counts[pmid]

                    if not test:
                        print "saving change"
                        cfg.write()

def get_pmid(cfg):
    '''
    return pubmed id or None if not in cfg or defined to an empty string
    '''
    try:
        pmid = cfg['gse']['pubmed_id']
    except KeyError:
        pmid = None
         
    if pmid and pmid.strip() == '':
        pmid = None

    return pmid

def count_pmids(cfg_list):
    '''
    given a list of configs, return a dictionary wiht key pubmid_id and value the # of cfg's in
    the list that have that pmid. configs with no pmid appear in the dict with key None
    '''
    
    pmid_counts = {}
    
    for cfg in cfg_list:
        pmid = get_pmid(cfg)
        
        if pmid in pmid_counts:
            pmid_counts[pmid] = pmid_counts[pmid] + 1
        else:
            pmid_counts[pmid] = 1

    return pmid_counts

def main(args):
    usage = "usage: %prog [options] master_config_file.cfg"

    description = "resolve network name collisions by appending a counter"
    parser = OptionParser(usage=usage, description=description)

    parser.add_option('-t', '--test',
    help='test mode, print what would be updated without saving the result',
    action="store_true", dest="test", default=False)

    (options, args) = parser.parse_args(args)

    if len(args) != 1:
        parser.error("require one master config file")

    config_file = args[0]

    process(config_file, test=options.test)

# minimal bits of master config needed for this test
TEST_MASTER_CFG = """
[FileLocations]

base_dir = .
data_dir = data
raw_dir = raw
profile_dir = profile
network_dir = network
attribute_dir = attributes
processed_network_dir = processed_network

[Organisms]
organisms = Hs, Sc

[Hs]
name = Homo sapiens
short_name = H. sapiens
common_name = human
ncbi_taxonomy_id = 9606
short_id = Hs
gm_organism_id = 4

[Sc]
name = Saccharomyces cerevisiae
short_name = S. cerevisiae
common_name = baker's yeast
ncbi_taxonomy_id = 4932
short_id = Sc
gm_organism_id = 6
"""

class TestAttributeAssociationLoader(unittest.TestCase):
    
    def setUp(self):
        self.db_dir = tempfile.mkdtemp()
        print "temp test dir:", self.db_dir
    
        # create a minimal db.cfg for this test
        self.master_cfg = self.create_master_cfg()
        
    def tearDown(self):
        shutil.rmtree(self.db_dir)
        
    def create_master_cfg(self):
        cfg = ConfigObj(StringIO.StringIO(TEST_MASTER_CFG), encoding='utf8')
        
        cfg.filename = os.path.join(self.db_dir, 'db.cfg')
        cfg.write()
        return cfg
        
    def create_network_config(self, organism, filename, collection, group, network_name, pmid):
        cfg = datalib.make_empty_config()

        dirname = os.path.join(datalib.get_location(self.master_cfg, 'data_dir'), collection, organism)
        print dirname
        
        if not os.path.exists(dirname):
            os.makedirs(dirname)
             
        cfg.filename = os.path.join(dirname, filename)
        cfg['dataset']['organism'] = organism
        cfg['dataset']['group'] = group
        cfg['dataset']['auto_name'] = network_name
        cfg['gse']['pubmed_id'] = pmid
        
        cfg.write()
        return cfg
        
    def test_dedup(self):        
        '''
        same name for two networks in same organism and group, renaming should be applied
        '''
        
        # create network metadata
        cfg1 = self.create_network_config('Hs', 'cfg1.cfg', 'geo', 'coexp', 'abc-def-2001', '12345')
        cfg2 = self.create_network_config('Hs', 'cfg2.cfg', 'geo', 'coexp', 'abc-def-2001', '12345')
        
        process(self.master_cfg.filename)
        
        cfg1_result = ConfigObj(cfg1.filename)
        cfg2_result = ConfigObj(cfg2.filename)
        
        print cfg1_result
        print cfg2_result
        self.assertNotEqual(cfg1_result['dataset']['auto_name'], cfg2_result['dataset']['auto_name'], 'names should be different')

        expected_disclaimer = DEDUP_DISCLAIMER % 2
        
        self.assertTrue(expected_disclaimer in cfg1_result['dataset']['aux_description'], "description must contain dedup note")
        self.assertTrue(expected_disclaimer in cfg2_result['dataset']['aux_description'], "description must contain dedup note")
    
    def test_different_pmid(self):
        '''
        same name for two networks, but pubmed ids differ. the networks should be renamed, but the extra text
        about the networks being from the same publication should not be added
        '''
        
        # create network metadata        
        cfg1 = self.create_network_config('Hs', 'cfg1.cfg', 'geo', 'coexp', 'abc-def-2001', '12345')
        cfg2 = self.create_network_config('Hs', 'cfg2.cfg', 'geo', 'coexp', 'abc-def-2001', '54321')
        
        process(self.master_cfg.filename)
        
        cfg1_result = ConfigObj(cfg1.filename)
        cfg2_result = ConfigObj(cfg2.filename)
        
        print cfg1_result
        print cfg2_result
        self.assertNotEqual(cfg1_result['dataset']['auto_name'], cfg2_result['dataset']['auto_name'], 'names should be different')

        self.assertTrue('aux_description' not in cfg1_result['dataset'], "description must not contain dedup note")
        self.assertTrue('aux_description' not in cfg2_result['dataset'], "description must not contain dedup note")        

    def test_same_name_different_group(self):
        '''
        in this case the names don't clash and renaming should not be applied
        '''
        
        # create network metadata
        cfg1 = self.create_network_config('Hs', 'cfg1.cfg', 'geo', 'coexp', 'abc-def-2001', '12345')
        cfg2 = self.create_network_config('Hs', 'cfg2.cfg', 'geo', 'coloc', 'abc-def-2001', '12345')
        
        process(self.master_cfg.filename)
        
        cfg1_result = ConfigObj(cfg1.filename)
        cfg2_result = ConfigObj(cfg2.filename)
        
        print cfg1_result
        print cfg2_result
        self.assertEqual(cfg1_result['dataset']['auto_name'], cfg2_result['dataset']['auto_name'], 'names should be equal')

        self.assertTrue('aux_description' not in cfg1_result['dataset'], "description must not contain dedup note")
        self.assertTrue('aux_description' not in cfg2_result['dataset'], "description must not contain dedup note")
        
    def test_same_name_different_organism(self):
        '''
        would be a shock if this failed. but i've been shocked before, so ...
        '''

        # create network metadata        
        cfg1 = self.create_network_config('Hs', 'cfg1.cfg', 'geo', 'coexp', 'abc-def-2001', '12345')
        cfg2 = self.create_network_config('Sc', 'cfg2.cfg', 'geo', 'coexp', 'abc-def-2001', '12345')
        
        process(self.master_cfg.filename)
        
        cfg1_result = ConfigObj(cfg1.filename)
        cfg2_result = ConfigObj(cfg2.filename)
        
        print cfg1_result
        print cfg2_result
        self.assertEqual(cfg1_result['dataset']['auto_name'], cfg2_result['dataset']['auto_name'], 'names should be same')

        self.assertTrue('aux_description' not in cfg1_result['dataset'], "description must not contain dedup note")
        self.assertTrue('aux_description' not in cfg2_result['dataset'], "description must not contain dedup note")

    def test_no_pmid(self):
        '''
        if two networks with same name but no pmid, don't count them as being from the same publication (so no disclaimer text)
        '''

        '''
        same name for two networks, but pubmed ids differ. the networks should be renamed, but the extra text
        about the networks being from the same publication should not be added
        '''
        
        # create network metadata        
        cfg1 = self.create_network_config('Hs', 'cfg1.cfg', 'geo', 'coexp', 'abc-def-2001', '')
        cfg2 = self.create_network_config('Hs', 'cfg2.cfg', 'geo', 'coexp', 'abc-def-2001', '')
        
        process(self.master_cfg.filename)
        
        cfg1_result = ConfigObj(cfg1.filename)
        cfg2_result = ConfigObj(cfg2.filename)
        
        print cfg1_result
        print cfg2_result
        self.assertNotEqual(cfg1_result['dataset']['auto_name'], cfg2_result['dataset']['auto_name'], 'names should be different')

        self.assertTrue('aux_description' not in cfg1_result['dataset'], "description must not contain dedup note")
        self.assertTrue('aux_description' not in cfg2_result['dataset'], "description must not contain dedup note")
        
    def test_clash_combo(self):
        '''
        3 clashing networks, two with same pubmid id, other with a different one. make sure the two have the correct
        count of total from same publication reported, and the other doesn't claim its from the same publication. all
        should get unique names.
        '''
        
        # create network metadata
        cfg1 = self.create_network_config('Hs', 'cfg1.cfg', 'geo', 'coexp', 'abc-def-2001', '12345')
        cfg2 = self.create_network_config('Hs', 'cfg2.cfg', 'geo', 'coexp', 'abc-def-2001', '12345')
        cfg3 = self.create_network_config('Hs', 'cfg3.cfg', 'geo', 'coexp', 'abc-def-2001', '54321')
        
        process(self.master_cfg.filename)
        
        cfg1_result = ConfigObj(cfg1.filename)
        cfg2_result = ConfigObj(cfg2.filename)
        cfg3_result = ConfigObj(cfg3.filename)
        
        print cfg1_result
        print cfg2_result
        print cfg3_result
        
        self.assertNotEqual(cfg1_result['dataset']['auto_name'], cfg2_result['dataset']['auto_name'], 'names should be different')
        self.assertNotEqual(cfg1_result['dataset']['auto_name'], cfg3_result['dataset']['auto_name'], 'names should be different')
        self.assertNotEqual(cfg2_result['dataset']['auto_name'], cfg3_result['dataset']['auto_name'], 'names should be different')

        expected_disclaimer = DEDUP_DISCLAIMER % 2
        
        self.assertTrue(expected_disclaimer in cfg1_result['dataset']['aux_description'], "description must contain dedup note")
        self.assertTrue(expected_disclaimer in cfg2_result['dataset']['aux_description'], "description must contain dedup note")        
        self.assertTrue('aux_description' not in cfg3_result['dataset'], "description must not contain dedup note")
           
if __name__ == '__main__':
    main(sys.argv[1:])

