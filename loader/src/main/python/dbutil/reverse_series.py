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


"""
create a set of series config files from the current
genemania database. To be used as part of a transition,
hopefully only once.
"""

import datalib, geolib, csv, sys, os
import MySQLdb
from MySQLdb.cursors import SSCursor  # streaming

dbhost = 'server4'
dbport = 3307
dbname = 'genemania_big'
dbuser = 'genemania'
dbpw = 'password' # i said, stop lauging

db = MySQLdb.connect(host=dbhost,
        port = dbport,
		user=dbuser,
		passwd=dbpw,
		db=dbname,
        charset='utf8',
        )

DEBUG = 1

def get_organisms():
    sql = """select organisms.id, organisms.name
    from organisms
    order by organisms.id asc"""

    records = exec_query(sql)
    return records

def get_networks(organism_id):
    sql = """select network_groups.name, networks.id, networks.name, networks.description, networks.default_selected+0
    from organisms, network_groups, networks
    where organisms.id = %s 
    and network_groups.organism_id = organisms.id
    and networks.group_id = network_groups.id
    order by networks.id asc""" % organism_id

    records = exec_query(sql)
    return records

def exec_query(sql):
    if DEBUG:
        print '============'
        print sql

    cursor = db.cursor()
    cursor.execute(sql)
    records = cursor.fetchall()
    cursor.close()

    if DEBUG:
        for record in records:
            print record

    return records

def dump_network_data(id, filename):
    sql = """
          select nodes1.name as u1, nodes2.name as u2,
          interactions.weight
          from interactions, nodes as nodes1, nodes as nodes2
          where interactions.network_id = %s
          and interactions.fromNode = nodes1.id
          and interactions.toNode = nodes2.id
          """
    sql = sql % id
    cursor = SSCursor(db)
    cursor.execute(sql)

    print "dumping %s" % filename

    f = open(filename, 'wb')
    while 1:
        record = cursor.fetchone()
        if record == None:
            break
        full_rec = list(str(i) for i in record)
        line = '\t'.join(full_rec) + '\n'
        f.write(line)

    f.close()

def make_config(config, organism_name, record):

    data_dir = datalib.get_location(config, 'data_dir')
    processed_network_dir = datalib.get_location(config, 'processed_network_dir')

    # look up organism in config
    short_id = datalib.get_short_id_for_organism_name(config, organism_name)
    
    # look up network group in config to make sure its there
    group_name = record[0]
    group_code = datalib.get_group_code_from_group_name(config, group_name)


    network_id = record[1]
    network_name = record[2]
    network_desc = record[3]
    default_selected = record[4]

    cfg_name = '%s.cfg' % network_id
    # build config
    
    cfg = datalib.make_empty_config()

    dir = os.path.join(data_dir, short_id)
    if not os.path.exists(dir):
        os.mkdir(dir)

    cfg.filename = os.path.join(dir, cfg_name)
    network_data_filename = '%s-interactions.txt' % network_id
    
    cfg['dataset'] = {}
    cfg['dataset']['type'] = 'import'
    cfg['dataset']['group'] = group_code
    cfg['dataset']['organism'] = organism_name
    cfg['dataset']['default_selected'] = default_selected
    cfg['dataset']['name'] = network_name
    cfg['dataset']['description'] = network_desc
    cfg['gse'] = {}
    cfg['gse']['gse_id'] = 'N/A'
    cfg['gse']['title'] = 'N/A'
    cfg['gse']['contributor'] = 'N/A'
    cfg['gse']['pubmed_id'] = 'N/A'
    cfg['gse']['num_samples'] = 0
    cfg['gse']['platforms'] = ['N/A']

    dir = os.path.join(os.path.dirname(cfg.filename), processed_network_dir)
    if not os.path.exists(dir):
        os.mkdir(dir)

    cfg['gse']['processed_network'] = network_data_filename
    cfg.write()

    fullname = os.path.join(dir, network_data_filename)
    dump_network_data(network_id, fullname)


def make_all_configs(config, organism_name, records):

    for record in records:
        make_config(config, organism_name, record)

if __name__ == "__main__":

    config_file = sys.argv[1]
    config = datalib.load_main_config(config_file)

    organisms = get_organisms()

    for organism_id, organism_name in organisms:
        networks = get_networks(organism_id)
        make_all_configs(config, organism_name, networks)
    
