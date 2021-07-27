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

import os.path

# based on GEOmetadb, see
# http://gbnci.abcc.ncifcrf.gov/geo/geo_help.php
#

# TODO: count platforms, organisms associated with a series

import sys, os, sqlite3, ftplib
from configobj import ConfigObj
import datalib

# subdir under 'data' in which to gather all
# the organism specific geo data, or '' if just
# gathering everything under 'data'
GEO_DATA_SUBDIR = 'geo'

# get db_row from http://opensource.theopalgroup.com/
import db_row

# series family files
# eg ftp://ftp.ncbi.nih.gov/pub/geo/DATA/SOFT/by_series/GSE3806/GSE3806_family.soft.gz
GSE_DOWNLOAD_HOST = 'ftp.ncbi.nih.gov'
GSE_DOWNLOAD_DIR = '/geo/series/%snnn/%s/soft'
GSE_DOWNLOAD_FILE = '%s_family.soft.gz'

# series matrix files
# eg ftp://ftp.ncbi.nih.gov/pub/geo/DATA/SeriesMatrix/GSE1110/GSE1110_series_matrix.txt.gz
GSEMATRIX_DOWNLOAD_HOST = 'ftp.ncbi.nih.gov'
GSEMATRIX_DOWNLOAD_DIR = '/geo/series/%snnn/%s/matrix'
GSEMATRIX_DOWNLOAD_FILE = '%s_series_matrix.txt.gz'

# platform annotation files
# eg ftp://ftp.ncbi.nih.gov/pub/geo/DATA/annotation/platforms/GPL570.annot.gz
GPL_DOWNLOAD_HOST = 'ftp.ncbi.nih.gov'
GPL_DOWNLOAD_DIR = '/geo/platforms/%snnn/%s/annot'
GPL_DOWNLOAD_FILE = '%s.annot.gz'

select_count_gsm = '''
select series_id, count(gsm.gsm) from gsm
where gsm.gpl = 'GPL198'
group by series_id
'''

def get_platform_filename_for_id(gpl):
    return '%s.annot' % gpl

def get_series_family(gse, dir):
    '''given a series id, download the correspondonding family file into dir
    '''


    '''for most of the gse file names you take off the last 3 characters in order to get
    the directory name.  if the file name has less than 7 characters though you just
    grab the first three characters.
    '''
    gse_dir = gse[ 0 : -3 ] if len(gse) > 6 else gse[ 0 : 3 ]

    download_dir = GSE_DOWNLOAD_DIR % (gse_dir ,gse)
    download_file = GSE_DOWNLOAD_FILE % gse

    f = ftplib.FTP(GSE_DOWNLOAD_HOST, 'anonymous', '')
    print download_dir
    f.cwd(download_dir)
    print download_file
    f.retrbinary("RETR %s" % download_file, open('%s/%s' % (dir, download_file), "wb").write)
    f.close()

    return download_file


def get_series_matrix(gse, dir):
    '''given a series id, download the correspondonding series matrix file into dir
    '''
    
    '''for most of the gse file names you take off the last 3 characters in order to get
    the directory name.  if the file name has less than 7 characters though you just
    grab the first three characters.
    '''
    gse_dir = gse[ 0 : -3 ] if len(gse) > 6 else gse[ 0 : 3 ]

    download_dir = GSEMATRIX_DOWNLOAD_DIR % (gse_dir , gse)
    download_file = GSEMATRIX_DOWNLOAD_FILE % gse

    f = ftplib.FTP(GSE_DOWNLOAD_HOST, 'anonymous', '')
    print download_dir
    f.cwd(download_dir)
    print download_file
    f.retrbinary("RETR %s" % download_file, open('%s/%s' % (dir, download_file), "wb").write)
    f.close()

    return download_file

def get_platform_annotation(gpl, dir):
    '''given a platform id, download the correspondonding annotation file into dir
    '''
    
    '''for most of the gse file names you take off the last 3 characters in order to get
    the directory name.  if the file name has less than 7 characters though you just
    grab the first three characters.
    '''
    gpl_dir = gpl[ 0 : -3 ] if len(gpl) > 6 else gpl[ 0 : 3 ]

    download_dir = GPL_DOWNLOAD_DIR % (gpl_dir, gpl)
    download_file = GPL_DOWNLOAD_FILE % gpl

    f = ftplib.FTP(GPL_DOWNLOAD_HOST, 'anonymous', '')
    print download_dir
    f.cwd(download_dir)
    print download_file
    f.retrbinary("RETR %s" % download_file, open('%s/%s' % (dir, download_file), "wb").write)
    f.close()

    return download_file

class GeoQuery(object):
    '''
    queries against a geo sqlite db
    '''
    
    def __init__(self, db_filename):
        self.db_filename = db_filename
        self.connection = sqlite3.connect(db_filename)
        # some of the geo metadata claims to be utf-8 but doesn't seem to be able to
        # be decoded as such, so explicitly replace those chars with the utf8 unknown
        # char symbol
        self.connection.text_factory = lambda x: unicode(x, 'utf8', errors='replace') 
        self.cursor = self.connection.cursor()

    def exec_query(self, sql):
        '''
        utility function to return list of Row objects given a sql query
        '''

        self.cursor.execute(sql)
        R = db_row.IMetaRow(self.cursor.description)
        results = [R(row) for row in self.cursor.fetchall()]
        return results

    def get_metainfo(self):
        '''
        db metainfo includes a build_date, useful to log for tracing future oddities
        '''
        
        sql = "select name, value from metaInfo;"
        results = self.exec_query(sql)
        return results
        
    def get_series_for_platform(self, gpl):
        select_total_gse_sql = '''
            select gse.gse, gse.title, gse.pubmed_id, gse.contributor
            from gse, gse_gpl, gpl
            where gse_gpl.gse = gse.gse
            and gse_gpl.gpl = gpl.gpl
            and gpl.gpl = '%s'
            '''
        sql = select_total_gse_sql % gpl
        results = self.exec_query(sql)
        c = len(results)

        select_total_gse_sql_with_pmid = '''
            select gse.gse, gse.title, gse.pubmed_id, gse.contributor
            from gse, gse_gpl, gpl
            where gse.pubmed_id is not null
            and gse_gpl.gse = gse.gse
            and gse_gpl.gpl = gpl.gpl
            and gpl.gpl = '%s'
            '''

        sql = select_total_gse_sql_with_pmid % gpl

        results = self.exec_query(sql)
        c_pmid = len(results)
        for row in self.cursor:
            c_pmid += 1
            #print repr(row).encode('utf-8')
        #print "totals", gpl, c, c_pmid
        totals = [gpl, c, c_pmid]
        return totals, results

    def get_series_info(self, gse_id):
        sql = """
        select gse.gse, gse.title, gse.pubmed_id, gse.contributor
        from gse
        where gse.gse = '%s'
        """

        sql = sql % gse_id

        results = self.exec_query(sql)
        return results
  
    def get_platform_info(self, gpl):
        sql = "select gpl, title, organism from gpl where gpl.gpl = '%s'" % gpl

        results = self.exec_query(sql)

        if len(results) > 1:
            raise Exception('multiple entries for the same platform!')

        if results:
            return results[0]
        else:
            return None

    def get_samples_for_series(self, gse):
        sql = '''select gsm.gsm, gsm.title, gsm.description, gsm.organism_ch1, gsm.organism_ch2
                 from gse_gsm, gsm
                 where gse_gsm.gse = '%s'
                 and gse_gsm.gsm = gsm.gsm
              ''' % gse

        return self.exec_query(sql)

    def get_distinct_platforms_for_series(self,gse):
        sql = '''select distinct(gpl.gpl)
                 from gse_gpl, gse, gpl
                 where gse.gse = '%s'
                 and gse_gpl.gse = gse.gse
                 and gse_gpl.gpl = gpl.gpl
              ''' % gse

        return self.exec_query(sql)

    def get_distinct_organisms_for_series(self, gse):
        '''check organisms associated with all samples
           in the series
        '''

        organisms = set()

        sql = '''select distinct(gsm.organism_ch1) as organism_name
                 from gse_gsm, gsm
                 where gse_gsm.gse = '%s'
                 and gse_gsm.gsm = gsm.gsm
                 and gsm.organism_ch1 is not null
              ''' % gse

        self.cursor.execute(sql)
        for row in self.cursor:
            if row[0]:
                organisms.add(row[0])

        sql = '''select distinct(gsm.organism_ch2) as organism_name
                 from gse_gsm, gsm
                 where gse_gsm.gse = '%s'
                 and gse_gsm.gsm = gsm.gsm
                 and gsm.organism_ch2 is not null
              ''' % gse

        self.cursor.execute(sql)
        for row in self.cursor:
            if row[0]:
                organisms.add(row[0])

        return list(organisms)

    def get_top_platforms(self, organism):
        sql = '''
        select gpl.organism,  gpl.gpl, count(gpl.gpl), gpl.title
        from gse, gse_gpl, gpl
        where gse.gse = gse_gpl.gse
        and gse_gpl.gpl = gpl.gpl
        and gpl.organism = '%s'
        group by gpl.gpl
        having count(gpl.gpl) > 5
        order by count(gpl.gpl) desc
        '''

        raise NotImplementedError
 
def seriesmatrix_to_annotatedprofile(seriesmatrix_file, annot_file, target_file):
    raise Exception('Not Implemented')

def identify_series(config, details = False):
    '''
    identify series to download, based on organisms
    of interest, platforms, cutoff for number of samples.
    
    return a list of individual config objects, one for each
    series selected. the config objects are not written.
    '''
    
    organisms = config['Organisms']['organisms']
    dbname = datalib.get_location(config, 'geo_metadb_name')

    print dbname
    geoquery = GeoQuery(dbname)
    
    metainfo = geoquery.get_metainfo()
    tab_print(0, metainfo)
        
    identified_series = []

    for organism in organisms:
        organism_name = config[organism]['name']
        common_name = config[organism]['common_name']
        short_id = config[organism]['short_id']
        tab_print(0, [organism, common_name])
        #platforms = config[organism]['platforms']
        platforms = config[organism]['retrieved_platforms']
        min_samples = int(config[organism]['min_samples_per_series'])

        for platform in platforms:
            platform_info = geoquery.get_platform_info(platform)
            totals_for_platform, series_list = geoquery.get_series_for_platform(platform)
            tab_print(2, platform_info, totals_for_platform)

            for series_info in series_list:
                gse = series_info['gse']
                samples_list = geoquery.get_samples_for_series(gse)
                platforms_for_series_list = geoquery.get_distinct_platforms_for_series(gse)
                organisms_list = geoquery.get_distinct_organisms_for_series(gse)
                tab_print(4, series_info, [len(samples_list), len(platforms_for_series_list), len(organisms_list)])
                if (len(organisms_list) == 1 and len(platforms_for_series_list) == 1 and len(samples_list) >= min_samples):
                    gpl = platforms_for_series_list[0]['gpl']
                    seriescfg = make_geo_series_cfg(config, gse, organism_name, short_id, series_info, platforms_for_series_list, len(samples_list))
                    identified_series.append(seriescfg)

                if details:
                    for sample_info in samples_list:
                        tab_print(6, sample_info)

    return identified_series

def make_geo_series_cfg(config, cfg_filename, organism_name, short_id, series_info, platforms, num_samples):
    data_dir = datalib.get_location(config, 'data_dir')
    
    # create each series cfg as a ConfigObj
    seriescfg = ConfigObj(encoding='utf8')

    dir = os.path.join(data_dir, GEO_DATA_SUBDIR, short_id)
    if not os.path.exists(dir):
        os.mkdir(dir)

    seriescfg.filename = os.path.join(dir, '%s.cfg' % cfg_filename)

    seriescfg['dataset'] = {}
    seriescfg['dataset']['source'] = 'GEO'
    seriescfg['dataset']['type'] = 'gse'
    seriescfg['dataset']['group'] = 'coexp'
    seriescfg['dataset']['organism'] = short_id
    seriescfg['dataset']['default_selected'] = 0
    seriescfg['dataset']['name'] = ''
    seriescfg['dataset']['description'] = ''
    seriescfg['dataset']['processing_type'] =  'Pearson correlation'
    seriescfg['gse'] = {}
    seriescfg['gse']['gse_id'] = series_info['gse']
    seriescfg['gse']['title'] = series_info['title']
    seriescfg['gse']['contributor'] = series_info['contributor']
    seriescfg['gse']['pubmed_id'] = series_info['pubmed_id']
    seriescfg['gse']['num_samples'] = num_samples
    seriescfg['gse']['platforms'] = ','.join((i['gpl'] for i in platforms))

    #seriescfg.write()
    return seriescfg

def identify_extra_series(config):
    '''
    create metadata entries for geo gse series specified in the config file
    '''
    
    organisms = config['Organisms']['organisms']
    dbname = datalib.get_location(config, 'geo_metadb_name')

    print dbname
    geoquery = GeoQuery(dbname)

    for organism in organisms:
        organism_name = config[organism]['name']
        common_name = config[organism]['common_name']
        short_id = config[organism]['short_id']
        tab_print(0, ["extra series"])
        tab_print(2, [organism, common_name])
        
        try:
            gse_list = config[organism]['extra_gse']
        except KeyError:
            gse_list = []
            
        for gse_id in gse_list:
            series_infos = geoquery.get_series_info(gse_id)

            if len(series_infos) > 1:
                raise Exception("multiple series returned for the given id!")
            elif len(series_infos) == 0:
                print "series not found: ", gse_id
                continue 
        
            series_info = series_infos[0]
            tab_print(4, [gse_id])
       
            samples_list = geoquery.get_samples_for_series(gse_id)            
            platforms = geoquery.get_distinct_platforms_for_series(gse_id)        
            seriescfg = make_geo_series_cfg(config, gse_id, organism_name, short_id, series_info, platforms, len(samples_list))
        
            seriescfg.write()            
    
def identify_given_series(config, organism_short_id, gse_id, pubmed_id = None):
    '''create a metadata entry for the given geo gse id (with the optional
    given pubmed id, in case its missing from the geo metadata).
    '''
    dbname = datalib.get_location(config, 'geo_metadb_name')
    geoquery = GeoQuery(dbname)


    organism_name = config[organism_short_id]['name']
    
    series_infos = geoquery.get_series_info(gse_id)
    if len(series_infos) > 1:
        raise Exception("multiple series returned for the given id!")
    elif len(series_infos) == 0:
        raise Exception("series not found")

    series_info = series_infos[0]

    # if we were given a specific pubmed id (sometimes GEO series are published
    # but the pubmed id field in GEO does not get updated), then set to
    # the given value
    if pubmed_id is not None:
        series_info['pubmed_id'] = pubmed_id

    # get platforms
    platforms = geoquery.get_distinct_platforms_for_series(gse_id)

    #seriescfg = make_geo_series_cfg(config, gse_id, organism_name, organism_short_id, series_info, [{'gpl':'N/A'}], 0)
    seriescfg = make_geo_series_cfg(config, gse_id, organism_name, organism_short_id, series_info, platforms, 0)

    seriescfg.write()

    return seriescfg
    
def tab_print(indent, *recs):
    '''print indent tabs followed by tab seperated fields of rec'''
    
    # look, i can do perl in python
    all_fields = [repr(field) for rec in recs if rec for field in rec if field]

    line = '\t'*indent + '\t'.join(all_fields)
    print line

if __name__ == '__main__':
    config_file = sys.argv[1]
    config = ConfigObj(config_file)

    cfgs = identify_series(config)
    datalib.save_cfgs(cfgs)
