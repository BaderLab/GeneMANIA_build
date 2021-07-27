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


import sys, datalib, csv
from optparse import OptionParser


# the filtering here needs cleanup, the filename & collection should be used
# when loading the configs, with the filter tests applied to the result, TODO.
def process(config, filters, setters, exec_exprs=None, test=False, collection_filter=None, filename=None):

    masterConfig = datalib.MasterConfig(config.filename)
    data_dir = masterConfig.getDataDir()
    if filters:
        network_cfgs = datalib.get_filtered_configs(config, filters)
    else:
        if filename: # fastpath for single unfiltered file
            network_cfgs = [datalib.load_cfg(filename)]
        else:
            network_cfgs = datalib.load_cfgs(masterConfig.getDataDir())

    for cfg in network_cfgs:

        # if a particular filename was given, check for it
        if filename:
            if filename != cfg.filename:
                continue

        # if a collection was specified, check we are in it
        if collection_filter:
            collection_dir = datalib.get_data_collection(data_dir, cfg.filename)
            print "filter %s, collection %s" % (collection_filter, collection_dir)
            if collection_filter != collection_dir:
                print "skipping %s, not in desired collection" % cfg.filename
                continue

        if test:
            print "test mode for %s" % cfg.filename
        else:
            print "updating %s" % cfg.filename

        if setters:
            for field, value in setters:
                expr = '%s=%s' % (field, value)
                print '  ', expr
                datalib.set_field(cfg, field, value)

        if exec_exprs:
            for expr in exec_exprs:
                print "exec-ing: %s" % (expr)
                exec(expr)

        if not test:
            cfg.write()
 
def main(args):
    usage = "usage: %prog [options] master_config_file.cfg -f filter_expression -f ..."
    "-s set_expressions -s ..."
    description = "convert profiles to networks"
    parser = OptionParser(usage=usage, description=description)

    parser.add_option('-f', '--filter',
    help='network metadata filter expression',
    action='append', type='string', dest='filter')

    parser.add_option('-s', '--set',
    help='network metadata set expression, but must be a configobj expression like data.source=geo',
    action='append', type='string', dest='set_expr')

    parser.add_option('-t', '--test',
    help='test mode, print what would be updated without saving the result',
    action="store_true", dest="test", default=False)

    parser.add_option('-e', '--exec',
    help='evil exec mode, will exec the given statement with var name cfg for the cfg, security risk',
    action='append', type='string', dest='exec_exprs')

    parser.add_option('-c', '--collection',
    help='restrict update to configurations falling within the given named collection, eg geo or biogrid_direct',
    action="store", dest="collection")

    parser.add_option('-l', '--filename', 
    help='restrict update to the named network metadata file',
    action="store", type='string', dest='filename')

    (options, args) = parser.parse_args(args)

    if len(args) != 1:
        parser.error("require one master config file")

    config_file = args[0]

    filter_params = options.filter
    if filter_params:
        filters = [param.split('=') for param in filter_params]
    else:
        filters = []
        
    set_params = options.set_expr
    if set_params:
        setters = [param.split('=') for param in set_params]
    else:
        setters = []

    exec_exprs = options.exec_exprs
    
    config = datalib.load_main_config(config_file)

    process(config, filters, setters, exec_exprs=exec_exprs, test=options.test,
        collection_filter=options.collection, filename=options.filename)


if __name__ == '__main__':
    main(sys.argv[1:])
