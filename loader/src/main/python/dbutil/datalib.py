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

__author__="khalid"
__date__ ="$Mar 24, 2009 7:05:32 PM$"

import os, gzip, glob, re
from configobj import ConfigObj
import unittest

# should have wrapped the config objects
# in classes originally. start
# doing this now and build up functionality
#
# eventually, client code should never have to
# inspect the a ConfigObj directly, we
# may want to switch to other storage later
class MasterConfig(object):
    def __init__(self, filename):
        self.config = load_main_config(filename)

    def getJobParallelism(self):
        '''return default value of 1
        if none specified
        '''
        
        try:
            return int(self.config['Defaults']['System']['max_parallel_jobs'])
        except KeyError:
            return 1

    def getDataDir(self):
        '''location of data dir
        
        error if not defined
        '''

        return get_location(self.config, 'data_dir')

    def getRawMappingDir(self):
        return get_location(self.config, 'raw_mappings_dir')

    def getReverseMappingDir(self):
        return get_location(self.config, 'reverse_mappings_dir')
    
    def getProcessedMappingDir(self):
        return get_location(self.config, 'processed_mappings_dir')

    def getRawOntologiesDir(self):
        return get_location(self.config, 'raw_ontologies_dir')

    def getProcessedOntologiesDir(self):
        return get_location(self.config, 'processed_ontologies_dir')

    def getGeoMetaDB(self):
        '''return path to geometadb sqlite db
        '''

    def getOrganismShortNameForCode(self, organism):
        return self.config[organism]['short_name']

    def getOrganismCodeForName(self, organism_name):
        return get_short_id_for_organism_name(self.config, organism_name)

    def getNetworkGroupNameForCode(self, group_code):
        return self.masterConfig['NetworkGroups'][group_code]['name']

    def getNetworkGroupDescriptionForCode(self, group_code):
        return self.masterConfig['NetworkGroups'][group_code]['description']
    

class NetworkConfig(object):
    def __init__(self, filename, masterConfig = None):
        self.config = load_cfg(filename)
        self.masterConfig = masterConfig # for defaults etc

    def getName(self):
        try:
            return self.config['dataset']['name']
        except:
            return None

    def getAutoName(self):
        try:
            return self.config['dataset']['auto_name']
        except:
            return None

    def getDescription(self):
        try:
            return self.config['dataset']['description']
        except:
            return None

    def getNetworkGroupCode(self):
        return self.config['dataset']['group']

    def getDefaultSelected(self):
        return self.config['dataset']['default_selected']

    def getNetworkId(self):
        return self.config['dataset']['gm_network_id']

    def getPubmedId(self):
        try:
            return self.config['gse']['pubmed_id']
        except:
            return None

    def getPubmedArticle(self):
        try:
            return self.config['gse']['pubmed_article']
        except:
            return None
        
    def getPubmedJournal(self):
        try:
            return self.config['gse']['pubmed_journal_shortname']
        except:
            return None

    def getPubmedAuthors(self):
        try:
            return self.config['gse']['pubmed_authors']
        except:
            return None

    def getPubmedDate(self):
        try:
            return self.config['gse']['pubmed_year']
        except:
            return None
        
    def getNetworkTypeCode(self):
        return None # not sure what to do here, generate dynamically?
    
    def getGSEID(self):
        '''return None if not found
        if none specified
        '''

        try:
            return self.config['gse']['gse_id']
        except KeyError:
            return None

    def getGDSID(self):
        '''return None if not found
        if none specified
        '''

        try:
            return self.config['gse']['gds_id']
        except KeyError:
            return None

    def getSource(self):
        return self.config['dataset']['source']

    def getSubSource(self):
        try:
            return self.config['dataset']['subsource']
        except KeyError:
            return None

    def getKeywords(self):
        try:
            return self.config['dataset']['keywords']
        except KeyError:
            return None

    def getProcessingType(self):
        try:
            return self.config['dataset']['processing_type']
        except KeyError:
            return None

    def getType(self):
        try:
            return self.config['dataset']['type']
        except KeyError:
            return None
        
    def getOrganismCode(self):
        return self.config['dataset']['organism']

    def getOrganismShortName(self):
        code = self.getOrganismCode()
        return self.masterConfig.getOrganismShortnameForCode(code)

    def getProcessedNetworkFilename(self):
        try:
            return self.config['gse']['processed_network']
        except KeyError:
            return None

    def getComment(self):
        try:
            return self.config['dataset']['comment']
        except KeyError:
            return None

    def getAuxDescription(self):
        try:
            return self.config['dataset']['aux_description']
        except KeyError:
            return None
        
def make_empty_config():
    cfg = ConfigObj(encoding='utf8')

    cfg['dataset'] = {}
    cfg['dataset']['type'] = ''
    cfg['dataset']['group'] = ''
    cfg['dataset']['organism'] = ''
    cfg['dataset']['default_selected'] = 0
    cfg['dataset']['name'] = ''
    cfg['dataset']['description'] = ''
    cfg['gse'] = {}
    cfg['gse']['gse_id'] = ''
    cfg['gse']['raw_type'] = ''
    cfg['gse']['title'] = ''
    cfg['gse']['contributor'] = ''
    cfg['gse']['pubmed_id'] = ''
    cfg['gse']['num_samples'] = 0
    cfg['gse']['platforms'] = ['']

    return cfg

def load_main_config(file_name):
    '''
    we are just using ConfigObj objects as our
    data objects
    '''

    if not os.path.isfile(file_name):
        raise Exception("file not found: '%s'" % file_name)
    
    config = ConfigObj(file_name, encoding='utf8')
    return config

def load_cfgs(dir, wrapperClass=None):
    '''
    get all dataset configurations in directory hierarchy rooted at dir,
    return as a list of ConfigObj objects. This ignores the list of organisms
    and network groups configured in master config file
    '''
    
    cfgs = []
    for root, dirs, files in os.walk(dir):
        if files:
            for filename in files:
                if filename.endswith('.cfg'):
                    fullname = os.path.join(root, filename)
                    if wrapperClass:
                        cfg = wrapperClass(fullname)
                    else:
                        cfg = load_cfg(fullname)
                    cfgs.append(cfg)

    return cfgs

def load_cfg(cfg_filename ):
    cfg = ConfigObj(cfg_filename, encoding='utf8')
    return cfg

def lookup_field(cfg, field):
    '''
    field looks like abc.def[xyz],
    which we translate to
    cfg['abc']['def'][xyz]
    '''
    field = field.strip()
    try:
        pos = field.index('[')
        a = field[0:pos]
        b = field[pos:]
        b = b [1:-1] # strip off surrounding square brackets
        b = int(b)
    except ValueError:
        a, b = field, None

    a_parts = a.split('.')
    value = cfg
    for part in a_parts:
        try:
            value = value[part]
        except KeyError:
            value = 'None'
            
    if b != None and value != None:
        value = value[b]

    if type(value) == list:
        value = join_multifield(value)

    return value

def set_field(cfg, field, value):
    '''
    field looks like abc.def,
    which we translate to
    cfg['abc']['def']
    '''
    field = field.strip()

    parts = field.split('.')

    # all but the last parts are dicts,
    # create if not already existing
    
    obj = cfg
    for part in parts[:-1]:
        try:
            obj = obj[part]
        except KeyError:
            obj[part] = {}
            obj = obj[part]

    # now set the value, don't handle lists yet
    obj[parts[-1]] = value

def join_multifield(field):
    if ',' in field:
        raise Exception('this no worky')
    return ','.join(field)

# ok, so there's now two ways to do filtering here. somethings got to go
# or maybe merge ...

def make_filter(orgs, groups):
    def filter(cfg):
        if cfg['dataset']['organism'] in orgs and cfg['dataset']['group'] in groups:
            return True
        else:
            return False

    return filter

def make_cmp(orgs, groups):
    def cmp(x, y):
        x_org = x['dataset']['organism']
        y_org = y['dataset']['organism']

        if orgs[x_org] < orgs[y_org]:
            return -1
        elif orgs[x_org] > orgs[y_org]:
            return 1
        else:
            x_group = x['dataset']['group']
            y_group = y['dataset']['group']
            if groups[x_group] < groups[y_group]:
                return -1
            elif groups[x_group] > groups[y_group]:
                return 1
            else:
                return 0
            
    return cmp

def make_cmp_obj(orgs, groups):
    def cmp(x, y):
        x_org = x.getOrganismCode()
        y_org = y.getOrganismCode()

        if orgs[x_org] < orgs[y_org]:
            return -1
        elif orgs[x_org] > orgs[y_org]:
            return 1
        else:
            x_group = x.getNetworkGroupCode()
            y_group = y.getNetworkGroupCode()
            if groups[x_group] < groups[y_group]:
                return -1
            elif groups[x_group] > groups[y_group]:
                return 1
            else:
                return 0

    return cmp


def get_filtered_configs(master_cfg, filters):
    '''
    return list of configs matching criteria

    filters is a list of (name,value) tuples, eg:

        [('dataset.organism', 'Sc'), ('dataset.source', 'GEO')]

    '''

    data_dir = get_location(master_cfg, 'data_dir')
    network_cfgs = load_cfgs(data_dir)

    filtered_network_cfgs = []

    for cfg in network_cfgs:
        if check_filters(cfg, filters) == True:
            filtered_network_cfgs.append(cfg)

    return filtered_network_cfgs

def check_filters(cfg, filters):
    '''
    return True if all filters are satisfied, else False
    '''
    for filter in filters:
        field, expected_value = filter
        found_value = lookup_field(cfg, field)
        if expected_value != found_value.encode("utf-8"):
            return False

    return True

def load_active_cfgs(config, wrap=False):
    '''
    return list of cfgs, only for organisms and network
    groups that are listed in the master config,
    and ordered by organism and network group display
    priority

    Hmm, we could just replace 'i' below with a priority
    field from the config, to make it explicit.

    wrap is just tricky business ...
    '''

    dir = get_location(config, 'data_dir')
    if wrap:
        all_cfgs = load_cfgs(dir, NetworkConfig)
    else:
        all_cfgs = load_cfgs(dir)
        
    active_organisms = {}
    for i, organism in enumerate(config['Organisms']['organisms']):
        short_id = config[organism]['short_id']
        active_organisms[short_id] = i

    active_groups = {}
    for i, group in enumerate(config['NetworkGroups']):
        group_info = config['NetworkGroups'][group]
        code = group_info['code']
        active_groups[code] = i

    # filter
    filter = make_filter(active_organisms, active_groups)
    if wrap:
        all_cfgs = [cfg for cfg in all_cfgs if filter(cfg.config) == True]
    else:
        all_cfgs = [cfg for cfg in all_cfgs if filter(cfg) == True]

    # sort
    if wrap:
        cmp = make_cmp_obj(active_organisms, active_groups)
    else:
        cmp = make_cmp(active_organisms, active_groups)

    all_cfgs.sort(cmp)

    return all_cfgs

def save_cfgs(configs):
    '''
    write out all the config objects
    '''

    for cfg in configs:
        cfg.write()

def magic_organism_file_matcher(config, organism_short_id, pattern):
    '''
    we have files stored with organism specific naming, but using
    all kinds of inconsistent conventions. this takes a glob-style
    pattern, containing the string MAGIC_ORG_IDENTIFIER, and tries
    various combinations of organism id, short code, long name etc,
    until it finds one where the corresponding file exists. otherwise
    raises an error. 
    '''
    
    organism_name = config[organism_short_id]['name']
    short_name = config[organism_short_id]['short_name']
    common_name = config[organism_short_id]['common_name']
    short_id = config[organism_short_id]['short_id']
    organism_id = config[organism_short_id]['gm_organism_id']
    default_ontology = config[organism_short_id]['default_ontology']
    taxonomy_id = config[organism_short_id]['ncbi_taxonomy_id']
    
    guesses = [pattern.replace('MAGIC_ORG_IDENTIFIER', organism_id),
               pattern.replace('MAGIC_ORG_IDENTIFIER', short_id),
               pattern.replace('MAGIC_ORG_IDENTIFIER', organism_name.replace(' ','_')),
               pattern.replace('MAGIC_ORG_IDENTIFIER', organism_name),
               pattern.replace('MAGIC_ORG_IDENTIFIER', common_name.replace(' ', '_')),
               pattern.replace('MAGIC_ORG_IDENTIFIER', common_name),
               ]

    for guess in guesses:
        print "guessing '%s'" % guess
        if glob.glob(guess):
            return guess
    
    raise Exception("failed to find file for pattern: '%s'" % pattern)
    
    
def gunzip(gzfilename):
    '''
    gunzip file and remove the original. return
    the new file's name
    '''

    newfilename = gzfilename.rstrip('.gz')

    gzfile = gzip.GzipFile(gzfilename, 'r')
    newfile = open(newfilename, 'w')
    
    newfile.write(gzfile.read())

    newfile.close()
    gzfile.close()

    os.unlink(gzfilename)
    return newfilename
    
def get_raw_mapping_file(dir, organism_short_id):
    '''
    there should be exactly one file in dir
    that ends with '_organism_short_id'
    '''

    entries = os.listdir(dir)
    found = [entry for entry in entries if entry.endsswith('_%s' % organism_short_id)]

    if len(found) != 1:
        raise Exception("failed to find a unique mapping file for %s" % organism_short_id)

    return found[0]

def get_processed_mapping_file(dir, organism_short_id):
    '''
    there should be exactly one file in dir
    that starts with 'organism_short_id_' 
    '''

    entries = os.listdir(dir)
    found = [entry for entry in entries if entry.startswith('%s_' % organism_short_id)]

    if len(found) != 1:
        raise Exception("failed to find a unique mapping file for %s" % organism_short_id)

    return found[0]

def get_short_id_for_organism_name(config, organism_name):
    '''
    this feels hackish. some processing of info in the config file
    '''

    map = {}
    for organism in config['Organisms']['organisms']:
        name = config[organism]['name']
        name = name.upper()
        id = config[organism]['short_id']
        map[name] = id

    return map[organism_name.upper()]

def get_short_id_for_organism_common_name(config, organism_name):
    '''
    this feels hackish. some processing of info in the config file
    '''

    map = {}
    for organism in config['Organisms']['organisms']:
        name = config[organism]['common_name']
        name = name.upper()
        id = config[organism]['short_id']
        map[name] = id

    return map[organism_name.upper()]
        
def get_group_code_from_group_name(config, group_name):
    '''
    shoulda used a db
    '''
    
    map = {}
    for group in config['NetworkGroups']:
        group_info = config['NetworkGroups'][group]
        name = group_info['name']
        code = group_info['code']
        map[name] = code

    return map[group_name]

def get_location(config, location_name=None):
    '''
    helper to apply base path to given location. 
    and now we realize that config should have been wrapped in an object 
    with this and other utils as methods ... (starting to happen now,
    see eg MasterConfig)
    
    if  location_name not given then just return base_dir
    '''

    base_dir = config['FileLocations']['base_dir']

    if base_dir == '.':
        base_dir = os.path.dirname(config.filename)

    if location_name:
        location = config['FileLocations'][location_name]
        location = os.path.join(base_dir, location)
    else:
        location = base_dir
        
    return location

def get_data_collection(data_dir, cfg_filename):
    '''
    the collection is just the first subdir under the data_dir

    this sillyness because the idea of groupings was retrofitted in,
    and the cfg iterator things don't return the collection yet
    '''

    abs1 = os.path.abspath(data_dir)
    abs2 = os.path.abspath(cfg_filename)
    common = os.path.commonprefix([abs1, abs2])

    if not os.path.isdir(common):
        raise Exception('path matching problem, partial common prefix? %s' % common)

    # strip off the common part from the cfg filename
    rest = abs2[len(common):]

    # split into path components, the first one is the collection
    a = rest
    while a and a != '/':
        a, b = os.path.split(a)
    return b

def dir_for_data_file_type(config, file_type):
    '''shouldn't have made it this configurable ...
    '''
    if file_type == 'raw_data':
        return config['FileLocations']['raw_dir']
    elif file_type == 'profile':
        return config['FileLocations']['profile_dir']
    elif file_type == 'network':
        return config['FileLocations']['network_dir']
    elif file_type == 'processed_network':
        return config['FileLocations']['processed_network_dir']
    else:
        raise Exception("don't know about file type %s" % file_type)
    
def get_loader_jar(target_dir):
    '''
    the version number changes, find via naming pattern
    '''
    files = glob.glob(os.path.join(target_dir, 'genemania-loader-*-jar-with-dependencies.jar'))

    if not files:
        raise Exception("failed to find loader jar")
    if len(files) > 1:
        raise Exception("found multiple loader jars")
    
    return files[0]

def is_organism_enabled(config, short_code):
    if short_code in config['Organisms']['organisms']:
        return True
    else:
        return False

def is_merging_enabled(config, org_prefix):
    key = 'identifier_merging_enabled'
    try:
        enabled = config[org_prefix][key]
    except KeyError:
        raise Exception('missing setting in master config for organism %s: %s' % (org_prefix, key))
    
    enabled = enabled.strip()
    if enabled.lower() == 'true':
        return True
    else:
        return False

def get_biotypes(config, org_prefix):
    key = 'identifier_biotypes'
    try:
        biotypes = config[org_prefix][key]
    except KeyError:
        raise Exception('missing setting in master config for organism %s: %s' % (org_prefix, key))

    # make sure we return a list
    if isinstance(biotypes, basestring):
        biotypes = [biotypes]

    return biotypes

def get_filters(config, org_prefix):
    key = 'identifier_sources_to_ignore'
    try:
        filters = config[org_prefix][key]
    except KeyError:
        raise Exception('missing setting in master config for organism %s: %s' % (org_prefix, key))
    
    # make sure we return a list, empty if no filters defined
    if isinstance(filters, basestring):
        if filters.strip() == '':
            filters = []
        else:
            filters = [filters]
       
    return filters

def clean_filename(filename):
    '''
    remove non-ascii chars, replace whitespace with underscores
    '''
    
    filename = re.sub(r'[\s]+', '_', filename)
    filename = re.sub(r'[^\w\.\-]+', '', filename)
    
    return filename

class TestCleanFilename(unittest.TestCase):
    def test(self):
        assert clean_filename('ab-c_d.txt') == 'ab-c_d.txt'
        assert clean_filename('ab c  d.txt') == 'ab_c_d.txt'