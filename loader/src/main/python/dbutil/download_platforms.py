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


import datalib, geolib, sys, os

def main(config, force=False):
    '''
    read in all the cfg files in dir, extract the pubmed id,
    fetch the corresponding mesh descriptors, and update the config file
    '''

    platform_dir = datalib.get_location(config, 'platform_data_dir')
    if not os.path.exists(platform_dir):
            os.mkdir(platform_dir)
            
    organisms = config['Organisms']['organisms']
    
    for organism in organisms:
        print "retrieving platforms for %s" % organism
        retrieved = []
        platforms_for_organism = config[organism]['platforms']
        for platform in platforms_for_organism:
            ok = retrieve_platform(platform, platform_dir, force=force)
            if ok:
                retrieved.append(platform)
        config[organism]['retrieved_platforms'] = retrieved
        config.write()
        
    """
    ok = retrieved_platforms = set()
    
    for platform in all_platforms:
        retrieve_platform(platform, force=force)
        
        if not force and os.path.exists(os.path.join(platform_dir, geolib.get_platform_filename_for_id(platform))):
            print "skipping %s, already exists" % platform
            continue

        try:
            platform_file = geolib.get_platform_annotation(platform, platform_dir)
        except:
            exctype, value = sys.exc_info()[:2]
            print "failed to download platform annotation file for %s, cause:\n%s %s" % (platform, exctype, value)
            platform_file = ''

        # decompress
        if platform_file.endswith('.gz'):
            platform_file = datalib.gunzip(os.path.join(platform_dir, platform_file))
            
        print 'downloaded', platform_file
    """
def retrieve_platform(platform, platform_dir, force=False):
    if not force and os.path.exists(os.path.join(platform_dir, geolib.get_platform_filename_for_id(platform))):
        print "skipping %s, already exists" % platform
        return True

    try:
        platform_file = geolib.get_platform_annotation(platform, platform_dir)
        if platform_file.endswith('.gz'):
            platform_file = datalib.gunzip(os.path.join(platform_dir, platform_file))
        print 'downloaded', platform_file
        return True
    except:
        exctype, value = sys.exc_info()[:2]
        print "failed to download platform annotation file for %s, cause:\n%s %s" % (platform, exctype, value)
        platform_file = ''
        return False

    raise Exception("how did we get here?")

if __name__ == '__main__':

    config_file = sys.argv[1]
    config = datalib.load_main_config(config_file)

    force_download = False
    if len(sys.argv) > 2:
        if sys.argv[2] == 'force':
            force_download = True
        else:
            raise Exception('unepxected cmd')

    main(config, force_download)
