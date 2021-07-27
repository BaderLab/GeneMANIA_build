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


import sys, os, shlex, datalib, jobqueue
from optparse import OptionParser

P2N_CMD = 'java -Xmx1g -cp %s org.genemania.engine.core.evaluation.ProfileToNetworkDriver -in "%s" -out "%s" -log "%s" -syn "%s" -proftype %s -cor %s -threshold auto -keepAllTies -limitTies'

def make_p2n_exec_cmd(cmd, loader_jar, profile, network, log_file, processed_mapping_file, profile_type, correlation_method):
    '''
    return the system command to run the tool to convert the
    profile to a network
    '''

    return cmd % (loader_jar, profile, network, log_file, processed_mapping_file, profile_type, correlation_method)

def run_job(cmd):
    '''
    use some job control system to submit jobs. for now we
    just execute directly. should be using subprocess here?
    '''
    print cmd
    os.system(cmd)

def process(config, filters=None, test=False, collection_filter=None):
    '''
    read in all the cfg files in dir, extract the pubmed id,
    fetch the corresponding mesh descriptors, and update the config file
    '''

    masterConfig = datalib.MasterConfig(config.filename)
    data_dir = masterConfig.getDataDir()

    enabled_organisms = config['Organisms']['organisms']

    #p2n_cmd = config['Tools']['p2n_cmd']
    p2n_cmd = P2N_CMD
    loader_jar = datalib.get_loader_jar('target')
    processed_mapping_dir = datalib.get_location(config, 'processed_mappings_dir')

    if filters:
        network_cfgs = datalib.get_filtered_configs(config, filters)
    else:
        network_cfgs = datalib.load_cfgs(data_dir)

    jq = jobqueue.JobQueue(masterConfig.getJobParallelism())
    
    for cfg in network_cfgs:

        if cfg['dataset']['organism'] not in enabled_organisms:
            continue
        
        collection = datalib.get_data_collection(data_dir, cfg.filename)

        # if a collection was specified, check we are in it
        if collection_filter:
            collection_dir = datalib.get_data_collection(data_dir, cfg.filename)
            #print "filter '%s', collection '%s'" % (collection_filter, collection_dir)
            if collection_filter != collection_dir:
                #print "skipping %s, not in desired collection" % cfg.filename
                continue

        # look up some processing instructions for the collection
        try:
            processing = config['processing'][collection]
        except KeyError:

            # no collection level config, try file level
            try:
                processing = cfg['processing']
            except KeyError:
                print "no processing instructions for cfg %s, skipping" % cfg.filename
                continue
                
        p2n_flag = processing['p2n'].lower()
        if p2n_flag == 'false':
            #print "don't need to process", cfg.filename
            continue
        elif p2n_flag == 'true':
            print "processing", cfg.filename
        else:
            raise Exception('unexpected value for processing p2n "%s", expected true or false' % p2n_flag)

        in_from = processing['p2n_input_from']
        out_to = processing['p2n_output_to']
        correlation = processing['correlation'].upper()
        proftype = processing['proftype'].upper()
        sparsification = processing['sparsification']
        
        # connect to file names
        input_file = cfg['gse'][in_from]
        
        name, ext = os.path.splitext(input_file)
        output_file = "%s_p2n%s" % (name, ext)
        log_file = "%s_p2n.log" % (name)

        cfg['gse'][out_to] = output_file

        cfg_dir = os.path.dirname(cfg.filename)

        input_dir = datalib.dir_for_data_file_type(config, in_from)
        input_dir = os.path.join(cfg_dir, input_dir)

        output_dir = datalib.dir_for_data_file_type(config, out_to)
        output_dir = os.path.join(cfg_dir, output_dir)

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        input_file = os.path.join(input_dir, input_file)
        output_file = os.path.join(output_dir, output_file)
        log_file = os.path.join(output_dir, log_file)

        short_id = cfg['dataset']['organism']
        try:
        	processed_mapping_file = datalib.get_processed_mapping_file(processed_mapping_dir, short_id)
        except Exception, e:
            print "failed to get processed mapping file for", short_id
            continue
       	processed_mapping_file = os.path.join(processed_mapping_dir, processed_mapping_file)

        if not os.path.isfile(input_file):
            raise Exception("input file does not exist: '%s'" % input_file)

        if test:
            print "test mode, just creating output"
            cmd = 'touch "%s"' % output_file
        else:
            cmd = make_p2n_exec_cmd(p2n_cmd, loader_jar, input_file, output_file, log_file, processed_mapping_file,
                proftype, correlation)

        # serial or parallel?
        #run_job(cmd)
        cmd = cmd.encode('ascii')
        cmd_split = shlex.split(cmd)
        jq.submit(cmd_split)
        cfg.write()

    jq.run()

def main(args):
    '''
    parse args & call process()
    '''

    usage = "usage: %prog [options] master_config_file.cfg"
    description = "convert profiles to networks"
    parser = OptionParser(usage=usage, description=description)
    
    parser.add_option('-f', '--filter',
    help='network metadata filter expression',
    action='append', type='string', dest='filter')

    parser.add_option('-t', '--test',
    help='test process, just create empty output files',
    action='store_true', dest='test', default=False)

    parser.add_option('-c', '--collection',
    help='restrict to configurations falling within the given named collection, eg geo or biogrid_direct',
    action="store", dest="collection")

    (options, args) = parser.parse_args(args)

    if len(args) != 1:
        parser.error("require one master config file")

    config_file = args[0]


    filter_params = options.filter
    if filter_params:
        filters = [param.split('=') for param in filter_params]
    else:
        filters = []
        
    config = datalib.load_main_config(config_file)
    process(config, filters, test=options.test, collection_filter=options.collection)

if __name__ == '__main__':
    main(sys.argv[1:])

