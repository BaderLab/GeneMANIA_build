'''
Ontology diff
'''

import sqlite3, os
import utils

class OntologyDiff(utils.Db):
    def __init__(self, conn, org_name):
        super(OntologyDiff, self).__init__(conn)
        self.org_name = org_name

    def diff(self, olddb = 'old', newdb = 'new'):
        '''
        return a dictionary containing report data comparing two
        versions of an organisms ontology (gene annotation) data
        '''
        
        d = {'name': self.org_name}
                
        if olddb:
            d['old'] = self.stats(olddb)
        else:
            d['old'] = None
            
        if newdb:
            d['new'] = self.stats(newdb)
        else:
            d['new'] = None

        print(d)
        return d
    
    def stats(self, db):               
        d = {}
        
        # number genes with an annotation
        sqlGeneAnnoCounts = "select count(distinct(Node_ID)) from %s.gene_annos where Annotations > 0" % db                
        d['gene_anno_counts'] = self.selectNumber(sqlGeneAnnoCounts)
                                   
        # number of categories with an annotation
        sqlCatAnnoCounts = "select count(distinct(Category_ID)) from %s.category_annos where Annotations > 0" % db
        d['cat_anno_counts'] = self.selectNumber(sqlCatAnnoCounts)
            
        # what fraction of genes for which we have interactions do we also
        # have annotation data?
        numIneractingGenes = self.selectNumber("select count(distinct(Node_ID)) from %s.degrees where degree > 0" % db)
        d['annotated_pct'] = d['gene_anno_counts']*100.0/numIneractingGenes
                        
        # genes with annotations but no interactions?
        sql = "select count(distinct(Node_ID)) from %s.gene_annos where Node_ID not in (select Node_ID from %s.degrees)" % (db, db)
        d['genes_with_annos_without_interactions'] = self.selectNumber(sql)
       
        return d

def process(conn):
    diff = OntologyDiff(conn, "test org")
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
