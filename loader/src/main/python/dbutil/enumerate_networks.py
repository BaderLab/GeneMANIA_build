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

import sys, datalib

def main(config, mode, verbose=False):
    '''
    Its actually helpful to assign each network an id before 
    loading (eg in the extract script). So we can build cache files identified
    by id without loading interactions into the db, or so we can reload the data
    but ensure network number hasn't changed so we don't have to rebuid the cache.

    mode = [check|clear|enumerate]
    '''

    data_dir = datalib.get_location(config, 'data_dir')
    network_cfgs = datalib.load_cfgs(data_dir)

    total = 0
    num_enumerated = 0

    for cfg in network_cfgs:
        total += 1

        if mode == 'check':
            num_enumerated += check(cfg)
        elif mode == 'clear':
            clear(cfg)
        elif mode == 'enumerate':
            enumerate(cfg, total)
        else:
            raise Exception('unkown mode: %s' % mode)

    if mode == 'check':
        print "total=%s, enumerated=%s, not-enumerated=%s" % (total, num_enumerated, total - num_enumerated)

def check(cfg):
    try:
        id = cfg['dataset']['gm_network_id']
        if id == 'NA':
            return 0
        else:
            return 1
    except KeyError:
        return 0

def clear(cfg):
    cfg['dataset']['gm_network_id'] = 'NA'
    cfg.write()

def enumerate(cfg, id):
    cfg['dataset']['gm_network_id'] = id
    cfg.write()

if __name__ == "__main__":

    config_file = sys.argv[1]
    mode = sys.argv[2]

    config = datalib.load_main_config(config_file)
    main(config, mode)
