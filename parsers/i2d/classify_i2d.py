
import sys, os, csv, shutil, signal

EXPECTED_HEADER = "Organism,Datasource,Use,Processing Notes,Pubmed ID,Network Name Prefix,Comment".split(',')

def handler(signum, frame):
    print 'Caught signal', signum
    sys.exit(1)
    
def load_sources_dict(spreadsheet_filename):
    '''
    return dictionary with key a datasource name and value the organism for which is its source
    '''
    
    dataset_mapping = {}
    
    reader = csv.reader(open(spreadsheet_filename, "rb"), delimiter=',')
    header = reader.next()
    
    # safety check, if this fails check header and the columns we use below
    assert header == EXPECTED_HEADER
    
    for record in reader:
        organism = record[0]
        dataset = record[1]
        use = record[2]
        
        organism = organism.strip().upper()
        
        if use.strip().upper() == 'TRUE':
            if dataset in dataset_mapping:
                raise Exception('same dataset multiple sources?: %s' % dataset)
            dataset_mapping[dataset] = organism

    return dataset_mapping

def classify(organism, dir, dataset_mapping):
    '''
    move files in given organism dir, which contains one file per dataset
    containing the interactions in that dataset, into subdirs called
    'source' and 'unknown', depending on whether that dataset contains
    predicted interactions for the given organism. The files remaining
    in the original folder should only be predicted
    '''
    
    organism = organism.upper()
    
    if not os.path.isdir(dir):
        raise Exception("directory %s does not exist" % dir)
    
    source_dir = os.path.join(dir, 'sources')
    unknown_dir = os.path.join(dir, 'unknown')
    
    if not os.path.isdir(source_dir):
        os.mkdir(source_dir)
    if not os.path.isdir(unknown_dir):
        os.mkdir(unknown_dir)
            
    files = os.listdir(dir)
        
    num_predicted_datasets = 0
    num_source_datasets = 0
    num_unknown_datasets = 0
    
    for file in files:
        if not os.path.isfile(os.path.join(dir, file)):
            continue
        
        if file in dataset_mapping:
            if dataset_mapping[file] == organism:
                # source interactions, move to source subdir
                shutil.move(os.path.join(dir, file), os.path.join(source_dir, file))
                num_source_datasets += 1
            else:
                # predicted interactions, leave alone
                num_predicted_datasets += 1
        else:
            print "unknown dataset, will be ignored: %s" % file
            shutil.move(os.path.join(dir, file), os.path.join(unknown_dir, file))
            num_unknown_datasets += 1
            
    print "classifying datasets for %s: %d source, %d predicted, %d unknown" % (organism, num_source_datasets, num_predicted_datasets, num_unknown_datasets)
            
def main(organism, dir, spreadsheet_filename):

    signal.signal(signal.SIGINT, handler)    
    dataset_mapping = load_sources_dict(spreadsheet_filename)    
    classify(organism, dir, dataset_mapping)

if __name__ == '__main__':

    if len(sys.argv) != 4:
        print 'usage: classify_i2d.py org_name org_dir spreadsheet_filename'
        sys.exit(1)
        
    organism, dir, spreadsheet_filename = sys.argv[1:]
    main(organism, dir, spreadsheet_filename)