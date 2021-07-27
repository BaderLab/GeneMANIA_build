

import sys, os, datalib
import pandas as pd
from optparse import OptionParser
import unittest, tempfile, shutil, StringIO
from configobj import ConfigObj

DEDUP_DISCLAIMER = 'One of %s datasets produced from this publication.'
ENDINGS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

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
    if len(network_cfgs) == 0:
        print "no configs for", short_id
        return

    df = config_list_to_dataframe(network_cfgs, ['dataset.source', 'dataset.group',
                                                 'dataset.organism', 'dataset.name',
                                                 'dataset.auto_name', 'gse.pubmed_id',
                                                 'gse.gse_id', ])

    # ignore cases where dataset.name is explicitly provided by user,
    # we only dedup the auto names
    df = df[df['dataset.name'] == '']

    groups = df.groupby(['dataset.organism', 'dataset.group', 'dataset.auto_name'])

    for group_key, group_frame in groups:
        if len(group_frame) < 2:
            continue

        group_frame = group_frame.sort(['gse.pubmed_id', 'dataset.source', 'gse.gse_id'], axis=0)


        if len(group_frame) > len(ENDINGS):
            raise Exception("too many colliding networks to rename")

        # append the dedup letters 'A', 'B', etc to the name
        group_frame['dedup_suffix'] = [' ' + ending for ending in ENDINGS[:len(group_frame)]]
        group_frame['deduped_auto_name'] = group_frame['dataset.auto_name'] \
                                           + group_frame['dedup_suffix']

        # add extra text when the pmids match
        subgroups = group_frame.groupby('gse.pubmed_id')

        for subgroup_key, subgroup_frame in subgroups:
            if len(subgroup_frame) == 1 or subgroup_key == "":
                write_updated_configs(subgroup_frame)
                continue

            num_pubmid_matches = len(subgroup_frame)
            aux = DEDUP_DISCLAIMER % num_pubmid_matches
            subgroup_frame['aux_description'] = aux
            write_updated_configs(subgroup_frame, write_aux=True)


def write_updated_configs(dataframe, test=False, write_aux=False):

    for index, series in dataframe.iterrows():
        cfg = datalib.load_cfg(index)
        cfg['dataset']['auto_name'] = series['deduped_auto_name']
        if write_aux:
            cfg['dataset']['aux_description'] = series['aux_description']

        print "updating", cfg.filename
        if not test:
            cfg.write()


def config_list_to_dataframe(configs, columns):
    '''
    take a list of loaded configs, and convert specified fields to
    dataframe columns. the index is the file path to the config.
    '''

    return pd.DataFrame(config_gen(configs, columns),
                        index=config_name_list(configs),
                        columns=columns)

def config_name_list(configs):
    '''
    return list of the names of the configs
    '''

    return [config.filename for config in configs]

def config_gen(configs, columns):
    '''
    generator to extract given elements from each config,
    in order to convert to tabular data
    '''

    for config in configs:
        item = []
        for column in columns:
            parts = column.split('.')
            try:
                value = config[parts[0]][parts[1]]
            except KeyError:
                value = ''

            value = value.strip()
            item.append(value)

        yield item


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

class TestDeduplication(unittest.TestCase):

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

    def create_network_config(self, organism, filename, collection, group,
                              network_name, pmid, source=None, gse_id=None):

        cfg = datalib.make_empty_config()

        dirname = os.path.join(datalib.get_location(self.master_cfg, 'data_dir'), collection, organism)

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        cfg.filename = os.path.join(dirname, filename)
        cfg['dataset']['organism'] = organism
        cfg['dataset']['group'] = group
        cfg['dataset']['auto_name'] = network_name
        cfg['gse']['pubmed_id'] = pmid

        if source is not None:
            cfg['dataset']['source'] = source

        if gse_id is not None:
            cfg['gse']['gse_id'] = gse_id

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

    def test_order(self):
        '''
        make sure ordering of networks is consistent. this test could just work by accident, since it depends on file loading
        order. but running it with sorting in the dedup code disabled does cause it to fail in manual testing, so there's
        hope it can be helpful. should probably make reliable by mocking out the config loading code
        '''

        # create network metadata
        cfg1 = self.create_network_config('Hs', 'cfg1.cfg', 'geo', 'coexp', 'abc-def-2001', '12345', 'GEO', 'GSE2')
        cfg2 = self.create_network_config('Hs', 'cfg2.cfg', 'geo', 'coexp', 'abc-def-2001', '12345', 'GEO', 'GSE1')

        cfg3 = self.create_network_config('Hs', 'cfg3.cfg', 'direct_network', 'pi', 'abc-def-2001', '12345', 'IREF')
        cfg4 = self.create_network_config('Hs', 'cfg4.cfg', 'direct_network', 'pi', 'abc-def-2001', '12345', 'BIOGRID')

        process(self.master_cfg.filename)

        cfg1_result = ConfigObj(cfg1.filename)
        cfg2_result = ConfigObj(cfg2.filename)
        cfg3_result = ConfigObj(cfg3.filename)
        cfg4_result = ConfigObj(cfg4.filename)

        self.assertEqual(cfg1_result['dataset']['auto_name'][-2:], ' B', 'wrong ordering')
        self.assertEqual(cfg2_result['dataset']['auto_name'][-2:], ' A', 'wrong ordering')

        self.assertEqual(cfg3_result['dataset']['auto_name'][-2:], ' B', 'wrong ordering')
        self.assertEqual(cfg4_result['dataset']['auto_name'][-2:], ' A', 'wrong ordering')


if __name__ == '__main__':
    main(sys.argv[1:])
