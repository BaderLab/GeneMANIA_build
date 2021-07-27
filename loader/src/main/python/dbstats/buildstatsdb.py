'''
Build a sqlite database containing the organism, identifier, network data etc
required to generate comparison reports between two database versions. This data
is produced by the engine program DatasetSummarizer.

TODO: describe stats db schema here
'''

import sys, os, codecs, sqlite3
import dbdiff, utils

class TableLoader(utils.Db):
    '''
    helper to pull in a report file into a database table
    '''
    
    def __init__(self, conn, fields, field_types, indices = None):
        
        if len(fields) != len(field_types):
            raise Exception("inconsistent field spec")
        super(TableLoader, self).__init__(conn)
        
        self.fields = fields
        self.field_types = field_types
        self.indices = indices
        self.delim = '\t'
        pass
    
    def _createTable(self, table):
        # build up table creation sql    
        field_spec = []
        for field, field_type in zip(self.fields, self.field_types):
            field_spec.append("%s %s" % (field, field_type))
        
        field_spec = ",".join(field_spec)
        c = self.conn.cursor()
        
        sql = "drop table if exists %s; create table %s (%s);" % (table, table, field_spec)
        c.executescript(sql)
        
        if self.indices:
            for index_info in self.indices:
                name, fields = index_info
                sql = "create index %s_%s on %s (%s);" % (name, table, table, fields)
                c.execute(sql)
                
        self.conn.commit()
        c.close()
                        
    def _createLoadSql(self, table):
        # build the insert sql    
        field_list = ",".join(self.fields)
        place_holders = ['?'] * len(self.fields)
        place_holders = ','.join(place_holders)
        sql = "insert into %s (%s) values (%s);" % (table, field_list, place_holders)
    
        #print sql.encode("utf8")
        self.insert_sql = sql
        
    def _loadRecords(self, filename):
        # pull in values and load
        # we pull all the records into memory and execute, but if we want to 
        # work with large data sets, this is where we would implement batching
        
        f = codecs.open(filename, "r", "utf8")
        
        header = f.readline()
        header = self._split(header)
        
        if len(header) != len(self.fields):
            raise Exception("inconsistent field spec")
            
        data_records = []
        
        for record in f:
            values = self._split(record)
            data_records.append(values)
        
        c = self.conn.cursor()                
        c.executemany(self.insert_sql, data_records)
        self.conn.commit()
        c.close()
       
    def _split(self, line):
        line = line.rstrip('\r\n')
        parts = line.split(self.delim)
        return parts
    
    def load(self, filename, table):
        self._createTable(table)
        self._createLoadSql(table)
        self._loadRecords(filename)

class OrganismReport(TableLoader):
    def __init__(self, conn, old_data, new_data):
        fields = ("id", "name", "tax_id")
        field_types = ("int", "text", "int")
        self.old_data = old_data
        self.new_data = new_data
        super(OrganismReport, self).__init__(conn, fields, field_types)
        self.conn = conn
    
    def loadall(self):
        organismTableName = "organisms.txt"
        oldFile = os.path.join(self.old_data, organismTableName)
        newFile = os.path.join(self.new_data, organismTableName)
        self.load(oldFile, "old_organisms")
        self.load(newFile, "new_organisms")
    
    def getMatchedOrganisms(self):
        sql = "select old.id as old_id, new.id new_id, old.name from old_organisms as old, new_organisms as new where old.name = new.name order by old.name;"
        matched = self.select(sql)
        
        sql = "select id, name from old_organisms where name not in (select name from new_organisms);"
        lost = self.select(sql)
        
        sql = "select id, name from new_organisms where name not in (select name from old_organisms);"
        gained = self.select(sql)
        
        return lost, matched, gained
    
def load_networks(conn, organism_folder):
    
    loader = TableLoader(conn, fields = ("network_group_id", "network_group_name", "network_id", "network_name", "num_nodes", "num_edges", "source", "source_url"),
        field_types = ("int", "text", "int", "text", "int", "int", "text", "text"))
    
    networks_file = os.path.join(organism_folder, "networks.txt")
    loader.load(networks_file, "networks")

def load_network_degrees(conn, organism_folder):
    
    loader = TableLoader(conn, fields = ("network_id", "node_id", "symbol", "degree", "interactors"),
        field_types = ("int", "int", "text", "float", "int"), 
        indices = [ ('ix_nid_sym', 'network_id, symbol') ])
    
    networks_file = os.path.join(organism_folder, "networkDegrees.txt")
    loader.load(networks_file, "degrees")

def load_identifiers(conn, organism_folder):
    
    loader = TableLoader(conn, fields = ("node_id", "symbol", "source"),
        field_types = ("int", "text", "text"),
        indices = [ ('ix_sym', 'symbol') ])
    
    networks_file = os.path.join(organism_folder, "identifiers.txt")
    loader.load(networks_file, "identifiers")

def load_gene_annos(conn, organism_folder):
    
    loader = TableLoader(conn, fields = ("node_id", "annotations"),
        field_types = ("int", "text"))
    
    networks_file = os.path.join(organism_folder, "gene_annos.txt")
    loader.load(networks_file, "gene_annos")

def load_category_annos(conn, organism_folder):
    
    loader = TableLoader(conn, fields = ("category_id", "annotations"),
        field_types = ("int", "text"))
    
    networks_file = os.path.join(organism_folder, "category_annos.txt")
    loader.load(networks_file, "category_annos")

def load_organisms(conn, db_folder):
    loader = TableLoader(conn, fields = ("id", "name", "tax_id"), field_types = ("int", "text", "int"))
    
    networks_file = os.path.join(db_folder, "organisms.txt")
    loader.load(networks_file, "organisms")    
    
def load_attributes(conn, db_folder):
    loader = TableLoader(conn, fields = ("attribute_group_id", "attribute_group_name", "attribute_id", "attribute_name", "num_nodes"), 
                         field_types = ("int", "text", "int", "text", "int"))
    attributes_file = os.path.join(db_folder, "attributes.txt")
    loader.load(attributes_file, "attributes")
    
def load(conn, organism_folder):
    '''
        - create new stats tables for given organism, prefixing all the 
        table names with given prefix. drops existing tables with the same name
    '''
    
    load_networks(conn, organism_folder)
    load_network_degrees(conn, organism_folder)
    load_identifiers(conn, organism_folder)
    load_gene_annos(conn, organism_folder)
    load_category_annos(conn, organism_folder)
    load_attributes(conn, organism_folder)

def build_summary_db(organism_folder, statsdbname):
    '''
        - create new stats tables for given organism, prefixing all the 
        table names with given prefix. drops existing tables with the same name
    '''

    statsdbname = os.path.join(organism_folder, statsdbname)
    if os.path.exists(statsdbname):
        os.remove(statsdbname)
        
    conn = sqlite3.connect(statsdbname)
    conn.row_factory = sqlite3.Row   
    try: 
        load(conn, organism_folder)
    finally:
        conn.close()

def get_org_list(dbDir):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    load_organisms(conn, dbDir)
   
    db = utils.Db(conn)
    data = db.select("select id, name, tax_id from organisms")
   
    conn.close()     
    return data
          
def main(dbDir):

    organisms = get_org_list(dbDir)
      
    for organism in organisms:
        org_id, org_name = organism['id'], organism['name']
        
        print("loading " + org_name)
            
        statsdbname = "summary.sqlite"
    
        org_folder = os.path.join(dbDir, str(org_id))
        build_summary_db(org_folder, statsdbname)

    print("done")
    
if __name__ == '__main__':
    
    for dbDir in sys.argv[1:]:
        print("processing" + dbDir)
        main(dbDir)
