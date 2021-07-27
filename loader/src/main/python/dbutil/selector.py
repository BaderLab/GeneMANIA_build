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


import sys, datalib, csv
from optparse import OptionParser

def print_header(fields):
    record = ['filename']
    if fields:
        record = record + fields

    print_record(record)

def print_cfg_as_record(cfg, fields):
    record = [cfg.filename]
    if fields:
        record = record + [datalib.lookup_field(cfg, field) for field in fields]

    print_record(record)

def print_record(record):
    print '\t'.join(record).encode('utf8')

def process(config, query_fields):
    '''
    create a table by querying all the configs.
    guess this proves i shoulda used a db to
    start with <sigh>.

    output to stdout, problems to stderr

    here's an example:

    python selector.py geo.cfg dataset.organism gse.platforms gse.gse_id
    gse.pubmed_id gse.num_samples gse.pubmed_journal gse.pubmed_year
    gse.pubmed_authors gse.genemania_tags gse.pubmed_authors[0]
    gse.pubmed_authors[-1] > report.txt
    '''

    data_dir = datalib.get_location(config, 'data_dir')
    network_cfgs = datalib.load_cfgs(data_dir)

    print_header(query_fields)
    for cfg in network_cfgs:
        #print cfg.filename
        #pmed_authors = cfg['gse']['pubmed_authors']
        print_cfg_as_record(cfg, query_fields)

def main(args):
    config_file = args[0]
    if len(args) > 1:
        query_fields = args[1:]
    else:
        query_fields = None

    config = datalib.load_main_config(config_file)
    process(config, query_fields)

if __name__ == '__main__':
    main(sys.argv[1:])
