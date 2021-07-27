import os.path
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



import sys, datalib, csv, os, shutil
from optparse import OptionParser


def process(config, target_dir, filters, test=False):

    if filters:
        network_cfgs = datalib.get_filtered_configs(config, filters)
    else:
        masterConfig = datalib.MasterConfig(config.filename)
        data_dir = masterConfig.getDataDir()
        network_cfgs = datalib.load_cfgs(masterConfig.getDataDir())

    for cfg in network_cfgs:            
        # copy the cfg file itself, and all the networks it refers to
        src = cfg.filename
        dst = os.path.join(target_dir, os.path.basename(cfg.filename))
        print src, dst
        #os.copyfile(cfg.filename, os.path.join(target_dir, os.path.basename(cfg.filename)))
        #os.copyfile()
        '''
        profile_dir = config['FileLocations']['profile_dir']
        profile_file = cfg['gse']['annotated_profile']
        rel_file = os.path.join(profile_dir, profile_file)
        profile_file = os.path.join(os.path.dirname(cfg.filename), rel_file)

        src = profile_file
        dst = os.path.join(target_dir, rel_file)
        print src, dst
        '''

        copy_data_file(os.path.dirname(cfg.filename), '',
            os.path.basename(cfg.filename), target_dir, test=test)
            
        try:
            copy_data_file(os.path.dirname(cfg.filename),
                config['FileLocations']['raw_dir'],
                cfg['gse']['raw_data'], target_dir, test=test)
        except KeyError:
            pass

        try:
            copy_data_file(os.path.dirname(cfg.filename),
                config['FileLocations']['profile_dir'],
                cfg['gse']['annotated_profile'], target_dir, test=test)
        except KeyError:
            pass

        try:
            copy_data_file(os.path.dirname(cfg.filename),
                config['FileLocations']['network_dir'],
                cfg['gse']['network'], target_dir, test=test)
        except KeyError:
            pass

        try:
            copy_data_file(os.path.dirname(cfg.filename),
                config['FileLocations']['processed_network_dir'],
                cfg['gse']['processed_network'], target_dir, test=test)
        except KeyError:
            pass

def copy_data_file(src_dir, sub_dir, filename, target_dir, test=False):
    src = os.path.join(src_dir, sub_dir, filename)
    dst = os.path.join(target_dir, sub_dir, filename)
    if not os.path.exists(src):
        print "no such file, skipping: %s" % src
        return
        
    if test:
        print "would copy %s to %s" % (src, dst)
    else:
        print "copying %s to %s" % (src, dst)
        if not os.path.isdir(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        shutil.copyfile(src, dst)

def main(args):
    usage = "usage: %prog [options] master_config_file.cfg target_dir -f filter_expression -f ..."
    "-s set_expressions -s ..."
    description = "export a network metadata file and associated data sets to a given filesystem location"
    parser = OptionParser(usage=usage, description=description)

    parser.add_option('-f', '--filter',
    help='network metadata filter expression',
    action='append', type='string', dest='filter')

    parser.add_option('-t', '--test',
    help='test mode, print what would be updated without saving the result',
    action="store_true", dest="test", default=False)


    (options, args) = parser.parse_args(args)

    if len(args) != 2:
        parser.error("require master config file and target dir")

    config_file = args[0]
    target_dir = args[1]

    filter_params = options.filter
    if filter_params:
        filters = [param.split('=') for param in filter_params]
    else:
        filters = []

    config = datalib.load_main_config(config_file)

    process(config, target_dir, filters, test=options.test)


if __name__ == '__main__':
    main(sys.argv[1:])
