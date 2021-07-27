
# build a simple sqlite db from generic_db files. 
# exclude interactions.
#

import sys, sqlite3, os, codecs

class Converter(object):
    def __init__(self, generic_db_dir, sqlite_db_name):
        self.generic_db_dir = generic_db_dir
        self.sqlite_db_name = sqlite_db_name

    def convert(self):
        try:
            self.conn = sqlite3.connect(sqlite_db_name)
            self.conn.row_factory = sqlite3.Row

            self._load_schema()
            self._load_data()
            self._index()

        finally:
            self.conn.close() 

    def _load_schema(self):
        fn = os.path.join(self.generic_db_dir, 'SCHEMA.txt')

        f = open(fn, 'r')

        lines = f.readlines()
        lines = [line.strip() for line in lines]
        lines = [line.split('\t') for line in lines]

        print lines
        self.schema = lines

    def _load_data(self):
        for table_spec in self.schema:
            name = table_spec[0]
            fields = table_spec[1:]

            self._create_table(name, fields)
            self._insert(name, fields)

    def _create_table(self, name, fields):
        field_spec = []
        for field in fields:
            field_spec.append("%s text" % field)
    
        field_spec = ",".join(field_spec)

        c = self.conn.cursor()
        sql = "drop table if exists %s; create table %s (%s);" % (name, name, field_spec)
        print sql
        c.executescript(sql)

    
    def _insert(self, name, fields):

        field_list = ",".join(fields)
        place_holders = ['?'] * len(fields)
        place_holders = ','.join(place_holders)
        sql = "insert into %s (%s) values (%s);" % (name, field_list, place_holders)
    

        fn = '%s.txt' % name
        fn = os.path.join(self.generic_db_dir, fn)
        f = codecs.open(fn, "r", "utf8")
        
        data_records = []
        
        for record in f:
            values = record.rstrip('\r\n')
            values = values.split('\t')

            data_records.append(values)
        
        c = self.conn.cursor()                
        c.executemany(sql, data_records)
        self.conn.commit()
        c.close()

    def _index(self):
        return # for later, when we need it

        # gotta hardcode this
        sql = """
        create index networks_ix on NETWORKS (ID);
        create index groups_ix on blah blah;
        """
        
        c = self.conn.cursor()                
        c.executescript(sql)
        c.close()
       
def main(generic_db_name, sqlite_db_name):

    converter = Converter(generic_db_name, sqlite_db_name)
    converter.convert()

if __name__ == '__main__':
    generic_db_name = sys.argv[1]
    sqlite_db_name = sys.argv[2]

    main(generic_db_name, sqlite_db_name)


