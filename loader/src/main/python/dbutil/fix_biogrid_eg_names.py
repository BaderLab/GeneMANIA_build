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
biogrid files seem to have an EG prefix in front of all
the ensemble gene ids. remove this so that our naming files
will properly map the ids
"""
import sys, os, shutil, datalib


def main(config, short_id, cfg_filename):
    '''
    read in all the cfg files in dir, extract the pubmed id,
    fetch the corresponding mesh descriptors, and update the config file
    '''

    data_dir = datalib.get_location(config, 'data_dir')
    #network_dir = datalib.get_location(config, 'network_dir')
    network_dir = config['FileLocations']['network_dir']
    #processed_network_dir = datalib.get_location(config, 'processed_network_dir')
    processed_network_dir = config['FileLocations']['processed_network_dir']
    nn_cmd = config['Tools']['nn_cmd']
    processed_mapping_dir = datalib.get_location(config, 'processed_mappings_dir')
    #processed_mapping_dir = config['FileLocations']['processed_mappings_dir']

    if not short_id:
        network_cfgs = datalib.load_cfgs(data_dir)
    else:
        network_cfgs = [datalib.load_cfg(os.path.join(data_dir, short_id, cfg_filename))]

    for cfg in network_cfgs:
        try:
            if cfg['dataset']['source'] == 'BIOGRID':
                print "processing", cfg.filename
                fix_eg(network_dir, cfg)
        except KeyError, e:
            print "skipping %s" % cfg.filename

def fix_eg(network_dir, cfg):
    network_file = cfg['gse']['network']
    network_file = os.path.join(os.path.dirname(cfg.filename), network_dir, network_file)
    newfilename = "tmp.txt"
    try:
        os.remove(newfilename)
    except OSError:
        pass
    newfile = open(newfilename, 'w')
    for line in open(network_file, 'r'):
        line = line.strip()
        parts = line.split('\t')
        if parts[0].startswith('EG'):
            parts[0] = parts[0][2:]
        if parts[1].startswith('EG'):
            parts[1] = parts[1][2:]
        newline = '\t'.join(parts) + '\n'
        #print line
        #print newline
        newfile.write(newline)
    newfile.close()

    os.remove(network_file)
    shutil.copyfile(newfilename, network_file)
    os.remove(newfilename)
        
if __name__ == '__main__':

    config_file = sys.argv[1]

    # optionally take a single organism short id and cfg name to process
    if len(sys.argv) > 2:
        short_id = sys.argv[2]
        cfg_filename = sys.argv[3]
    else:
        short_id = None
        cfg_filename = None

    config = datalib.load_main_config(config_file)

    main(config, short_id, cfg_filename)
