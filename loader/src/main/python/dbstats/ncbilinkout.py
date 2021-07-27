'''
build ncbi linkouts

query summary sqlite databases created by buildstatsdb, and
generate linkout xml files per organism suitable to upload
to ncbi for generation of linkouts to genemania
  
  python ncbilinkout.py /path/to/rXby_summary_folder output_xml_dir
  
deeplinks are only created for genes that have positive degree.

'''

import sqlite3, os, sys
import utils, buildstatsdb

class EntrezIdentifiers(utils.Db):
    def __init__(self, conn, tax_id):
        super(EntrezIdentifiers, self).__init__(conn)
        self.tax_id = tax_id

    def getEntrezIdsWithNonzeroDegree(self):
        '''
        description is in the name
        '''
        
        # add in some index
        sqlIndex = '''
        create index if not exists ix_identifiers_node_symbol on identifiers (node_id, symbol);
        create index if not exists ix_degrees_node on degrees(node_id);
        '''
        print "indexing"
        self.executescript(sqlIndex)
        
        print "querying"
        sqlGetInteractingEntrezGenes = '''select distinct(degrees.node_id) as node_id, identifiers.symbol as entrez_id 
        from degrees inner join identifiers 
        where degrees.degree > 0 
        and identifiers.node_id = degrees.node_id 
        and identifiers.source = 'Entrez Gene ID'
        order by degrees.node_id;
        '''
        
        result = self.select(sqlGetInteractingEntrezGenes)        
        print "number of interacting entrez ids found:", len(result)
        return result
        
def build_linkout_xml(org_folder, statsdbname, xmlDir, org_id, tax_id):

    if not os.path.exists(xmlDir):
        os.makedirs(xmlDir)
    
    print "connecting to", os.path.join(org_folder, statsdbname)
    conn = sqlite3.connect(os.path.join(org_folder, statsdbname))
    conn.row_factory = sqlite3.Row   
    try: 
        reporter = EntrezIdentifiers(conn, 0)
        genes = reporter.getEntrezIdsWithNonzeroDegree()
        
        data = {}
        data['tax_id'] = tax_id
        data['genes'] = genes
        
        out_xml = os.path.join(xmlDir, "%d.xml" % org_id)
        print "creating", out_xml
        utils.create_report(data, "ncbi_linkout.xml", out_xml, render_to = "xml")
        
    finally:
        conn.close()
        
def build_provider_info_xml(xmlDir):

    if not os.path.exists(xmlDir):
        os.makedirs(xmlDir)
            
    out_xml = os.path.join(xmlDir, "providerinfo.xml")
    print"creating", out_xml
    utils.create_report({}, "providerinfo.xml", out_xml, render_to = "xml") 
    
def main(dbDir, xmlDir):

    organisms = buildstatsdb.get_org_list(dbDir)
    
    for organism in organisms:
        org_id, org_name, tax_id = organism['id'], organism['name'], organism['tax_id']
        
        print "loading %s" % org_name
            
        statsdbname = "summary.sqlite"
    
        org_folder = os.path.join(dbDir, str(org_id))
        build_linkout_xml(org_folder, statsdbname, xmlDir, org_id, tax_id)

    build_provider_info_xml(xmlDir)
    print "done"
    
if __name__ == '__main__':
    
    dbDir = sys.argv[1]
    xmlDir = sys.argv[2]
    
    main(dbDir, xmlDir)
