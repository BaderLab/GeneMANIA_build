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



import sys, datalib, csv, os
from optparse import OptionParser


def process(config, filters, test=False, filename=None):

    if filters:
        network_cfgs = datalib.get_filtered_configs(config, filters)
    else:
        masterConfig = datalib.MasterConfig(config.filename)

        if filename: # fastpath for single unfiltered file
            network_cfgs = [datalib.load_cfg(filename)]
        else:
            network_cfgs = datalib.load_cfgs(masterConfig.getDataDir())


    for cfg in network_cfgs:
        # copy the cfg file itself, and all the networks it refers to
        src = cfg.filename

        # if a particular filename was given, check for it
        if filename:
            if filename != cfg.filename:
                continue

        try:
            del_data_file(os.path.dirname(cfg.filename),
                config['FileLocations']['raw_dir'],
                cfg['gse']['raw_data'], test=test)
        except KeyError:
            pass

        try:
            del_data_file(os.path.dirname(cfg.filename),
                config['FileLocations']['profile_dir'],
                cfg['gse']['annotated_profile'], test=test)
        except KeyError:
            pass

        try:
            del_data_file(os.path.dirname(cfg.filename),
                config['FileLocations']['network_dir'],
                cfg['gse']['network'], test=test)
        except KeyError:
            pass

        try:
            del_data_file(os.path.dirname(cfg.filename),
                config['FileLocations']['processed_network_dir'],
                cfg['gse']['processed_network'], test=test)
        except KeyError:
            pass

        del_data_file(os.path.dirname(cfg.filename), '',
            os.path.basename(cfg.filename), test=test)


def del_data_file(src_dir, sub_dir, filename, test=False):
    src = os.path.join(src_dir, sub_dir, filename)

    if not os.path.exists(src):
        print "no such file, skipping: %s" % src
        return

    if test:
        print "would delete %s" % (src)
    else:
        print "deleting %s" % (src)
        os.remove(src)

def main(args):
    usage = "usage: %prog [options] master_config_file.cfg target_dir -f filter_expression -f ..."
    "-s set_expressions -s ..."
    description = "delete network metadata files and associated data sets"
    parser = OptionParser(usage=usage, description=description)

    parser.add_option('-f', '--filter',
    help='network metadata filter expression',
    action='append', type='string', dest='filter')

    parser.add_option('-t', '--test',
    help='test mode, print what would be updated without saving the result',
    action="store_true", dest="test", default=False)

    parser.add_option('-l', '--filename',
    help='restrict update to the named network metadata file',
    action="store", type='string', dest='filename')


    (options, args) = parser.parse_args(args)

    if len(args) != 1:
        parser.error("require master config file")

    config_file = args[0]

    filter_params = options.filter
    if filter_params:
        filters = [param.split('=') for param in filter_params]
    else:
        filters = []

    config = datalib.load_main_config(config_file)

    process(config, filters, test=options.test, filename=options.filename)


if __name__ == '__main__':
    main(sys.argv[1:])
