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

import sys, re, os, codecs
from optparse import OptionParser
import datalib

trna_pattern = re.compile('^t[A-Z]\([AUCGX]{3,3}\)[\w_-]+$') # 't' followed by one capital letter, then an '(', exactly 3 bases, ')', and then any sequence of alphanumerics or underscore or hyphen
snrna_pattern = re.compile('^snR[\w_-]+$')  # 'snR' followed by any sequence of alphanumerics or underscore or hyphen
ncrna_pattern = re.compile('^[0-9_]+S_rRNA$') # some digits followed by the pattern 'S_rRNA', which is apparently some other non-coding rna
internal_whitespace_pattern = re.compile('\S+\s+') # whitespace after some non-whitespace chars
mirna_pattern = re.compile('^[a-zA-Z]{3,3}-[mM][iI][rR]-[\w-]+$') # 
numeric_pattern = re.compile('^\d+$') # only digits, one or more
smells_like_rna_pattern = re.compile('rna', re.IGNORECASE)
unusual_chars_pattern = re.compile('[^\w-]')

bad_patterns = [(internal_whitespace_pattern, "contains whitespace")]
suspicious_patterns = [(smells_like_rna_pattern, 'contains the term rna'), (unusual_chars_pattern, 'contains non-alphanumeric characters'),
                (trna_pattern, "tRNA"), (snrna_pattern, "snRNA"), (ncrna_pattern, "non-coding RNA"), 
                (mirna_pattern, "micro RNA")]



class NameSys:
    ''' some rules
        - if a synonym collides with another synonym, then they are both removed, and
          the name added to the synonym-blacklist, so any more occurances of
          that synonym are also removed
        - if a synonym collides with a non-synonym, the synonym is removed but the
          non-synonym remains. 
        - if two non-synonyms collide, they are both removed, and added to the
          non-synonym-blacklist so future occurances can also be removed

    '''
    def __init__(self, prefix, logfilename):
        self.prefix = prefix
        self.name_map = {} # {normalized_name: (uid, name, source, is_synonym)} map, used for detection of duplicates
        self.blacklisted_synonym_names = {}
        self.blacklisted_nonsynonym_names = {}

        self.logfilename = logfilename
        self.logfile = open(logfilename, 'w')
        
    def close(self):
        self.logfile.close()

    def is_name_okay(self, id, name, name_type=None):
        for pattern, reason in bad_patterns:
            if pattern.match(name):
                self.log(id, name, name_type, 'rejected', 'matched pattern: %s' % reason)
                return False
        return True

    def is_name_suspicious(self, id, name, name_type=None):
        for pattern, reason in suspicious_patterns:
            if pattern.match(name):
                self.log(id, name, name_type, 'warning', 'matched pattern: %s' % reason)
                return False
        return True

    # should probably learn to use the logging package, but anyway ...
    def log(self, id, name, name_type, action, details):
        self.logfile.write("%s\t%s\t%s\t%s\t%s\n" % (id, name, name_type, action, details))

    def add(self, id, name, name_type, pure_numeric_allowed, synonym_priority):

        # get rid of empties
        if not name:
            return

        name = name.strip()

        if not name:
            return

        # hmm, we have fields nested within fields in the input, and the subfields can be quoted!
        # strip them out here for now, maybe use a csv reader for the subfield parsing later?
        if name[0] == '"' and name[-1] == '"' and len(name) > 1:
            name = name[1:-1]

        # special code for empty field ... no-one would be so malicious as to create a gene
        # with an identifier of 'N/A' ... would they?
        if name == 'N/A':  
            return

        # do some pattern-filtering & logging
        if not self.is_name_okay(id, name, name_type):
            return

        self.is_name_suspicious(id, name, name_type) # ignore result for now, this will just end up logging it

        if not pure_numeric_allowed:
            if numeric_pattern.match(name):
                self.log(id, name, name_type, 'rejected', 'pure numeric not allowed for %s' % name_type)
        
        # our identifier deduplication
        normalized_name = self.normalize(name)
        if synonym_priority:
            if normalized_name in self.blacklisted_synonym_names:
                rec = self.blacklisted_synonym_names[normalized_name]
                prev_id, prev_name, prev_name_type, prev_synonym_priority = rec
                self.log(id, name, name_type, 'rejected', 'synonym has already been blacklisted (%s)' % prev_id)
                return
            elif normalized_name in self.blacklisted_nonsynonym_names:
                rec = self.blacklisted_nonsynonym_names[normalized_name]
                prev_id, prev_name, prev_name_type, prev_synonym_priority = rec
                self.log(id, name, name_type, 'rejected', 'synonym collides with blacklisted non-synonym (%s) ' % prev_id)
                return
            else:
                # look into the names we've already accepted
                if normalized_name in self.name_map:
                    rec = self.name_map[normalized_name]
                    prev_id, prev_name, prev_name_type, prev_synonym_priority = rec
                    if id == prev_id:
                        # name collision with the same id, that's okay, just ignore
                        return
                    else:
                        # name collision with different id ... need to figure if previous entry was
                        # also a synonym to handle correctly
                        if prev_synonym_priority:
                            self.log(id, name, name_type, 'rejected', 'matched synonym name used by a different gene (%s), blacklisting this synonym' % (prev_id))
                            self.blacklisted_synonym_names[normalized_name] = rec
                            del self.name_map[normalized_name]
                            return
                        else:
                            self.log(id, name, name_type, 'rejected', 'matched non-synonym name used by a different gene (%s), rejecting this synonym' % (prev_id))
                            return
                else: # okay, it wasn't already there, add it in
                    rec = (id, name, name_type, synonym_priority)
                    self.name_map[normalized_name] = rec
                    return
        else:  # non-synonym
            if normalized_name in self.blacklisted_nonsynonym_names:
                rec = self.blacklisted_nonsynonym_names[normalized_name]
                prev_id, prev_name, prev_name_type, prev_synonym_priority = rec
                aux_msg = self.check_sources_different(prev_name_type, name_type)
                self.log(id, name, name_type, 'rejected', 'non-synonym collides with blacklisted non-synonym (%s). %s' % (prev_id, aux_msg))
                return
            else:
                if normalized_name in self.name_map:
                    rec = self.name_map[normalized_name]
                    prev_id, prev_name, prev_name_type, prev_synonym_priority = rec
                    if id == prev_id:
                        # name collision with the same id, that's okay, just ignore
                        return
                    else:
                        # name collision with different id ... need to figure if previous entry was
                        # also a synonym to handle correctly
                        if prev_synonym_priority:
                            del self.name_map[normalized_name]
                            self.log(prev_id, prev_name, prev_name_type, 'rejected', 'synonym matched non-synonym name used by a different gene (%s), removing that synonym' % (id))
                            rec = (id, name, name_type, synonym_priority)
                            self.name_map[normalized_name] = rec
                            return
                        else:
                            aux_msg = self.check_sources_different(prev_name_type, name_type)
                            self.log(id, name, name_type, 'rejected', 'non-synonym matched non-synonym name used by a different gene (%s), blacklisting this non-synonym. %s' % (prev_id, aux_msg))
                            self.blacklisted_nonsynonym_names[normalized_name] = rec
                            del self.name_map[normalized_name]
                            return
                else: # okay, it wasn't already there, add it in
                    rec = (id, name, name_type, synonym_priority)
                    self.name_map[normalized_name] = rec

    def check_sources_different(self, source1, source2):
        if source1 == source2:
            return ''
        else:
            return "and the sources don't match!!! (%s, %s)" % (source1, source2)

    def make_uid(self, id):
        name = "%s:%s" % (self.prefix, str(id).rjust(5,'0'))
        return name

    def write(self, outfile, sep_char = '\t'):
        '''produce output file data, this is small
        enough to do in memory
        '''
        all_lines = []
        for name in self.name_map:
            rec = self.name_map[name]
            id = rec[0]
            uid = self.make_uid(id)
            rec = (uid,) + rec[1:-1] 
            line = sep_char.join(str(item) for item in rec)
            all_lines.append(line)

        all_lines.sort()
        #print '\n'.join(all_lines)
        for line in all_lines:
            outfile.write(line + '\n')

    def normalize(self, name):
        return name.lower()

# each entry is a tuple of (HEADER_NAME, INTERNAL_NAME, USE_FLAG, MULTI_FIELD_SEP, PURE_NUMERIC_ALLOWED, SYNONYM_PRIORITY)
# hmmm, added enough fields to this tuple that it probably should be made a class (named tuple would work, do we have
# those yet?)
expected_headers = [
    ('GMID', 'GMID', False, None, False, False),
    ('Ensembl Gene ID', 'Ensembl Gene ID', True, None, False, False),
    ('Protein Coding', 'Protein Coding', False, None, False, False),
    ('Ensembl Gene Name', 'Ensembl Gene Name', True, None, False, False),
    ('Ensembl Transcript ID', 'Ensembl Transcript ID', False, ';', False, False),
    ('Ensembl Protein ID', 'Ensembl Protein ID', True, ';', False, False),
    ('Uniprot ID', 'Uniprot ID', True, ';', False, False),
    ('Entrez Gene ID', 'Entrez Gene ID', True, ';', True, False),
    ('RefSeq mRNA ID', 'RefSeq mRNA ID', True, ';', False, False),
    ('RefSeq Protein ID', 'RefSeq Protein ID', True, ';', False, False),
    ('Ensembl Definition', 'Ensembl Definition', False, None, False, False),
    ('Entrez Gene Name', 'Entrez Gene Name', True, None, False, False),
    ('TAIR Locus ID', 'TAIR ID', True, ';', False, False),
    ('Entrez Definition', 'Entrez Definition', False, None, False, False),
    ('Synonyms', 'Synonym', True, ';', False, True),
    ]

def dictify_row(header, row):
    d = {}
    for name, value in zip(header, row):
        d[name] = value
        
    return d

def update_header(header, org_prefix):
    '''
    this hack to work around changes in the header format,
    it used to distinguish between entrez and ensembl gene names
    but no longer does. workaround for now is organism specific, until
    we figure out if we need to distinguish downtream or not. TODO
    Update (jan 2011) we no longer need the organism specific workaround
    for arabidopsis, but we'll keep the Gene Name -> Ensembl Gene Name
    remapping for now, until we can be sure that other code doesn't
    depend on this identifier type.
    '''

    new_header = []
    for item in header:
        if item == 'Gene Name':
            item = 'Ensembl Gene Name'
        new_header.append(item)

    return new_header

def myreader(file, delim):
    '''
    return parsed rows
    '''
    for l in file:
        l = l.strip()
        parts = l.split(delim)
        yield parts


def read_generic_dw_idmapping_file(filename, org_prefix, logfilename, biotypes):
    '''read and parse an id mapping file, producing a name mapping object.
    Each row in the file is a unique gene, we use the value in the column 'GMID'
    to identify the gene internally.
    '''

    f = codecs.open(filename, "r", "utf8")
    header = None

    namesys = NameSys(org_prefix, logfilename)

    for rownum, row in enumerate(myreader(f, '\t')):
        if not header: 
            header = row
            # this next bit is because the header format changed
            header = update_header(header, org_prefix)
        else:
            d = dictify_row(header,row)

            gmid = d['GMID']

            # "Protein Coding" is the column header of the ID mapping file - should really be changed to Biotype at some point
            curr_biotype = d['Protein Coding']

            # the ID mapping file sets Uniprot ID protein coding fields to "True" instead of "protein_coding". This causes the filter
            # to skip these if the user filters for biotype "protein_coding" but not for "True", so we convert biotype instances of 
            # "True" to "protein_coding":
            if curr_biotype == "True":
                curr_biotype = "protein_coding"

            if biotypes and curr_biotype not in biotypes:
                #print "skipping biotype:", curr_biotype
                continue

            #print "processing biotype:", curr_biotype
            for header_name, internal_name, use_flag, multi_field_sep, numeric_allowed, syn_priority in expected_headers:
                if not use_flag:
                    continue

                try:
                    field = d[header_name]
                except KeyError:
                    continue

                if field:
                    field.strip()

                if not field:
                    continue

                if multi_field_sep:
                    fields = field.split(multi_field_sep)
                else:
                    fields = [field] # wrap in a list for consistency

                for field in fields:
                    namesys.add(gmid, field, internal_name, pure_numeric_allowed = numeric_allowed, synonym_priority = syn_priority)

    #namesys.write()
    return namesys

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

def process_mapping(org_prefix, raw_file, normalized_file, log_file, biotypes):
    '''
    normalize mappings from the given raw file into the specified
    output file.
    '''

    namesys = read_generic_dw_idmapping_file(raw_file, org_prefix, log_file, biotypes)

    outfile = open(normalized_file, 'w')
    namesys.write(outfile)
    outfile.close()
    namesys.close()

    
def process(config, biotypes):

    raw = get_raw_files(config.getRawMappingDir())

    for org_prefix, raw_file in raw:
        normalized_file, log_file = make_new_filenames(org_prefix, config.getProcessedMappingDir())
        print org_prefix, raw_file, normalized_file, log_file

        process_mapping(org_prefix, raw_file, normalized_file, log_file, biotypes)


def main(args):
    '''extract args and execute
    normalization
    '''

    usage = "usage: %prog [options] master_config_file.cfg"
    description = "normalize raw mapping files"
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-n", "--non_protein_coding", help="include non-protein coding genes", 
        default="False", action="store_true") 

    parser.add_option('-b', '--biotypes',
        help="comma separated values of biotypes: Mt_rRNA Mt_tRNA miRNA " + \
        "misc_RNA protein_coding pseudogene rRNA retrotransposed snRNA snoRNA")   

    (options, args) = parser.parse_args(args)

    if len(args) != 1:
        parser.error("require one master config file")

    print "Process non-protein-coding genes:", options.non_protein_coding

    biotypes = None
    if options.biotypes:
        biotypes = options.biotypes.split(",")
        print "Biotypes:", biotypes

    config_file = args[0]
    config = datalib.MasterConfig(config_file)
    process(config, biotypes)
    
if __name__ == '__main__':
    main(sys.argv[1:])

