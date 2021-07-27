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


import os, sys, shutil
import datalib, geolib

def main(config, force=False):
    '''
    read in all the cfg files in dir, extract the pubmed id,
    fetch the corresponding mesh descriptors, and update the config file

    if force=True, it will re-download all the files, otherwise
    the script checks if the file already exists locally and only
    download's it if needed

    if the download fails for some reason, move the corresponding cfg
    to a rejected folder
    '''

    data_dir = datalib.get_location(config, 'data_dir')
    raw_dir = config['FileLocations']['raw_dir']
    rejected_dir = os.path.join(os.path.dirname(config.filename), 'rejected')
    if not os.path.isdir(rejected_dir):
        os.mkdir(rejected_dir)
    
    network_cfgs = datalib.load_cfgs(data_dir)
    for cfg in network_cfgs:
        if cfg['dataset']['source'] != 'GEO' and cfg['dataset']['type'] != 'gse':
            continue
            
        gse_id = cfg['gse']['gse_id']
        print "gse_id from config:",gse_id
        # put the series matrix in the subdir specified by raw_dir under the
        # the same location as the cfg, and update the config with this info

        dir = os.path.dirname(cfg.filename)
        dir = os.path.join(dir, raw_dir)
        if not os.path.exists(dir):
            os.mkdir(dir)
                    
        # skip download if not in force download mode, and
        # the file already exists locally
        if not force and check_local(dir, cfg):
            print "skipping download for %s, raw data already exists" % gse_id
            
            #we still  need to put the file specification into the cfg file though
            #breaks downstream if we skip that.
            cfg['gse']['raw_data'] = cfg['gse']['gse_id'] + "_series_matrix.txt"
            cfg['gse']['raw_type'] = 'unannotated_profile'
            cfg.write()
            continue

        # if the download fails, skip on to the next one, setting the file name
        # for the failed download to empty
        try:
            series_file = geolib.get_series_matrix(gse_id, dir)
            # decompress
            if series_file.endswith('.gz'):
                series_file = datalib.gunzip(os.path.join(dir, series_file))
                series_file = os.path.basename(series_file)

            cfg['gse']['raw_data'] = series_file
            cfg['gse']['raw_type'] = 'unannotated_profile'

            cfg.write()
        except:
            exctype, value = sys.exc_info()[:2]
            print "failed to download series matrix file for %s, cause:\n%s %s" % (gse_id, exctype, value)
            print "moving cfg to rejected folder"
            shutil.move(cfg.filename, os.path.join(rejected_dir,
                os.path.basename(cfg.filename)))
            
def check_local(raw_dir, cfg):
    try:
        #some/most of the files don't seem to have the raw_data file
        # name specified and eventhough the file is there
        # it is re-downloading it and the download takes a long time. 
        series_file = cfg['gse']['gse_id'] + "_series_matrix.txt"
        #series_file = cfg['gse']['raw_data']
    except KeyError:
        return False

    series_file = os.path.join(raw_dir, series_file)

    if series_file.endswith('.gz'):
        series_file = series_file[:-3]

    print "checking %s" % series_file
    if os.path.isfile(series_file):
        return True
    else:
        return False


if __name__ == '__main__':

    config_file = sys.argv[1]
    config = datalib.load_main_config(config_file)

    if len(sys.argv) > 2:
        force_download = sys.argv[2]
        if force_download == 'force':
             force_download == True
        else:
             raise Exception('unexpected command')
    else:
        force_download = False

    main(config, force_download)
