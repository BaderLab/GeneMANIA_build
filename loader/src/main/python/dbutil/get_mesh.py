#!/usr/bin/env python
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

# -*- coding: UTF-8 -*-

'''
load mesh descriptors for each data descriptor from pubmed
'''

import sys, urllib2, os, time
import xml.etree.ElementTree as et
import datalib

# secs to sleep between queries, to be nice to server
SLEEP_TIME = 1

# this is configured based on the global config
PMED_CACHE_DIR = None

pubmed_url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?id=%s&db=pubmed&retmode=xml'

def get_tree_for_pmid(pmid):
    #url = pubmed_url % pmid
    #feed = urllib2.urlopen(url)
    
    filename = get_xml(pmid)
    tree = et.parse(open(filename, 'r'))

    return tree

def setup_cachedir(config):
    '''
    put in a subdir of the folder containing the config
    '''

    global PMED_CACHE_DIR
    PMED_CACHE_DIR = datalib.get_location(config, 'pubmed_cache_dir')

    if not os.path.exists(PMED_CACHE_DIR):
        os.mkdir(PMED_CACHE_DIR)

def get_xml(pmid):
    '''get from cache, or download if not already there
    '''
    
    filename = os.path.join(PMED_CACHE_DIR, '%s.xml' % pmid)
    
    if not os.path.exists(filename):
        print "fetching %s" % pmid
        filename = download_xml(pmid)
    else:
        print "already cached %s" % pmid

    return filename

def download_xml(pmid):
    '''pull in the pmed xml into our local cache folder
    '''

    # this little sleep is in here to be at least a little
    # nice to the servers when making lots of requests
    time.sleep(SLEEP_TIME)

    url = pubmed_url % pmid
    feed = urllib2.urlopen(url)
    data = feed.read()

    filename = os.path.join(PMED_CACHE_DIR, '%s.xml' % pmid)
    file = open(filename, 'w')
    file.write(data)
    file.close()

    return filename



def get_all_mesh_descriptors(tree):
    root = tree.getroot()

    descriptors = root.findall('.//MeshHeading/DescriptorName')

    descriptors = [d.text for d in descriptors]
    return  descriptors

def get_pmed_authors(tree):
    root = tree.getroot()

    authors = root.findall('.//Author')
    author_names = []
    for author in authors:
        #author_name = "%s, %s %s" % (author.findtext('./LastName'), author.findtext('./ForeName'), author.findtext('./Initials'))
        #author_names.append(author_name)

        # last name only for now. note its possible that instead of an individual
        # author name we have an entry under a CollectiveName tag with value such as
        # "Genomics of Pediatric SIRS/Septic Shock Investigators". we'll ignore those.
        name = author.findtext('./LastName')
        if name is not None:
            author_names.append(name)

    return author_names

def get_pmed_year(tree):
    root = tree.getroot()

    pubdate = root.find('.//PubDate')
    if not pubdate:
        print "couldn't find pubdate"
        #return 'UnknownDate'
        return None
    try:
        pmed_year, pmed_month, pmed_day = pubdate.findtext('./Year'), pubdate.findtext('./Month'), pubdate.findtext('./Day')
        
        # sometimes the extraction of year succeeds but its empty (eg pmed: 10214908), raise
        # an exception explicitly to trigger the medline date fallback
        if not pmed_year:
            raise Exception("no year")
        
    except:    
        medline_date = pubdate.findtext('./MedlineDate')
        # lets hope this is consistent
        pmed_year = medline_date.split(' ')[0]

    return pmed_year

def get_pmed_journal(tree):
    root = tree.getroot()
    
    journal = root.findtext('.//Journal/Title')
    #short_journal = root.findtext('.//Journal/ISOAbbreviation')
    short_journal = root.findtext('.//MedlineJournalInfo/MedlineTA')
    
    return journal, short_journal

def get_pmed_article(tree):
    root = tree.getroot()

    article = root.findtext('.//ArticleTitle')

    return article

def main(config):
    '''
    read in all the cfg files in dir, extract the pubmed id, 
    fetch the corresponding mesh descriptors, and update the config file
    '''

    data_dir = datalib.get_location(config, 'data_dir')

    # setup the cache dir
    setup_cachedir(config)

    network_cfgs = datalib.load_cfgs(data_dir)
    for cfg in network_cfgs:
        try:
            pmid = cfg['gse']['pubmed_id']

            if not pmid:
                print "no pubmed id for %s, skipping" % cfg.filename
                continue
            else:
                print "fetch pubmed info for %s" % cfg.filename

            tree = get_tree_for_pmid(pmid)

            descriptors = get_all_mesh_descriptors(tree)
            if descriptors:
                cfg['gse']['mesh_descriptors'] = descriptors
            else:
                cfg['gse']['mesh_descriptors'] = ''

            pmed_article = get_pmed_article(tree)
            if pmed_article:
                cfg['gse']['pubmed_article'] = pmed_article
            else:
                cfg['gse']['pubmed_article'] = ''

            pmed_journal, pmed_journal_shortname = get_pmed_journal(tree)

            if pmed_journal:
                cfg['gse']['pubmed_journal'] = pmed_journal
            else:
                cfg['gse']['pubmed_journal'] = ''

            if pmed_journal_shortname:
                cfg['gse']['pubmed_journal_shortname'] = pmed_journal_shortname
            else:
                cfg['gse']['pubmed_journal_shortname'] = ''

            pmed_authors = get_pmed_authors(tree)
            cfg['gse']['pubmed_authors'] = pmed_authors

            pmed_year = get_pmed_year(tree)
            if pmed_year:
                cfg['gse']['pubmed_year'] = pmed_year
            else:
                cfg['gse']['pubmed_year'] = ''

            cfg.write()
        except:
            exctype, value = sys.exc_info()[:2]
            print "error processing %s" % cfg.filename
            print exctype, value


def test():
    tree = get_tree_for_pmid(18688027)
    desc = get_all_mesh_descriptors(tree)

    print desc 

if __name__ == '__main__':
    #test()

    config_file = sys.argv[1]
    config = datalib.load_main_config(config_file)
    main(config)
