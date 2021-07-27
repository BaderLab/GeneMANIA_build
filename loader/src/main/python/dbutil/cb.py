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


import sys, os, datalib


def make_cb_exec_cmd(cmd, network_cache_dir, generic_db_dir):
    '''
    any interpolation to build up the cmd ... nothing yet!
    '''

    return cmd % (network_cache_dir, network_cache_dir, os.path.join(generic_db_dir, 'INTERACTIONS'))

def run_job(cmd):
    '''
    use some job control system to submit jobs. for now we
    just execute directly. should be using subprocess here?
    '''
    print cmd
    os.system(cmd)

def main(config):
    '''
    build cache from a db
    '''

    network_cache_dir = datalib.get_location(config, 'network_cache_dir')
    generic_db_dir = datalib.get_location(config, 'generic_db_dir')

    cb_cmd = config['Tools']['cb_cmd']
    cmd = make_cb_exec_cmd(cb_cmd, network_cache_dir, generic_db_dir)
    run_job(cmd)

if __name__ == '__main__':

    config_file = sys.argv[1]
    config = datalib.load_main_config(config_file)
    main(config)
