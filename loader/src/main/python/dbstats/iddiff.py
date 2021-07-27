'''
Identifier diff
'''

import sqlite3, os
import utils

class IdentifierDiff(utils.Db):
    def __init__(self, conn, org_name):
        super(IdentifierDiff, self).__init__(conn)
        self.org_name = org_name

    def diff(self, olddb=None, newdb=None):
        '''
        return a dictionary containing report data comparing two
        versions of an organisms identifier tables
        '''
        
        if not olddb and not newdb:
            raise Exception("can't diff nothing with nobody!")
        
        dbs = {'old': olddb, 'new': newdb}
        
        d = {'name': self.org_name}
        
        
        # number of identifiers belonging to each identifier source
        
        if olddb:
            sqlOldSourceCounts = "select source, count(source) as count from %(old)s.identifiers group by source order by source" % dbs          
            d['old_source_counts'] = self.select(sqlOldSourceCounts)
        else:
            d['old_source_counts'] = []
            
        if newdb:    
            sqlNewSourceCounts = "select source, count(source) as count from %(new)s.identifiers group by source order by source" % dbs           
            d['new_source_counts'] = self.select(sqlNewSourceCounts)
        else:
            d['new_source_counts'] = []

        # we want counts of sources present only in one or the other versions, but for one-sided diff where
        # the organism itself is only present in one, then these boil down to the same counts as above
        if not olddb:
            d['sources_added'] = d['new_source_counts']
        else:
            d['sources_added'] = []
            
        if not newdb:
            d['sources_removed'] = d['old_source_counts']
        else:
            d['sources_removed'] = []
                        
        # otherwise, compare by nested query on the two versions
        if olddb and newdb:
            sqlSourcesAdded = "select source, count(source) as count from %(new)s.identifiers where source not in (select distinct(source) from %(old)s.identifiers) group by source;" % dbs  
            d['sources_added'] = self.select(sqlSourcesAdded)
    
            sqlSourcesLost = "select source, count(source) as count from %(old)s.identifiers where source not in (select distinct(source) from %(new)s.identifiers) group by source;" % dbs        
            d['sources_removed'] = self.select(sqlSourcesLost)


        if olddb and newdb:    
            sqlSourcesMaintained = "select distinct(source) from %(old)s.identifiers where source in (select distinct(source) from %(new)s.identifiers)" % dbs
            d['sources_maintained_short'] = self.select(sqlSourcesMaintained)
             
            sqlMaintainedScript = '''
            drop table if exists id_diffs;
            create temp table id_diffs (source text, old_count int, new_count int, change_count int, change_pct float, lost_symbols int, gained_symbols int);  
            
            insert into id_diffs (source) select distinct (source) from %(old)s.identifiers where source in (select distinct(source) from %(new)s.identifiers);
                    
            update id_diffs set old_count = (select count(%(old)s.identifiers.source) from %(old)s.identifiers where %(old)s.identifiers.source = id_diffs.source);        
            update id_diffs set new_count = (select count(%(new)s.identifiers.source) from %(new)s.identifiers where %(new)s.identifiers.source = id_diffs.source);
            
            update id_diffs set change_count = new_count - old_count;
            update id_diffs set change_pct = (new_count - old_count)*100./(old_count);
            ''' % dbs
            
            self.executescript(sqlMaintainedScript)
            
            # should be able to compute the lost/gained counts with a single query, but it seems to run slow,
            # so just do a loop over the maintained groups. here's the fancy version that needs debugging:
            #        sql_does_not_work_fast = '''
            #        update id_diffs set lost_symbols = (select count(old_identifiers.Symbol) from old_identifiers 
            #        where old_identifiers.source = id_diffs.source 
            #        and old_identifiers.Symbol not in (select new_identifiers.Symbol from new_identifiers where new_identifiers.source = id_diffs.source));
            #        '''
            for m in d['sources_maintained_short']:
                source = m[0]
                params = dict(dbs)
                params['source'] = source
                
                sqlCountLost = '''
                update id_diffs set lost_symbols = (select count(%(old)s.identifiers.Symbol) from %(old)s.identifiers 
                where %(old)s.identifiers.source = '%(source)s' 
                and %(old)s.identifiers.Symbol not in (select %(new)s.identifiers.Symbol from %(new)s.identifiers where %(new)s.identifiers.source = '%(source)s'))
                where id_diffs.source = '%(source)s';
                ''' % params
                self.execute(sqlCountLost)
    
                sqlCountGained = '''
                update id_diffs set gained_symbols = (select count(%(new)s.identifiers.Symbol) from %(new)s.identifiers 
                where %(new)s.identifiers.source = '%(source)s' 
                and %(new)s.identifiers.Symbol not in (select %(old)s.identifiers.Symbol from %(old)s.identifiers where %(old)s.identifiers.source = '%(source)s'))
                where id_diffs.source = '%(source)s';
                ''' % params
                self.execute(sqlCountGained)
            
            d['sources_maintained'] = self.select("select * from id_diffs")
            
            # total gains/losses
            d['total_genes_gained'] = self.count_gained_identifiers()
            d['total_genes_lost'] = self.count_lost_identifiers()

            # splits & joins    
            sqlIdentifiersSplitScript = """
            drop table if exists t1;
            create temp table t1 as select t1.Node_ID as oldid, t2.Node_ID as newid from %(old)s.identifiers as t1, %(new)s.identifiers as t2 where t1.Symbol = t2.Symbol;
            
            create index ix_t1_old on t1 (oldid);
            create index ix_t1_new on t1 (newid);
            
            drop table if exists t2;
            create temp table t2 as select distinct oldid, newid from t1;
            """ % dbs
            
            self.executescript(sqlIdentifiersSplitScript)
            
            #sqlsplit = "select oldid as node_id from t2 group by oldid having count(oldid) > 1;"
            sqlsplit = "select oldid, count(newid) as count_new from t2 group by oldid having count(newid) > 1;"
            d['genes_split'] = self.select(sqlsplit)
            print('splits!:' + str(len(d['genes_split'])) +  str(d['genes_split'])[1:-1])
            
            #sqljoined = "select newid as node_id from t2 group by newid having count(newid) > 1;"
            sqljoined = "select newid, count(oldid) as count_old from t2 group by newid having count(oldid) > 1;"
            d['genes_joined'] = self.select(sqljoined)
            print('joins!:'+ str(len(d['genes_joined'])) + str(d['genes_joined'])[1:-1])
            
            # more detailed split/join reporting            
            sql = """
            -- load up identifiers ids that have been split into a temp table
            drop table if exists split_ids;
            create temp table split_ids as select oldid, count(newid) as count_new from t2 group by oldid having count(newid) > 1;
            create index ix_split on split_ids (oldid);
            
            -- create a report table by writing out a join between the new and old identifier tables for the old ids that have been split
            create table split_report (oldid int, oldsymbol text, oldsource text, newid int, newsymbol text, newsource text);
            
            insert into split_report (oldid, oldsymbol, oldsource, newid, newsymbol, newsource) 
            select old.identifiers.node_id, old.identifiers.symbol, old.identifiers.source, new.identifiers.node_id, new.identifiers.symbol, new.identifiers.source 
            from old.identifiers, new.identifiers, split_ids
            where old.identifiers.node_id = split_ids.oldid and old.identifiers.symbol = new.identifiers.symbol;      
            """
            
            self.executescript(sql)
            
            print("count from split_report: " + str(self.selectNumber("select count(*) from split_report;")))

            sql = """
            -- load up identifier ids that jave been joined into a temp table
            drop table if exists join_ids;
            create temp table join_ids as select newid, count(oldid) as count_old from t2 group by newid having count(oldid) > 1;
            create index ix_join on join_ids (newid);
            
            -- create a report table by writing out a join between the new and old identifier tables for the new ids that have been joined 
            create table join_report (oldid int, oldsymbol text, oldsource text, newid int, newsymbol text, newsource text);
            
            insert into join_report (oldid, oldsymbol, oldsource, newid, newsymbol, newsource) 
            select old.identifiers.node_id, old.identifiers.symbol, old.identifiers.source, new.identifiers.node_id, new.identifiers.symbol, new.identifiers.source 
            from old.identifiers, new.identifiers, join_ids
            where new.identifiers.node_id = join_ids.newid and old.identifiers.symbol = new.identifiers.symbol;      
            """
            
            self.executescript(sql)
            
            print("count from join_report: " + str(self.selectNumber("select count(*) from join_report;")))
            
        else:
            d['sources_maintained_short'] = []
            d['sources_maintained'] = []
            d['genes_split'] = []
            d['genes_joined'] = []
            d['total_genes_gained'] = []
            d['total_genes_lost'] = []
            
        return d

    def write_split_data(self, file):

        query = "select * from split_report order by oldid, newid;"
        self.write_report_data(query, file)
        
    def write_join_data(self, file):
        query = "select * from join_report order by newid, oldid;"
        self.write_report_data(query, file)
    
    def write_lost_identifiers(self, file):        
        query = "select old.identifiers.symbol, old.identifiers.source from old.identifiers where old.identifiers.symbol not in (select symbol from new.identifiers) order by old.identifiers.source asc, old.identifiers.symbol asc;"
        self.write_report_data(query, file)
        
    def write_gained_identifiers(self, file):
        query = "select new.identifiers.symbol, new.identifiers.source from new.identifiers where new.identifiers.symbol not in (select symbol from old.identifiers) order by new.identifiers.source asc, new.identifiers.symbol asc;"
        self.write_report_data(query, file)
        
    def count_lost_identifiers(self):
        query = "select count(old.identifiers.symbol) from old.identifiers where old.identifiers.symbol not in (select symbol from new.identifiers);"
        return self.selectNumber(query)
    
    def count_gained_identifiers(self):
        query = "select count(new.identifiers.symbol) from new.identifiers where new.identifiers.symbol not in (select symbol from old.identifiers);"
        return self.selectNumber(query)
        
def process(conn):
    diff = IdentifierDiff(conn)
    diff.diff()

def test():
    statsdbname = os.path.join(os.getenv("HOME"), "tmp", "statsdb.sqlite")
    main(statsdbname)

def main(statsdbname):
    '''
        - create new stats tables for given organism, prefixing all the 
        table names with given prefix. drops existing tables with the same name
    '''

    conn = sqlite3.connect(statsdbname)
    conn.row_factory = sqlite3.Row   
    try: 
        process(conn)
    finally:
        conn.close()

if __name__ == '__main__':
    test()
