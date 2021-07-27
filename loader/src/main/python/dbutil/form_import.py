#!/usr/bin/python
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


# pull down unprocessed rows from our spreadsheet, and import

import sys, os, datetime, urllib, csv, time
import gdata.spreadsheet
import gdata.spreadsheet.service
import datalib, import_file
import traceback
from optparse import OptionParser

# spreadsheet & worksheet keys
# if you don't know, do this:
#
#   processor = ImportProcessor('user@gmail.com', 'mypassword')
#   ss_key, ws_key = processor.get_keys('GeneMANIA Data Import Request', 'Sheet1')
#
ss_key, ws_key = ('t_60KYmtJrco8A8fezjTx4w', 'od6')


# col name constants for our convenience

TIMESTAMP = 'Timestamp'
ORG = 'Organism'
GRP = 'Network Group'
PMID = 'Pubmed ID'
IMPORT_STATUS = 'Import Status'
IMPORT_DATE = 'Import Date'
NAME = 'Network name override'
DESC = 'Network Description override'
SOURCE = 'Source'
PROC = 'Processing'
DEFAULT = 'Use as default network'
COMMENT = 'Comment'
DATA_URL = 'Link to data'
FILENAME = 'Filename'

def select_collection(processing):
    '''
    need to figure out which of our named processing
    colletions in the master db.cfg should bu used
    for various values of the user input 'processing'
    field. hardcoded for now
    '''

    if processing.startswith('Profile'):
        return 'web_import_profile'
    elif processing.startswith('Weighted'):
        return 'web_import_network'
    elif processing.startswith('Binary'):
        return 'web_import_binary_to_shared_neighbor'
    elif processing.startswith('Sparse'):
        return 'web_import_sparse_profile'
    else:
        raise Exception("unknown processing option: %s" % processing)
    
def get_key(feed, search_name):
    '''
    helper to parse key from a feed, for spreadsheet and worksheet keys
    '''

    for spreadsheet in feed.entry:
        name = spreadsheet.title.text
        key = spreadsheet.id.text.rsplit('/', 1)[1]
        if name == search_name:
            return key

    return None

class ImportProcessor(object):
    def __init__(self, config_file, user, pw):
        self.config_file = config_file
        self.config = datalib.load_main_config(config_file)
        self.user = user
        self.pw = pw

    def connect(self):
        self.gd_client = gdata.spreadsheet.service.SpreadsheetsService()
        self.gd_client.email = self.user
        self.gd_client.password = self.pw
        self.gd_client.ProgrammaticLogin()

    def get_records(self, min_row=None, max_row=None):

        if min_row is not None or max_row is not None:

            query = gdata.spreadsheet.service.CellQuery()
 
            if min_row is not None:
                query['min-row'] = str(min_row)
         
            if max_row is not None:
                query['max-row'] = str(max_row)
        else:
            query = None


        if query:
            feed = self.gd_client.GetCellsFeed(ss_key, ws_key, query=query)
        else:
            feed = self.gd_client.GetCellsFeed(ss_key, ws_key)


        data = []
        for entry in feed.entry:
            row = entry.cell.row
            col = entry.cell.col
            text = entry.cell.text
            inputValue = entry.cell.inputValue
            data.append( (row, col, text) )
        return data

    def update_cell(self, row, col, value):
        entry = self.gd_client.UpdateCell(row=row, col=col, inputValue=value, key=ss_key, wksht_id=ws_key)
        if isinstance(entry, gdata.spreadsheet.SpreadsheetsCell):
            return True
        else:
            return False

    def load_header(self):
        '''
        build some dicts for mapping between col positions and names
        '''

        records = self.get_records(min_row=1, max_row=1)

        self.col_name_to_index = {}
        self.col_index_to_name = {}

        for rec in records:
            row, col, text = rec
            row = int(row)
            col = str(col) # should already be a string, but anyway
            assert row == 1 
            self.col_name_to_index[text] = col
            self.col_index_to_name[col] = text

    def load_request_records(self):
        requests = {} # by row

        cells = self.get_records(min_row=2)

        for cell in cells:
            row, col, text = cell
            if requests.has_key(row):
                request = requests[row]
            else:
                request = {}
                requests[row] = request

            #col_name = self.col_id_to_name[col]
            request[col] = text
              
        return requests

    def close(self):
        '''don't know how to close. need to close?'''
        pass

    def get_keys(self, ss_name, ws_name):
        '''
        helper to get keys if you only know the sheet names
        '''

        feed = self.gd_client.GetSpreadsheetsFeed()
        key1 = get_key(feed, ss_name)

        feed = self.gd_client.GetWorksheetsFeed(key1)
        key2 = get_key(feed, ws_name)

        return key1, key2

    def process_imports(self, requests):
        for request_row_num in requests:
            request = requests[request_row_num]
            c = self.col_name_to_index[IMPORT_STATUS]
            #print request

            try:
                print request
                # why can't i get the timestamp out?
                #ts = request[self.col_name_to_index[TIMESTAMP]]
                print "processing record %s" % (request_row_num)
                filename = self.process_import(request_row_num, request)
                self.mark_done(request_row_num, filename)
            except:
                print "error processing record %s, will be marked as failed" % request_row_num
                exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                #print traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback)
                traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, file=sys.stdout)

                self.mark_error(request_row_num)

            # only process records with no value in the status field
            #if not request.has_key(c) or request[c].strip() == '':
            #    try:
            #        print request
            #        # why can't i get the timestamp out?
            #        #ts = request[self.col_name_to_index[TIMESTAMP]]
            #        print "processing record %s" % (request_row_num)
            #        filename = self.process_import(request_row_num, request)
            #        self.mark_done(request_row_num, filename)
            #    except:
            #        print "error processing record %s, will be marked as failed" % request_row_num
            #        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            #        #print traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback)
            #        traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback,
            #                  file=sys.stdout)
            #
            #
            #        self.mark_error(request_row_num)
            #
            #else:
            #    print "skipping record %s because its status is '%s'" % (request_row_num, request[c])

    def process_import(self, request_row_num, request):
        #print "should process: ", request

        processing = request[self.col_name_to_index[PROC]]
        collection = select_collection(processing)
        print "request is for collection: %s" % collection

        filename, filekey = self.get_data_file(request, collection)

        # convert form values to internal codes
        organism_name = request[self.col_name_to_index[ORG]].strip()
        group_name = request[self.col_name_to_index[GRP]].strip()

        group_code = datalib.get_group_code_from_group_name(self.config, group_name)
        org_code = datalib.get_short_id_for_organism_common_name(self.config, organism_name)

        try:
            pmid = request[self.col_name_to_index[PMID]].strip()
        except KeyError:
            pmid = None

        try:
            name = request[self.col_name_to_index[NAME]].strip()
            name = name.replace("_", "-")
        except KeyError:
            name = None

        try:
            description = request[self.col_name_to_index[DESC]].strip()
        except KeyError:
            description = None

        try:
            source = request[self.col_name_to_index[SOURCE]].strip()
        except KeyError:
            source = 'UNKNOWN-SOURCE'

        try:
            default = request[self.col_name_to_index[DEFAULT]].strip()
        except:
            default = 'No'

        if default != 'Yes':
            default = None

        try:
            comment = request[self.col_name_to_index[COMMENT]].strip()
        except KeyError:
            comment = None
            
        
        # import! note the confusion with the use of the term 'comment'.
        # we have a comment field in the spreadsheet, but that's for internal use
        # the comment field in the metadata refers to the text that is shown
        # in the UI description formatted along with links etc. sorry bout that :(
        import_file.process(self.config_file, collection, org_code, filename,
        group_code, source=source, pubmed_id = pmid, name=name,
        comment=description, keywords=None, description=None, default=default)

        return filename
    
    def mark_done(self, row, filename):
        print "marking %s as done" % row

		# don't mark the Import Status column as Imported so everything gets re-imported
		# when doing a full data refresh - Harold

        #col = self.col_name_to_index[IMPORT_STATUS]
        #self.update_cell(row, col, 'Imported')

        date = datetime.datetime.now()
        date = str(date)
        col = self.col_name_to_index[IMPORT_DATE]
        self.update_cell(row, col, date)

        col = self.col_name_to_index[FILENAME]
        self.update_cell(row, col, filename)

    def mark_error(self, row):
        # don't mark Import Status column as Error so everything gets re-imported
        # when doing a full data refresh - Harold
        #col = self.col_name_to_index[IMPORT_STATUS]
        #self.update_cell(row, col, 'Error')
        date = datetime.datetime.now()
        date = str(date)
        col = self.col_name_to_index[IMPORT_DATE]
        self.update_cell(row, col, date)

    def get_data_file(self, request, collection):
        col = self.col_name_to_index[DATA_URL]
        url = request[col].strip()
        url = url.replace(' ', '%20')
        #kprint "url is [%s]" % url

        #now = datetime.datetime.now()
        #filekey = now.strftime("%Y%m%d_%H%M%S")
        #filekey = "%s_%s" % (filekey, now.microsecond)

        col = self.col_name_to_index[TIMESTAMP]
        ts = request[col]
        timeTuple = time.strptime(ts, "%m/%d/%Y %H:%M:%S")
        filekey = time.strftime("%Y%m%d_%H%M%S", timeTuple)
        

        outfile = "%s.txt.tmp.1" % filekey

        print "saving %s to %s" % (url, outfile)
        urllib.urlretrieve(url, outfile)

 
        infile = outfile
        outfile = "%s.txt.tmp.2" % filekey
        print "reformatting %s to %s" % (infile, outfile)
        num_recs, min_fields, max_fields, first_line_num_fields = reformat_file(infile, outfile)

        # fixup binary networks with '1'
        if collection == 'web_import_network' and min_fields == 2 and max_fields == 2:
            infile = outfile
            outfile = "%s.txt.tmp.3" % filekey
            print "adding 1's to binary network, from file %s to file %s" % (infile, outfile)
            add_weights_to_bin_network(infile, outfile)

        if collection == 'web_import_profile' and (min_fields != first_line_num_fields or max_fields != first_line_num_fields):
            infile = outfile
            outfile = "%s.txt.tmp.4" % filekey
            print "setting all lines of non-rectangular profile to length %s, from file %s to file %s" % (first_line_num_fields, infile, outfile)
            rectangularize_file(infile, outfile, first_line_num_fields)

        # rename
        filename = "%s.txt" % filekey
        print "renaming %s to %s" % (outfile, filename)
        os.rename(outfile, filename)
        
        return filename, filekey


def reformat_file(input_file, output_file):
    '''
    use csv reader to sniff format, and write
    back out as tab delimted. also adjusts for
    mac \r newlines
    '''

    num_recs = 0
    min_fields = 9999999
    max_fields = 0
    first_line_num_fields = None
    
    csvfile = open(input_file, 'U')
    dialect = csv.Sniffer().sniff(csvfile.read(166536))
    csvfile.seek(0)
    reader = csv.reader(csvfile, dialect)

    out = open(output_file, 'w')
    for record in reader:
        line = '\t'.join(record) + '\n'
        out.write(line)
        num_recs += 1

        if first_line_num_fields is None:
            first_line_num_fields = len(record)
        if len(record) < min_fields:
            min_fields = len(record)
        if len(record) > max_fields:
            max_fields = len(record)


    out.close()
    csvfile.close()

    print "num records: %d, min fields: %d, max fields: %d, first line num fields: %d" % (num_recs, min_fields, max_fields, first_line_num_fields)
    return num_recs, min_fields, max_fields, first_line_num_fields

def add_weights_to_bin_network(input_file, output_file):
    '''
    add a weight column containing just 1's
    to col 3 of a binary network input file. we could update
    our downstream tools to handle this, but reformatting
    the inputs in these scripts is easier for now.

    the input file is assumed to have been passed through
    reformat_file, so we don't sniff for format and just
    assume its tabs

    we add a column with '1's to the third position.
    '''

    csvfile = open(input_file, 'U')
    reader = csv.reader(csvfile, delimiter='\t')

    out = open(output_file, 'w')
    for record in reader:
        if len(record) == 2:
            line = '\t'.join(record + ['1']) + '\n'
        else:
            line = '\t'.join(record) + '\n'
        out.write(line)


    out.close()
    csvfile.close()

def rectangularize_file(input_file, output_file, fix_len):
    '''
    trim or extend all lines to match the given length.
    fill in with missing values if necessary
    '''
    csvfile = open(input_file, 'U')
    reader = csv.reader(csvfile, delimiter='\t')

    out = open(output_file, 'w')
    for record in reader:
        if len(record) > fix_len:
            record = record[:fix_len]
        elif len(record) < fix_len:
            record = record + [''] * (fix_len - len(record))

        line = '\t'.join(record) + '\n'

        out.write(line)

    out.close()
    csvfile.close()

def process(config_file, username, password):
    '''
    setup and process the imports
    '''
    
    processor = ImportProcessor(config_file, username, password)
    processor.connect()
    processor.load_header()

    recs = processor.load_request_records()
    processor.process_imports(recs)

    processor.close()

    print 'done'

def main(args):
    usage = "usage: %prog [options] master_config_file.cfg -u user -p pass"
    description = "import data from google spreadsheet into srcdb"
    parser = OptionParser(usage=usage, description=description)

    parser.add_option('-u', '--username',
    help='google username, eg joe@gmail.com',
    action='store', type='string', dest='username')

    parser.add_option('-p', '--password',
    help='',
    action='store', type='string', dest='password')

    (options, args) = parser.parse_args(args)

    if len(args) != 1:
        parser.error("require one master config file")

    config_file = args[0]

    process(config_file, options.username, options.password)

if __name__ == '__main__':
    main(sys.argv[1:])
