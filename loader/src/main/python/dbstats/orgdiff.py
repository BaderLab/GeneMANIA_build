'''
Ontology diff
'''

import sqlite3, os
import utils

class OrgDiff(utils.Db):
    def __init__(self, conn, org_name):
        super(OrgDiff, self).__init__(conn)
        self.org_name = org_name

    def diff(self, olddb = 'old', newdb = 'new'):
        '''
        return a dictionary containing simple top-level 
        summary data on networks, identifiers, annotations
        
        TODO: there's some duplication in sql queries between here and
        the detailed stats for the different data types (networks, identifiers), 
        should consolidate
        '''
        
        d = {'name': self.org_name}

        if olddb:
            d['old'] = self.orgstats(olddb)
        else:
            d['old'] = None
        
        if newdb:    
            d['new'] = self.orgstats(newdb)
        else:
            d['new'] = None

        print(d)
        return d
    
    def orgstats(self, dbname):
        '''
        return a dictionary containing simple top-level 
        summary data on networks, identifiers, annotations
        
        TODO: there's some duplication in sql queries between here and
        the detailed stats for the different data types (networks, identifiers), 
        should consolidate
        '''
        
        d = {'name': self.org_name}
        
        # number networks
        sqlNumNetworks = "select count(distinct(Network_ID)) from %s.networks;" % dbname                
        d['numNetworks'] = self.selectNumber(sqlNumNetworks)
        
        # number interactions
        sqlNumInteractions = "select sum(num_edges) from %s.networks;" % dbname # equivalently, could do "select sum(interactors)/2 from %s.degrees;"
        d['numInteractions'] = self.selectNumber(sqlNumInteractions)
        
        # number of unique genes
        sqlNumGenes = "select count(distinct(Node_ID)) from %s.identifiers;" % dbname
        d['numGenes'] = self.selectNumber(sqlNumGenes)
                
        # number recognized symbols
        sqlNumSymbols = "select count(distinct(Symbol)) from %s.identifiers;" % dbname
        d['numSymbols'] = self.selectNumber(sqlNumSymbols)
        
        # number of genes with interactions
        sqlNumInteractingGenes = "select count(distinct(Node_ID)) from %s.degrees where degree > 0;" % dbname
        d['numInteractingGenes'] = self.selectNumber(sqlNumInteractingGenes)
        
        # number genes with an annotation
        sqlGeneAnnoCounts = "select count(distinct(Node_ID)) from %s.gene_annos where Annotations > 0;" % dbname                
        d['numGeneAnnoCounts'] = self.selectNumber(sqlGeneAnnoCounts)
        
        # number of categories with an annotation
        sqlCatAnnoCounts = "select count(distinct(Category_ID)) from %s.category_annos where Annotations > 0;" % dbname
        d['numCatAnnoCounts'] = self.selectNumber(sqlCatAnnoCounts)
        
        # some fractions
        d['ratioInteractingGenes'] = d['numInteractingGenes'] * 1. / d['numGenes']
        d['ratioAnnotatedGenes'] = d['numGeneAnnoCounts'] * 1. / d['numGenes']
        print(d)
        return d
    
        
        
def process(conn):
    diff = OrgDiff(conn, "test org")
    diff.diff()

def test():
    statsdbname = os.path.join(os.getenv("HOME"), "tmp", "S. cerevisiae_statsdb.sqlite")
    main(statsdbname)

def main(statsdbname):

    conn = sqlite3.connect(statsdbname)
    conn.row_factory = sqlite3.Row   
    try: 
        process(conn)
    finally:
        conn.close()

if __name__ == '__main__':
    test()
