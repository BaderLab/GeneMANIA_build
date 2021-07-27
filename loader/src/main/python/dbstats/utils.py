'''

'''

import sqlite3, codecs, os
from genshi.template import MarkupTemplate
from genshi.template import TemplateLoader

class Db(object):
    '''
    db access convenience methods
    '''
    
    def __init__(self, conn):        
        self.conn = conn   
               
    def selectNumber(self, sql):
        c = self.conn.cursor()
        row = next(c.execute(sql))
        #row = c.next()
        n = int(row[0])
        c.close()
        return n
    
    def select(self, sql):
        c = self.conn.cursor()
        c.execute(sql)
        data = c.fetchall()
        c.close()
        return data

    def selectDesc(self, sql):
        '''also return field names with select query result data'''
        c = self.conn.cursor()
        c.execute(sql)
        data = c.fetchall()
        desc = c.description
        desc = [item[0] for item in desc]
        c.close()
        return data, desc
    
    def execute(self, sql):
        self.conn.execute(sql)
        self.conn.commit()

    def executescript(self, sql):
        self.conn.executescript(sql)
        self.conn.commit()        

    def write_report_data(self, query, file, sep="\t"):
        '''
        dump a table (assumed to have
        already been generated) to a text file
        
        this is a bit more complicated than it needs to be, since
        for python 2.5 support the sqlite row object isn't as 
        convenient to use (doesn't have keys(), not iterable)
        '''
        
        records, headers = self.selectDesc(query)

        f = open(file, "w")

        try:
            
            line = sep.join(headers)
            f.write(line + '\n')
            
            for record in records:
                fixed_record = []
                for i in range(len(headers)):
                    fixed_record.append(record[headers[i]])
                  
                fixed_record = ['' if not field else field for field in fixed_record]
                fixed_record = [str(field) for field in fixed_record]
                #fixed_record = [field.encode('utf8') for field in fixed_record]
                line = sep.join(fixed_record)
                f.write(line + '\n')
                
        finally:
            f.close()
                    
def create_report(data, template_filename, output_filename, render_to = None):
        loader = TemplateLoader(os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'templates'),
                                auto_reload=True)

        tmpl = loader.load(template_filename)
        
        if render_to:
            text = tmpl.generate(d=data).render(render_to)     
        else:        
            text = tmpl.generate(d=data).render('html', doctype='html')
        
        out = codecs.open(output_filename, 'w', encoding='utf8')
        out.write(text)
        out.close()
    
