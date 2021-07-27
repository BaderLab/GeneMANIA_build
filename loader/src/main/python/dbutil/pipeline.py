'''
ruffus-pipelined version of p2n & nn
'''

import sys, os
from ruffus import *
import datalib
from pipeline_utils import touch, run_cmd

import annotate_series, geolib

#
# configuration. using ruffus seems easier when you do everything at the top level
#

P2N_CMD = 'java -Xmx1g -cp %s org.genemania.engine.core.evaluation.ProfileToNetworkDriver -in "%s" -out "%s" -log "%s" -syn "%s" -proftype %s -cor %s -threshold auto -keepAllTies -limitTies'
NN_CMD = u'java -Xmx1g -cp %s org.genemania.engine.apps.NetworkNormalizer -outtype uidstripped -norm %s -in "%s" -out "%s" -log "%s" -syn "%s"'

if len(sys.argv) != 2:
    raise Exception("require one master config file")

config_file = sys.argv[1]
config = datalib.load_main_config(config_file)

data_dir = datalib.get_location(config, 'data_dir')
enabled_organisms = config['Organisms']['organisms']
processed_mapping_dir = datalib.get_location(config, 'processed_mappings_dir')

processing_instructions = config['processing']

loader_jar = datalib.get_loader_jar('target')

#
# helpers
#

    

def param_builder(cfg_dir, in_from , out_to, naming_suffix, *extras):
    '''
    setup input and output file names according to old p2n & nn naming conventions,
    specified in config files. 
    
    returns a list of params, where each element is a ruffus-style list of task specifications
    of the form [list-of-inputs, list-of-outputs, other_params] specifically:
    
      [[input_file, identifier_file], [output_file, flag_file], log_file, correlation_method]  

    this works by scanning the cfg files in the given dir.     
    '''

    params = []    

    cfg_dir = os.path.join(data_dir, cfg_dir)
    configs = datalib.load_cfgs(cfg_dir)
    
    for cfg in configs:

        short_id = cfg['dataset']['organism']
        if short_id not in enabled_organisms:
            continue

        try:
            input_file = cfg['gse'][in_from]
        except KeyError as e:
            print "error in", cfg.filename
            raise e
        
        name, ext = os.path.splitext(input_file)
        output_file = "%s_%s%s" % (name, naming_suffix, ext)
        log_file = "%s_%s.log" % (name, naming_suffix)

        cfg['gse'][out_to] = output_file
        cfg.write()

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

        try:
            processed_mapping_file = datalib.get_processed_mapping_file(processed_mapping_dir, short_id)
        except Exception as e:
            print e
            continue

        processed_mapping_file = os.path.join(processed_mapping_dir, processed_mapping_file)
   
        flag_file = output_file + ".OK"
        
        param = [[input_file, processed_mapping_file], [output_file, flag_file], log_file]
        if extras:
            param = param + list(extras)      
        
        params.append(param)
    
    return params

def anno_params():
    '''
    coexpression platform stuff
    '''

    params = []

    platforms_dir = datalib.get_location(config, 'platform_data_dir')
    raw_dir = config['FileLocations']['raw_dir']
    profile_dir = config['FileLocations']['profile_dir']
    
    #print platforms_dir,raw_dir, profile_dir,"\n"

    network_cfgs = datalib.load_cfgs(data_dir)
    for cfg in network_cfgs:

        if cfg['dataset']['organism'] not in enabled_organisms:
            continue

        if cfg['dataset']['source'] != 'GEO' and cfg['dataset']['type'] != 'gse':
            continue

        #print cfg.filename

        gse_id = cfg['gse']['gse_id']
        
        series_matrix_file = cfg['gse']['raw_data']
        #we were having the same issue when downloading the GSE data
        # the config files don't always specify the raw data file name
        #series_matrix_file = gse_id + "_series_matrix.txt"
        if cfg['gse']['raw_type'] != 'unannotated_profile':
            print "unexpected raw type for geo gse series:", cfg['gse']['raw_type'], ", skipping microarray platform annotation"
            continue

        if series_matrix_file.strip() == '':
            print "no series matrix file for %s, skipping" % (gse_id)
            continue

        platform = cfg['gse']['platforms'] # there should only be one, right?
        platform_file = os.path.join(platforms_dir, geolib.get_platform_filename_for_id(platform))

        if not os.path.exists(platform_file):
            print "skipping %s because platform file does not exist: %s" % (gse_id, platform_file)
            continue

        series_matrix_file = os.path.join(os.path.dirname(cfg.filename), raw_dir, series_matrix_file)

        # annotated file stored in the profile_dir folder
        dir = os.path.join(os.path.dirname(cfg.filename), profile_dir)
        if not os.path.exists(dir):
            os.mkdir(dir)

        annotated_file = os.path.join(dir, '%s_annotated.txt' % gse_id)


        log_file = os.path.join(dir, '%s_annotated.log' % gse_id)

        flag_file = annotated_file + '.OK'

        params.append([[series_matrix_file, platform_file], [annotated_file, flag_file], log_file, gse_id])

        cfg['gse']['profile'] = os.path.basename(annotated_file)
        cfg.write()

    return params

def p2n_params():
    '''
    load processing directions for various collections of networks,
    configured in the master config file
    '''
    
    params = []
    for name, settings in processing_instructions.iteritems():
        if not 'p2n' in settings:
            print "skipping misconfigured section", name
            continue
            
        if settings['p2n'].lower() == 'true':
            in_from = settings['p2n_input_from']
            out_to = settings['p2n_output_to']
            correlation_method = settings['correlation'].upper()
            proftype = settings['proftype'].upper()
            
            params = params + param_builder(name, in_from, out_to, 'p2n', correlation_method, proftype)
    
    return params
        
def nn_params():
    '''
    load processing directions for various collections of networks,
    configured in the master config file
    '''
    params = []
    for name, settings in processing_instructions.iteritems():
        if not 'p2n' in settings:
            print "skipping misconfigured section", name
            continue
        
        in_from = settings['nn_input_from']
        out_to = settings['nn_output_to']
        normalize = settings['normalize'].lower()
        
        params = params + param_builder(name, in_from, out_to, 'nn', normalize)
    
    return params

#
# pipeline tasks
#


@files(anno_params)
def anno(input_files, output_files, log_file, gse_id):
    input_file, map_file = input_files
    output_file, flag_file = output_files

    # TODO: could keep a few maps in mem instead of rereading all the time, but
    # why waste time optimizing a non-critical path
    try:
        map = annotate_series.load_annotation_file(map_file)
    except Exception as e:
        exctype, value = sys.exc_info()[:2]
        print "failed to load annotation file %s for %s, cause:\n%s %s" % (map_file, gse_id, exctype, value)
        raise

    annotate_series.apply_platform_annotation(input_file, map, output_file, log_file)

    touch(flag_file)


@files(p2n_params)
def p2n(input_files, output_files, log_file, correlation_method, proftype):

    input_file, processed_mapping_file = input_files
    output_file, flag_file = output_files
     
    cmd = P2N_CMD % (loader_jar, input_file, output_file, log_file, processed_mapping_file, proftype, correlation_method)
    run_cmd(cmd)
    
    touch(flag_file)

@files(nn_params)
def nn(input_files, output_files, log_file, normalize):

    input_file, processed_mapping_file = input_files
    output_file, flag_file = output_files
    
    cmd = NN_CMD % (loader_jar, normalize, input_file, output_file, log_file, processed_mapping_file)
    run_cmd(cmd)
    
    touch(flag_file)
    
#
# run pipeline. the steps don't feed into each other properly via
# ruffus, but run correctly as independent steps
#
print "map geo arrays"
pipeline_run([anno], verbose=1, multiprocess=2)
print "p2n"
pipeline_run([p2n], verbose=1, multiprocess=2)
print "nn"
pipeline_run([nn], verbose=1, multiprocess=2)

