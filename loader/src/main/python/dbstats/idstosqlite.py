'''
load processed identifier file into sqlite database

  python idstosqlite.py /somewhere/At_names.txt /tmp/At.sqlite

'''

import sqlite3, sys

def load(idfile, dbfile):
    
    conn = sqlite3.connect(dbfile)    
    conn.text_factory = str
    conn.row_factory = sqlite3.Row  # handy for selects
    
    try:
        sql = """
        drop table if exists identifiers; 
        create table identifiers (node_id text, symbol text, source text);
        create index ix_identifers_symbol on identifiers (symbol);        
        """
        conn.executescript(sql)
        
        # all into mem
        records = []
        for line in open(idfile):
            line = line.strip()
            parts = line.split('\t')
            if len(parts) != 3:
                raise Exception("invalid input file")
            records.append(parts)
            
        # big batch insert
        conn.executemany("insert into identifiers (node_id, symbol, source) values (?, ?, ?);", records)
        conn.commit()
        
        # test query        
        cursor = conn.cursor()
        cursor.execute("select source, count(source) as count from identifiers group by source;")
        results = cursor.fetchall()
        for row in results:
            print row['source'], row['count']
            
    finally:
        conn.close()
        
if __name__ == '__main__':
    
    idfile = sys.argv[1]
    dbfile = sys.argv[2]
    load(idfile, dbfile)
