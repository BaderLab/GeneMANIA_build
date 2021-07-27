'''
wrap call to mapping implementation
'''

import sys

import normalize_mappings_new
import normalize_mappings_classic

    
if __name__ == '__main__':
    
    normalize_mappings_new.main(sys.argv[1:])
    #    normalize_mappings_classic.main(sys.argv[1:])
