'''
generate entrez-to-ensembl identifier tables to use to
resolve identifier ambiguities in the raw (idmapper) tables
'''

import os, sys, datalib
from identifiers import fetch_entrez_identifiers

def process(config, dbhost, dbport, dbuser, dbpass, dbname):
    organisms = config.config['Organisms']['organisms']
    
    for organism in organisms:
        organism_name = config.config[organism]['name']
        short_id = config.config[organism]['short_id']
        tax_id = config.config[organism]['ncbi_taxonomy_id']
        
        dirname = config.getReverseMappingDir()
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            
        reverse_filename = os.path.join(dirname, "ENTREZ_TO_ENSEMBL_%s" % short_id)

        print organism_name, reverse_filename
        fetch_entrez_identifiers.fetch(tax_id, reverse_filename, dbhost, dbport, dbuser, dbpass, dbname)
    
def main(args):
    '''
    arg processing. should the db connection params come from db.cfg or
    the command line via some controlling scripts?
    '''

    if len(args) != 6:
        raise Exception("usage: [prog] config-file dbhost dbport dbuser dbpass dbname")

    config_file = args[0]
    dbhost = args[1]
    dbport = int(args[2])
    dbuser = args[3]
    dbpass = args[4]
    dbname = args[5]

    config = datalib.MasterConfig(config_file)
    
    process(config, dbhost, dbport, dbuser, dbpass, dbname)
    
if __name__ == '__main__':
    main(sys.argv[1:])

