#
# This file is part of GeneMANIA.
# Copyright (C) 2010 University of Toronto.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#



# id remapping script

import sys
from optparse import OptionParser

NO_ID_STRING = 'no_identifier_found'

def load_mapping(filename, from_col=1, to_col=0, filter_col=None, filter_val=None,
    from_col_clean_func=None, to_col_clean_func=None):

    #print "filter val: >>>%s<<<" % filter_val
    
    mapping = {}
    for line in open(filename):
        line = line.strip()
        parts = line.split('\t')

        id = parts[to_col]
        if to_col_clean_func:
            id = to_col_clean_func(id)

        symbol = parts[from_col]
        if from_col_clean_func:
            symbol = from_col_clean_func(symbol)

            
        # if a filter was given, eg 'Ensembl Gene ID', apply and
        # skip records that don't match
        if filter_col:
            val = parts[filter_col]
            if val != filter_val:
                continue

        symbol = symbol.upper()
        if mapping.has_key(symbol):
            raise Exception("symbol already in mapping table: %s" % symbol)

        mapping[symbol] = id

    if len(mapping) == 0:
        raise Exception("no mappings loaded")
    
    return mapping


def clean_internal_id(id):
    '''
    our mapping files use an org prefix, eg 'Ce:12345', this
    function returns just the 12345 part (as a string)
    '''

    code, id = id.split(':')
    return id

def process(input_file, output_file, mapping_file, errors, keep_comments, mapping,
    col_list = None, col_range = None):
    '''
    col_list is a 0-indexed sequence of col ids to map
    
    col_range is a 1 or 2-tuple of python style col range

    can't have both given. if none given, we assume the entire file is to be remapped
    '''

    if col_list and col_range:
        raise Exception("must specify only one of col_list or col_range")

    if not col_list and not col_range:
        col_range = (0, -1)

    out = open(output_file, 'w')

    try:
        for line in open(input_file):
            line = line.rstrip()

            if line.startswith('#'):
                if keep_comments:
                    out.write(line + '\n')
                continue
                
            parts = line.split()

            if col_list:
                for col in col_list:
                    if col < len(parts):
                        try:
                            id = mapping[parts_col.upper()]
                        except KeyError:
                            id = NO_ID_STRING

                        parts[col] = id

            elif col_range:
                if len(col_range) == 2:
                    sub_parts = parts[col_range[0]:col_range[1]]
                else:
                    sub_parts = parts[col_range[0]:]
                    
                for i, part in enumerate(sub_parts):
                    try:
                        id = mapping[part.upper()]
                    except KeyError:
                        id = NO_ID_STRING

                    sub_parts[i] = id

                if len(col_range) == 2:
                    parts[col_range[0]:col_range[1]] = sub_parts
                else:
                    parts[col_range[0]:] = sub_parts
                    
            else:
                raise ("internal error")

            if NO_ID_STRING in parts:
                if errors == 'skip_record':
                    continue
                elif errors == 'replace_blank':
                    new_parts = []
                    for part in parts:
                        if part == NO_ID_STRING:
                            new_parts.append('')
                        else:
                            new_parts.append(part)
                    parts = new_parts
                elif errors == 'shift_left':
                    new_parts = []
                    for part in parts:
                        if part == NO_ID_STRING:
                            pass
                        else:
                            new_parts.append(part)
                    parts = new_parts
                else:
                    raise Exception('unknown error handling request: %s' % errors)

            out.write('\t'.join(parts) + '\n')
            
    finally:
        out.close()
        
def extract_col(cols):
    '''
    given a col spec argument like '1,2,5' or '3:5', split
    and return in the form (col_list, col_range) where either
    one or the other is None
    '''
    
    if ':' in cols:
        first, last = cols.split(':')
        first = int(first)
        if last == '*':
            return None, (first,)
        else:
            last = int(last)
            return None, (first, last)
    else:
        cols = cols.split(',')
        cols = (int(col) for col in cols)
        return cols, None

def main(args):
    usage = "usage: %prog [options] master_config_file.cfg -i input_file -o output_file -m mapping_file -c columns"
    description = "apply identifier remappings"
    parser = OptionParser(usage=usage, description=description)

    parser.add_option('-i', '--infile',
    help='input file to be remapped',
    action='store', type='string', dest='infile')

    parser.add_option('-o', '--outfile',
    help='output file containing remapped data',
    action='store', type='string', dest='outfile')

    parser.add_option('-m', '--mapfile',
    help='normalized mapping file to be applied',
    action='store', type='string', dest='mapfile')

    parser.add_option('-c', '--columns',
    help='column list or range, negative indexing from end of row (python style), eg 0,2,3 or 3:5 or 3:-1',
    action='store', type='string', dest='columns')

    parser.add_option('-e', '--errors',
    help='error handling, either skip_record, replace_blank, or shift_left',
    action='store', type='string', dest='errors')

    parser.add_option('-k', '--keep_comments',
    help='keep comment lines starting with #, default is to remove them',
    action="store_true", dest="keep_comments", default=False)

    parser.add_option('--map_from_col',
    help='map from col, 0-indexed, defaults to 1',
    action="store", type='string', dest="map_from_col", default="1")

    parser.add_option('--map_to_col',
    help='map to col, 0-indexed, defaults to 0',
    action="store", type='string', dest="map_to_col", default="0")

    parser.add_option('--clean_internal_ids',
    help='parse eg, Ce:12345 to 12345, set to from or to or none, defaults to none',
    action="store", type='string', dest="clean_internal_ids", default="none")

    parser.add_option('--filter_col',
    help='col of filter if want to select a subset of rows from mapping',
    action="store", type='string', dest="filter_col", default=None)

    parser.add_option('--filter_val',
    help='filter to apply for selecting mapping records, eg "Ensembl Gene ID"',
    action="store", type='string', dest="filter_val", default=None)
    
    (options, args) = parser.parse_args(args)

#    if len(args) != 1:
#        parser.error("require one master config file")
#
#    config_file = args[0]
#    config = datalib.load_main_config(config_file)

    if options.clean_internal_ids == 'none':
        from_col_clean_func=None
        to_col_clean_func=None
    elif options.clean_internal_ids == 'from':
        from_col_clean_func=clean_internal_id
        to_col_clean_func=None
    elif options.clean_internal_ids == 'to':
        from_col_clean_func=None
        to_col_clean_func=clean_internal_id

    map_from_col = int(options.map_from_col)
    map_to_col = int(options.map_to_col)

    if options.filter_col is not None:
        filter_col = int(options.filter_col)
        filter_val = options.filter_val
        if not filter_val:
            raise Exception('filter col given but filter val not given')
    else:
        filter_col = None
        filter_val = None
            
    col_list, col_range = extract_col(options.columns)

    mapping = load_mapping(options.mapfile, from_col_clean_func=from_col_clean_func,
    to_col_clean_func=to_col_clean_func, from_col=map_from_col, to_col=map_to_col,
    filter_col=filter_col, filter_val=filter_val)

    process(options.infile, options.outfile, options.mapfile, options.errors,
        options.keep_comments, mapping, col_list, col_range)

if __name__ == '__main__':
    main(sys.argv[1:])
