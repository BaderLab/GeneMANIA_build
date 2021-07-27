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


import sys
import geolib, datalib
from configobj import ConfigObj

def main(config, organism_short_id = None, gse_id = None, pubmed_id = None):

    if gse_id is not None:
        geolib.identify_given_series(config, organism_short_id, gse_id, pubmed_id)
    else:
        # select series by heuristic
        cfgs = geolib.identify_series(config)
        datalib.save_cfgs(cfgs)
        
        # extra series specified directly in the config
        geolib.identify_extra_series(config) 

if __name__ == '__main__':
    '''
    first arg is master config file,
    second, optional arg, is organism short id (eg At for Arabidopsis thaliana),
    third, optional arg, is a gse id,
    fourth, optional arg, is a pubmed id

    with one arg, all candidate series are 
    automatically identified

    with the two or three or four arg versions, only a
    default series file with the given id is created
    '''

    config_file = sys.argv[1]
    config = datalib.load_main_config(config_file)

    organism_short_id = None
    gse_id = None
    pubmed_id = None

    try:
        organism_short_id = sys.argv[2]
        gse_id = sys.argv[3]
        pubmed_id = sys.argv[4]
    except:
        pass

    main(config, organism_short_id, gse_id, pubmed_id)
