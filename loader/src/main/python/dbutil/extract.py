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

import sys, codecs, datetime, csv, shutil
import os.path
import datalib
from optparse import OptionParser

'''
dump data into intermediate (non-db specific) files, split into one file
per table. Inspired by JM's DataExtractor, but driven by metadata stored
in config files instead of strict filesystem hierarchy.
'''

PUBMED_URL_PATTERN = "http://www.ncbi.nlm.nih.gov/pubmed/%s";

class Table(object):
    '''
    hey, what's this?
    '''

    def __init__(self, name, fields, dir, ref_fields=None, skip_id=False, encoding="utf8"):
        # name of table will be used to produce an
        # output file, name.txt
        self.name = name

        # ordered list of fields in the table, id field is always first
        self.fields = fields

        # data sources refer to records in this table by
        # ref_field (must be in fields), we need to be able
        # to conveniently convert form ref_field to id, hence
        # the map. so ref_field should be a unique column in
        # the table.
        self.ref_fields = ref_fields

        if ref_fields:
            self.ref_fields_to_id = {}
            self.ref_fields_index = [fields.index(ref_field)-1 for ref_field in ref_fields] # minus -1 because add() doesn't take the id column

        # output file is created in dir. create the dir if needed
        self.dir = dir
        if not os.path.exists(dir):
            os.mkdir(dir)

        # first value for id field
        self.id = 1
        self.skip_id = skip_id # don't write the id field out

        # file handle
        self.encoding = encoding
        self.filename = os.path.join(dir, "%s.txt" % name)
        if encoding:
            self.f = codecs.open(self.filename, "w", encoding)
        else: # no encoding is faster
            self.f = open(self.filename, "w")

        # keep track of the number of records we write out.
        # this might be different than the id field if the
        # caller is providing us with non-incremental id's
        self.record_count = 0

    def size(self):
        return self.record_count

    def max_id(self):
        return self.id-1
        
    def add(self, values, id=None):
        '''
        value to add for all fields except for the id field,
        which is auto-generated

        can be explicitly passed an id, in which case we skip the auto-increment thing
        '''

        if id:
            new_id = int(id)
        else:
            if(isinstance(self.id,int)):
                new_id = self.id
            else:
                new_id = unicode(self.id,"utf8")
            
        assert len(values) == len(self.fields)-1

        # replace None's with empty string. what's the
        # python one-liner for this?
        new_values = []
        for v in values:
            if v == None:
                v = ''
            new_values.append(v)
        values = new_values

        if self.skip_id:
            record = self.format(values)
        else:
            record = self.format([new_id] + values)
        #print record
        
        self.f.write(record)

        if self.ref_fields:
            key_parts = [values[ref_field_index] for ref_field_index in self.ref_fields_index]
            key = '-'.join(key_parts)
            self.ref_fields_to_id[key] = new_id

        if id:
            self.id = max(self.id, new_id) + 1
        else:
            self.id += 1

        self.record_count += 1
        
        return new_id
        
    def format(self, values):
        if self.encoding:
            return u'\t'.join((unicode(val) for val in values)) + '\n'
        else:
            return '\t'.join((str(val) for val in values)) + '\n'

    def lookup(self, ref_fields):
        key = '-'.join(ref_fields)
        try:
            id = self.ref_fields_to_id[key]
        except KeyError:
            id = None

        return id
    
    def close(self):
        self.f.close()

    def make_schema_record(self):
        '''
        the description of a table is just a record with the table name
        followed by the ordered list of table field names. tab delimited.
        '''

        record_fields = [self.name] + self.fields
        return '\t'.join(record_fields)

def make_nullifempty_clause(fields):
    '''
    trick to make empty string fields get loaded as null by mysql bulk db load,
    instead of as empty '' strings. unfortunately it also causes numeric fields
    containing 0 get get loaded as nulls. argh.
    '''
    clause = []
    for field in fields:
        part = "%s=nullif(%s, '')" % (field, field)
        clause.append(part)

    return "SET %s" % (','.join(clause))

class DB(object):
    '''
    okay, now we're just getting carried away. shoulda just used sqlite.
    '''

    def __init__(self, dir):

        self.dir = dir

        # in-memory table objects
        self.nodes = Table('NODES', ['ID', 'NAME', 'GENE_DATA_ID', 'ORGANISM_ID'], dir, ('NAME',))
        self.genes = Table('GENES', ['ID', 'SYMBOL', 'SYMBOL_TYPE', 'NAMING_SOURCE_ID', 'NODE_ID', 'ORGANISM_ID', 'DEFAULT_SELECTED'], dir)
        self.organisms = Table('ORGANISMS', ['ID', 'NAME', 'DESCRIPTION', 'ALIAS', 'ONTOLOGY_ID', 'TAXONOMY_ID'], dir, ('NAME',))
        self.networks = Table('NETWORKS', ['ID', 'NAME', 'METADATA_ID', 'DESCRIPTION', 'DEFAULT_SELECTED', 'GROUP_ID'], dir)
        self.network_groups = Table('NETWORK_GROUPS', ['ID', 'NAME', 'CODE', 'DESCRIPTION', 'ORGANISM_ID'], dir, ('NAME','ORGANISM_ID'))
        self.interactions = Table('INTERACTIONS', ['ID', 'fromNode', 'toNode', 'weight', 'NAME', 'NETWORK_ID'], dir, encoding=None)
        self.gene_data = Table('GENE_DATA', ['ID', 'DESCRIPTION', 'EXTERNAL_ID', 'LINKOUT_SOURCE_ID'], dir)
        self.gene_naming_sources = Table('GENE_NAMING_SOURCES', ['ID', 'NAME', 'RANK', 'SHORT_NAME'], dir, ('NAME',))
        self.statistics = Table('STATISTICS', ['ID', 'organisms', 'networks', 'interactions', 'genes', 'predictions', 'date'], dir)
        self.network_metadata = Table('NETWORK_METADATA', ['ID', 'source', 'reference',
        'pubmedId', 'authors', 'publicationName', 'yearPublished',
        'processingDescription', 'networkType', 'alias', 'interactionCount', 'dynamicRange',
        'edgeWeightDistribution', 'accessStats', 'comment', 'other', 'title', 'url', 'sourceUrl'], dir)
        self.tags = Table('TAGS', ['ID', 'NAME'], dir, ['NAME'])
        self.network_tag_assoc = Table('NETWORK_TAG_ASSOC', ['ID', 'NETWORK_ID', 'TAG_ID'], dir)
        self.ontologies = Table('ONTOLOGIES', ['ID', 'NAME'], dir, ('NAME',))
        self.ontology_categories = Table('ONTOLOGY_CATEGORIES', ['ID', 'ONTOLOGY_ID', 'NAME', 'DESCRIPTION'], dir)

        # table i should not have a foreing key to table j if i < j
        self.table_order = [
            self.ontologies,
            self.ontology_categories,
            self.organisms,
            self.network_groups, self.network_metadata, self.networks,
            self.gene_naming_sources, self.gene_data, self.nodes, self.genes,
            self.statistics,
            self.interactions,
            self.tags,
            self.network_tag_assoc,
            ]


    def close(self):

        for table in self.table_order:
            table.close()

    def write_schema(self):
        '''
        write out a schema file describing all the flat-text files

        '''

        schema_filename = os.path.join(self.dir, 'SCHEMA.txt')

        file = open(schema_filename, 'w')

        for table in self.table_order:
            record = table.make_schema_record()
            file.write(record + '\n')

        file.close()
        
class Extractor(object):
    def __init__(self, config, handle_interactions='small_table'):

        self.config = config
        self.masterConfig = datalib.MasterConfig(config.filename) # same as config but through wrapper object, TODO: clean up redundancy
        self.dbdir = datalib.get_location(self.config, 'generic_db_dir')
        self.db = DB(self.dbdir)
        self.handle_interactions = handle_interactions
        # since we may not load interactions directly in the db, but need
        # to keep track of the count for statistics, keep them in here
        self.total_interactions = 0

    def extract(self):
        self.extract_ontologies()
        self.extract_organisms()
        self.extract_gene_naming_sources()
        self.extract_nodes_and_gene_data()
        self.extract_tags()
        self.extract_networks()
        self.update_statistics()

        # write out schema
        self.db.write_schema()
        
    def close(self):
        self.db.close()

    def update_statistics(self):
        today = datetime.date.today()
        date = today.strftime('%Y-%m-%d')
        self.db.statistics.add([self.db.organisms.size(), self.db.networks.size(), self.total_interactions, self.db.nodes.size(), 0, date])

    def extract_ontologies(self):

        # retrieve all files in processed ontologies folder,
        # enter each in ontologies table, and all its records
        # in the categories table

        # disabled: experimental loading of functional categories from 
        # admin ui, overwriting those automatically loaded from GO via
        # other pipeline steps
        #self.copy_replacement_ontologies_kludge()

        processed_ontologies_dir = self.masterConfig.getProcessedOntologiesDir()
        ontology_files = os.listdir(processed_ontologies_dir)

        for file in ontology_files:
            ontology_name = os.path.splitext(file)[0]
            ontology_id = self.db.ontologies.add([ontology_name])
            full_ontology_filename = os.path.join(processed_ontologies_dir, file)
            self.extract_ontology_categories(ontology_id, full_ontology_filename)

    def copy_replacement_ontologies_kludge(self):
        
            d = datalib.get_location(self.config, 'replacement_ontologies_dir')
            p = self.masterConfig.getProcessedOntologiesDir()
            if os.path.exists(d):
                files = os.listdir(d)
                for f in files:
                    if f.endswith(".annos-filtered.txt"):
                        print "copy kludge: " + os.path.join(d, f) + " " + os.path.join(p, f)
                        shutil.copyfile(os.path.join(d, f), os.path.join(p, f))

    def extract_ontology_categories(self, ontology_id, ontology_file):
        print "extracting terms from ", ontology_file

        for line in open(ontology_file):
            line = line.strip()
            term_name, term_desc = line.split('\t')

            category_id = self.db.ontology_categories.add([ontology_id, term_name, term_desc])
            
    def extract_organisms(self):
        organisms = self.config['Organisms']['organisms']
        for organism in organisms:
            organism_name = self.config[organism]['name']
            short_name = self.config[organism]['short_name']
            common_name = self.config[organism]['common_name']
            short_id = self.config[organism]['short_id']
            organism_id = self.config[organism]['gm_organism_id']
            default_ontology = self.config[organism]['default_ontology']
            taxonomy_id = self.config[organism]['ncbi_taxonomy_id']

            ontology_id = self.db.ontologies.lookup((default_ontology,))

            self.db.organisms.add([short_name, common_name, organism_name, ontology_id, taxonomy_id], id = organism_id)
    
    def extract_networks(self):
        '''
        note that interactions, networks, network_metadata, and network groups are
        triggered by going through this list
        '''
        
        data_dir = datalib.get_location(self.config, 'data_dir')
        #processed_dir = datalib.get_location(self.config, 'processed_network_dir')
        processed_dir = self.config['FileLocations']['processed_network_dir']

        network_cfgs = datalib.load_active_cfgs(self.config, wrap=True)

        total_interactions = 0
        
        for cfg in network_cfgs:
            gse_id = cfg.getGSEID()
            organism = cfg.getOrganismCode()
            organism_short_name = self.config[organism]['short_name']
            organism_id = self.db.organisms.lookup((organism_short_name,))

            if organism_id is None:
                raise Exception("Failed to lookup organism id for %s" % organism)

            print "extracting network " + cfg.config.filename + " organism " + organism
            name = cfg.getName()

            # if we don't have a name, try pulling out an auto-generated name
            if not name:
                name = cfg.getAutoName()

            if name:
                name = name.strip()
                
            description = cfg.getDescription()
            # strip newlines from description
            description = description.replace('\n','')

            group = cfg.getNetworkGroupCode()
            group_name = self.config['NetworkGroups'][group]['name']
            group_code = self.config['NetworkGroups'][group]['code']
            group_description = self.config['NetworkGroups'][group]['description']

            default_selected = cfg.getDefaultSelected()

            # use pre-generated network id
            network_id = cfg.getNetworkId()
            network_id = int(network_id)


            # if there is no processed network file, log and load an empty network. TODO: add tidying step to get rid of such error networks, then add the fatal exception back in here
            try:
                processed_network_filename = cfg.getProcessedNetworkFilename()
                if not processed_network_filename:
                    normalized_network_file = ''
                else:
                    normalized_network_file = os.path.join(os.path.dirname(cfg.config.filename), processed_dir, processed_network_filename) # TODO: tidy up file naming, eg put full paths in cfg, add util function to compute
            except:
                exctype, value = sys.exc_info()[:2]
                print "error getting processed network filename for %s, will load empty network" % cfg.config.filename
                print exctype, value

                processed_network_filename = ''
                normalized_network_file = ''

            num_interactions = self.extract_interactions_for_network(organism_id, network_id, normalized_network_file, self.handle_interactions)

            total_interactions += num_interactions
            print "extracted %s interactions" % num_interactions

            # if we are not in skip interactions mode, we don't expect any 0 interaction counts,
            # so print a message and skip networks that actually have 0 interactions
            if num_interactions == 0:
                print "empty interaction file, not loading %s" % cfg.config.filename
                continue

            # note we lookup/assign a group id only after determining if the
            # network has at least one interaction, so we don't end up creating an
            # empty group
            group_id = self.db.network_groups.lookup((group_name, str(organism_id)))
            if group_id is None:
                group_id = self.db.network_groups.add([group_name, group_code, group_description, str(organism_id)])
            if group_id is None:
                raise Exception("no group id for group '%s' organism %s" % (group, organism_id))

            # add metadata and network records
            source = cfg.getSource()

            # put the geo id into the reference field,
            # otherwise put in the value in subsource if any
            reference = ''
            if source == 'GEO':
                type_ = cfg.getType()
                if type_ == 'gse':
                    reference = cfg.getGSEID()
                elif type_ == 'gds':
                    reference = cfg.getGDSID()
                else:
                    #raise Exception("unexpected type for GEO dataset: ", type_)
                    print "unexpected type for GEO dataset: '%s'. no GEO linkout will be available" % type_
            else:
                subsource = cfg.getSubSource()
                if subsource is None:
                    subsource = ''
                reference = subsource

            #referenceLink = ''
            pubmedId = cfg.getPubmedId()
            #pubmedLink = ''
            
            authors = cfg.getPubmedAuthors()

            if authors: # format into a single string from list
                authors = u', '.join(authors)
            else:
                authors = ''
                
            publicationName = cfg.getPubmedJournal()
            #journalName = cfg.getPubmedJournal()
            yearPublished = cfg.getPubmedDate()
            #dateDownloaded = ''
            processingDescription = cfg.getProcessingType()
            networkType = group_name
            alias = ''
            interactionCount = num_interactions
            dynamicRange = ''
            edgeWeightDistribution = ''
            accessStats = 0
            title = cfg.getPubmedArticle()

            if pubmedId:
                url = PUBMED_URL_PATTERN % pubmedId
            else:
                url = u''
                
            sourceUrl = self.make_source_url(source, reference)

            # build comment from user-entered field & system
            # generated aux description (why couldn't i use consistent and simple naming???)
            comment = cfg.getComment()

            # nothing? need an empty string
            if comment is None:
                comment = u''

            # newlines break the loading, for now just join together
            if comment:
                comment = comment.strip()
                comment_parts = comment.split('\n')
                comment = u' '.join(comment_parts)

            # we may need to join some additional text to the description
            aux_description = cfg.getAuxDescription()
            if aux_description:
                comment = comment + u' ' + aux_description

            # remove newlines
            other = cfg.getKeywords()

            metadata_id = self.db.network_metadata.add([source, reference,
            pubmedId, authors, publicationName, yearPublished,
            #dateDownloaded,
            processingDescription, networkType,
            alias, interactionCount, dynamicRange,
            edgeWeightDistribution, accessStats, comment, other, title, url, sourceUrl])

            self.db.networks.add([name, metadata_id, description, default_selected, group_id], id=network_id)

            # tags
            self.extract_tags_for_network(cfg.config)
        print "extracted a total of %s interactions" % total_interactions
        self.total_interactions = total_interactions

    def make_source_url(self, source, reference):
            urlmap = self.config['DataSources']
            print urlmap
            
            try:
                urls = urlmap[source]
            except KeyError:
                print "unable to compute source url for source '%s', ignoring (consider updating DataSources in db.cfg)" % source
                return u''

            print urls
            if reference and 'ref_url' in urls:
                ref_url = urls['ref_url']
                url = ref_url % reference

            elif 'url' in urls:
                url = urls['url']
            else:
                print "DataSources in db.cfg does not define a url or source  url for source '%s', ignoring" % source
                return u''

            return url
        
    def extract_tags(self):
        '''
        load all the tags in certain column of our spreadsheet dump csv
        into a tags table.

        the parsing here is roughly the same as in gmtags.py,
        TODO: need to consolidate
        '''

        tagfile = datalib.get_location(self.config, 'mesh_to_gmtag_filename')
        reader = csv.reader(open(tagfile, "rb"), delimiter=',')
        header = None

        term_col = 0
        tag_col = 3

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

                # put tag in the db
                for tag in tag_list:
                    # hmm, the spreadsheet has duplicates, lets map to one tag
                    tag_id = self.db.tags.lookup((tag,))
                    if not tag_id:
                        self.db.tags.add([tag])

    def extract_tags_for_network(self, cfg):
        '''
        populate the network tag assoc table, based
        on any tags associated with a network.

        if there is no tags field in the network metadata,
        that's okay just ignore

        but if there is an associated tag we didn't know about
        in our master table, throw an error
        '''

        try:
            tags = cfg['gse']['genemania_tags']
        except KeyError:
            # no tags for this network, ignore
            return

        if not tags:
            return

        network_id = cfg['dataset']['gm_network_id']

        for tag in tags:
            tag_id = self.db.tags.lookup((tag,))
            if not tag_id:
                raise Exception("failed to lookup tag '%s' in tag table" % tag)
            self.db.network_tag_assoc.add([network_id, tag_id])
            
    def extract_gene_naming_sources(self):
        sources = self.config['NamingSources']
        for source in sources:
            name = self.config['NamingSources'][source]['name']
            priority = self.config['NamingSources'][source]['priority']
            short_name = self.config['NamingSources'][source]['short_name']
            self.db.gene_naming_sources.add([name, priority, short_name])


    def extract_genes(self, organism_short_id):
        pass
        #self.parse_mapping(mapping_file, organism_name)


    def extract_nodes_and_gene_data(self):
        organisms = self.config['Organisms']['organisms']
        for organism in organisms:
            organism_name = self.config[organism]['name']
            common_name = self.config[organism]['common_name']
            short_id = self.config[organism]['short_id']

            self.extract_nodes_and_gene_data_for_organism(organism_name, short_id)
        
    def extract_nodes_and_gene_data_for_organism(self, organism_name, organism_short_id):

        #self.parse_mapping()

        raw_mapping_dir = datalib.get_location(self.config, 'raw_mappings_dir')
        processed_mapping_dir = datalib.get_location(self.config, 'processed_mappings_dir')
        
        raw_mapping_file = self.get_raw_mapping_file_for_organism(organism_short_id, raw_mapping_dir)
        processed_mapping_file = self.get_processed_mapping_file_for_organism(organism_short_id, processed_mapping_dir)

        self.parse_node_data(os.path.join(raw_mapping_dir, raw_mapping_file), organism_name, organism_short_id)
        self.parse_gene_data(os.path.join(processed_mapping_dir, processed_mapping_file), organism_name, organism_short_id)

    def extract_interactions_for_network(self, organism_id, network_id, normalized_network_file, handle_interactions):

        num_interactions = 0
        std_filename = '%s.%s' % (organism_id, network_id)
        if handle_interactions == 'skip':
            return 0
        elif handle_interactions == 'count':
            return count_lines(normalized_network_file)
        elif handle_interactions == 'small_tables':
            dir = os.path.join(self.dbdir, 'INTERACTIONS')
            if not os.path.exists(dir):
                os.mkdir(dir)
            new_table =  Table(std_filename, ['ID', 'fromNode', 'toNode', 'weight'], dir, skip_id=True, encoding=None)
        elif handle_interactions == 'big_table':
            new_table = None
            num_interactions = self.db.interactions.size()
        elif handle_interactions == 'copy':
            dir = os.path.join(self.dbdir, 'INTERACTIONS')
            if not os.path.exists(dir):
                os.mkdir(dir)
            std_filename = os.path.join(dir, std_filename + '.txt')
            shutil.copyfile(normalized_network_file, std_filename)
            return count_lines(normalized_network_file)            
        else:
            raise Exception("unexpected interaction handling setting: '%s'" % handle_interactions)

        if normalized_network_file == '':
            print "no normalized network specified, assuming no interactions"
        else:
            for line in open(normalized_network_file, 'r'):
                line = line.strip()
                uid1, uid2, weight = line.split('\t')

                #uid1 = normalize_gmid(uid1)
                #uid2 = normalize_gmid(uid2)

                #id1 = self.db.nodes.lookup((uid1,))
                #id2 = self.db.nodes.lookup((uid2,))

                #if id1 is None:
                #    raise Exception("couldn't find id for symbol '%s'" % uid1)
                #if id2 is None:
                #    raise Exception("couldn't find id for symbol '%s'" % uid2)

                # instead of the lookups commented out from above,
                # we assume that the ids in the network files map
                # directly into database node ids
                id1 = get_id_from_gmid(uid1)
                id2 = get_id_from_gmid(uid2)

                name = 'N/A' # TODO: why is this field here???

                #print id1, id2, uid1, uid2, weight

                # either one big file, or many small ones:
                if handle_interactions == 'big_table':
                    self.db.interactions.add([id1, id2, weight, name, network_id])
                elif handle_interactions == 'small_tables':
                    new_table.add([id1, id2, weight])
            
        if new_table:
            num_interactions = new_table.size()
            new_table.close()
        else:
            num_interactions = self.db.interactions.size() - num_interactions

        return num_interactions

    def get_processed_mapping_file_for_organism(self, organism_short_id, dir):
        mappings = os.listdir(dir)

        for file in mappings:
            if file.startswith('%s_' % organism_short_id):
                return file

        raise Exception("failed to find raw mapping file for %s" % organism_short_id)
        
    def get_raw_mapping_file_for_organism(self, organism_short_id, dir):
        mappings = os.listdir(dir)

        for file in mappings:
            if file.endswith('_%s' % organism_short_id):
                return file

        raise Exception("failed to find raw mapping file for %s" % organism_short_id)

    def parse_node_data(self, mapping_file, organism_name, short_id):
        '''
        Extracts node data from the data warehouse's id mapping files.
        adapted Jason's extract.py
        '''

        organism_id = self.config[short_id]['gm_organism_id']        

        # load enabled biotypes
        biotypes = datalib.get_biotypes(self.config, short_id)
        print "biotypes for organism %s: %s" % (short_id, biotypes)
        
        # TODO: consolidate code for parsing this file, eg see also normalize_mappings.py
        GMID_HEADER = 'GMID'
        PROTEIN_CODING_HEADER = 'Protein Coding'
        DESCRIPTION_HEADER = 'Definition'
        ENTREZ_ID_HEADER = 'Entrez Gene ID'
        ENSEMBL_ID_HEADER = 'Ensembl Gene ID'
        TAIR_LOCUS_ID_HEADER = 'TAIR Locus ID'
        TAIR_NAMING_SOURCE_NAME = 'TAIR ID' # not same as header val as for other columns, historical reasons ...

        # linkout sources
        ENSEMBL_SOURCE_ID = self.db.gene_naming_sources.lookup((ENSEMBL_ID_HEADER,))
        ENTREZ_SOURCE_ID = self.db.gene_naming_sources.lookup((ENTREZ_ID_HEADER,))
        TAIR_SOURCE_ID = self.db.gene_naming_sources.lookup((TAIR_NAMING_SOURCE_NAME,))

        # linkout patterns - the codes here like entrgid are hardcoded, must match the master db.cfg.
        ENTREZ_LINKOUT_PATTERN = self.config['NamingSources']['entrgid']['link']
        ENSEMBL_LINKOUT_PATTERN = self.config['NamingSources']['ensgid']['link']
        TAIR_LINKOUT_PATTERN = self.config['NamingSources']['tairid']['link']

        # figure out columns from file header
        f = codecs.open(mapping_file, 'r', 'utf8')
        header = f.next()
        header = header.strip()
        header_fields = header.split('\t')

        # must have these fields
        GMID_COL = header_fields.index(GMID_HEADER)
        PROTEIN_CODING_COL = header_fields.index(PROTEIN_CODING_HEADER)
        DESCRIPTION_COL = header_fields.index(DESCRIPTION_HEADER)

        # these fields may not be there, depending on the file
        try:
            ENTREZ_ID_COL = header_fields.index(ENTREZ_ID_HEADER)
        except ValueError:
            ENTREZ_ID_COL = None

        try:
            ENSEMBL_ID_COL = header_fields.index(ENSEMBL_ID_HEADER)
        except ValueError:
            ENSEMBL_ID_COL = None

        try:
            TAIR_LOCUS_ID_COL = header_fields.index(TAIR_LOCUS_ID_HEADER)
        except ValueError:
            TAIR_LOCUS_ID_COL = None

        '''
        GMID    Ensembl Gene ID Protein Coding  Gene Name       Ensembl Transcript ID   Ensembl Protein ID
        Uniprot ID      Entrez Gene ID  RefSeq mRNA ID  RefSeq Protein ID       Synonyms        Definition
        '''

        for line in f:
            values = line.rstrip('\r\n').split('\t')
            if len(values) < 2:
                continue

            node_id = int(values[GMID_COL])
            gmid = '%s:%s' % (short_id, node_id) # maybe we can ditch this decoration and just use the integer id's?
            gmid = normalize_gmid(gmid)

            curr_biotype = values[PROTEIN_CODING_COL]
            description = values[DESCRIPTION_COL]


            # ignore biotypes that we're not interested in
            if curr_biotype not in biotypes:
                continue 

            # gene data table needs linkout, populate here:
            linkout_source_id, linkout = extract_linkout(values, ENTREZ_ID_COL, ENSEMBL_ID_COL, TAIR_LOCUS_ID_COL,
                ENTREZ_SOURCE_ID, ENSEMBL_SOURCE_ID, TAIR_SOURCE_ID, organism_name,
                ENTREZ_LINKOUT_PATTERN, ENSEMBL_LINKOUT_PATTERN, TAIR_LINKOUT_PATTERN)
            #print "linkout: %s %s %s" % (linkout_param1, linkout_param2, linkout_source_id)

            gene_data_id = self.db.gene_data.add([description, linkout, linkout_source_id])
            self.db.nodes.add([gmid, gene_data_id, organism_id], id=node_id)

        f.close()

    def parse_gene_data(self, mapping_file, organism_name, organism_short_id):
        '''
        Extracts gene data from the normalized id mapping files.
        adapted rom Jason's extract.py
        '''
        print "loading genes for", organism_name
        
        filename = os.path.split(mapping_file)[-1]
        if '_names' not in filename:
            raise Exception("unexpected filename")

        organism_id = self.config[organism_short_id]['gm_organism_id']
        default_gene_names = self.get_organism_default_gene_names(organism_name)
        
        for line in open(mapping_file, 'r').readlines():
            values = line.strip().split('\t')
            if len(values) < 3:
                print "skipping invalid record in mapping file:", line
                continue

            gmid = values[0]
            gmid = normalize_gmid(gmid)

            node_id = self.db.nodes.lookup((gmid,))

            if node_id is None:
                raise Exception("failed to lookup gmid '%s'" % gmid)

            symbol = values[1]
            #encoding issue below with comparison between symbol and default_gene_names
            if not isinstance(symbol, int):
                symbol = unicode(symbol, "utf8")
            
            naming_source = values[2]
            #Because of repeated issues further down the pipeline - during step 7 and step 8
            # manifests as a missing attribute but after digging deeper is actually from a missing
            # naming source in the GENES.txt file.  This causes issues for attributes as well as 
            # data dumping
            naming_source_id = self.db.gene_naming_sources.lookup((naming_source,))
            if not isinstance(naming_source_id,int):
                print "We are missing the naming source in the config file for %s" % naming_source
                print "Outputting this gene without a naming source WILL cause issues further down the pipeline"
            symbol_type = 'N/A' # TODO: what is this for? obsolete maybe
            if symbol.upper() in default_gene_names:
                print "%s is a default" % symbol
                default_selected = 1
            else:
                default_selected = 0

            self.db.genes.add([symbol, symbol_type, naming_source_id, node_id, organism_id, default_selected])

    def get_organism_default_gene_names(self, organism_name):
        '''
        from config file
        '''

        short_id = datalib.get_short_id_for_organism_name(self.config, organism_name)
        default_genes = self.config['Defaults']['Genes'][short_id]
        return default_genes

def count_lines(filename):
    i=-1 # if no lines in file, we'll return 0
    for i, line in enumerate(open(filename, "r")):
        pass
    return i+1

def normalize_gmid(gmid):
    '''
    messed up the gmids by sometimes including leading zero's as in
    Hs:00002 and sometimes not. This function gets rid of the 0's.
    '''

    org, id = gmid.split(':')
    id = int(id)
    gmid = "%s:%s" % (org, id)

    return gmid

def get_id_from_gmid(gmid):
    org, id = gmid.split(':')
    id = int(id)
    
    return id

def extract_linkout(values, ENTREZ_ID_COL, ENSEMBL_ID_COL, TAIR_LOCUS_ID_COL,
    ENTREZ_SOURCE_ID, ENSEMBL_SOURCE_ID, TAIR_SOURCE_ID, organism_name,
    ENTREZ_LINKOUT_PATTERN, ENSEMBL_LINKOUT_PATTERN, TAIR_LINKOUT_PATTERN):
    '''
    specialized logic to determine linkout sources. outputs the tuple:

           linkout_source_id, linkout

    basic logic is to extract the lowest-numbered entrez gene id if there is
    one ignoring those that start with '1000'. otherwise lookup ensembl id,
    and if that still is not found then look for a tair id.
    
    TODO: too many args to this function, reorganize
    '''

    if ENTREZ_ID_COL is not None:
        entrez_ids = values[ENTREZ_ID_COL]
        if entrez_ids != '':
            entrez_ids = entrez_ids.split(';')
            entrez_ids.sort()

            # get rid of ids 'N/A'
            entrez_ids = [id for id in entrez_ids if id != 'N/A']

            # we prefer to ignore gene ids starting with 1000 (but why? ...
            # there's a missing backstory to this)
            filtered = []
            for id in entrez_ids:
                if not id.startswith('1000'):
                    filtered.append(id)

            if len(filtered) > 0:
                entrez_id = filtered[0]
                linkout = ENTREZ_LINKOUT_PATTERN.replace('${1}', entrez_id)
                return ENTREZ_SOURCE_ID, linkout
            elif len(entrez_ids) > 0:
                entrez_id = entrez_ids[0]
                linkout = ENTREZ_LINKOUT_PATTERN.replace('${1}', entrez_id)
                return ENTREZ_SOURCE_ID, linkout

    if ENSEMBL_ID_COL is not None:
        ensembl_id = values[ENSEMBL_ID_COL] # should only ever be one
        if ensembl_id != '' and ensembl_id != 'N/A':
            organism_name = organism_name.replace(' ', '_') # ensembl likes organism names with underscore between genus & species
            linkout = ENSEMBL_LINKOUT_PATTERN.replace('${1}', ensembl_id)
            linkout = linkout.replace('${2}', organism_name)
            return ENSEMBL_SOURCE_ID, linkout

    if TAIR_LOCUS_ID_COL is not None:
        tair_id = values[TAIR_LOCUS_ID_COL]
        if tair_id != '':
            linkout = TAIR_LINKOUT_PATTERN.replace('${1}', tair_id)
            return TAIR_SOURCE_ID, linkout

    # the genemania common module has its own linkout generation code, this may be unneeded now. 
    # TODO remove after verifying. for now try returning empty link if generation fails, instead of
    # blowing up.    
#    raise Exception('unable to determine linkout for %s raw mapping fields: %s' % (organism_name, values))
    print 'unable to determine linkout for %s raw mapping fields: %s, returning empty linkout' % (organism_name, values)
    return '','' 

def process(config, handle_interactions):
    extractor = Extractor(config, handle_interactions = handle_interactions)
    extractor.extract()
    extractor.close()

def main(args):
    '''arg processing
    '''

    usage = "usage: %prog [options] master_config_file.cfg"
    description = "extract metadata to generic db"
    parser = OptionParser(usage=usage, description=description)

    parser.add_option('-i', '--interactions',
        help='handle interactions as big_table, small_tables, count or skip',
        type='string', dest='handle_interactions', default='small_tables')
    
    (options, args) = parser.parse_args(args)

    if len(args) != 1:
        parser.error("require one master config file")

    config_file = args[0]

    handle_interactions = options.handle_interactions
    if not handle_interactions in ['big_table', 'small_tables', 'count', 'skip', 'copy']:
        parser.error('handle_interactions must be big_table, small_tables, count, skip, or copy')
    
    config = datalib.load_main_config(config_file)

    process(config, handle_interactions)

if __name__ == '__main__':
    main(sys.argv[1:])
