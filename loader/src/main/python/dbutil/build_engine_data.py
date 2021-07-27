'''
ruffus-ized version of the build_engine_data.sh loader script
'''

import sys, os
from ruffus import *
import datalib
from pipeline_utils import touch, run_cmd

if len(sys.argv) < 3:
    raise Exception("require db_dir lucene_index_dir [output_dir]")

srcdb_dir = sys.argv[1]
lucene_index_dir = sys.argv[2]

if len(sys.argv) == 4:
    output_dir = sys.argv[3]
else:
    output_dir = 'target' # subdir under current working

# check params
if not os.path.isdir(srcdb_dir):
    raise Exception("srcdb directory '{0}' does not exist".format(srcdb_dir))

if not os.path.isdir(lucene_index_dir):
    raise Exception("lucene index directory '{0}' does not exist".format(lucene_index_dir))

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    
# the file structure/naming is too messy to pass on
# directly to each task as inputs & outputs. instead
# use flag files to mark completion of each task
flag_dir = os.path.join(srcdb_dir, 'jobstatus')

if not os.path.exists(flag_dir):
    os.makedirs(flag_dir)

# if output_dir is target and current working dir is
# loader, then this makes sense. otherwise, not so much
loader_jar = datalib.get_loader_jar(output_dir)

# parameters passed on to java programs
common_params = {"JAVA_OPTS": "-Xmx1500M",
                 "CLASS_PATH": loader_jar,
                 "LUCENE_INDEX_DIR": lucene_index_dir,
                 "NETWORK_CACHE_DIR": os.path.join(output_dir, "network_cache"),
                 "LOG_DIR": os.path.join(output_dir, "logs"),
                 "SRCDB_DIR": srcdb_dir}

def oneline(s):
    return s.strip().replace('\n', ' ')

@files(None, os.path.join(flag_dir, 'cachebuilder_done.txt'), 'log_file', common_params)   
def step_cachebuilder(input_file, flag_file, log_file, params):
    cmd = """
    java {JAVA_OPTS} -cp {CLASS_PATH} org.genemania.engine.apps.CacheBuilder
    -indexDir "{LUCENE_INDEX_DIR}"
    -cachedir "{NETWORK_CACHE_DIR}"
    -log "{LOG_DIR}/CacheBuilder.log"
    -networkDir "{SRCDB_DIR}/generic_db/INTERACTIONS"
    """
    
    cmd = oneline(cmd)    
    cmd = cmd.format(**params)
    run_cmd(cmd)
    
    touch(flag_file)

@follows(step_cachebuilder)
@files(os.path.join(flag_dir,'cachebuilder_done.txt'), os.path.join(flag_dir, 'postsparsifier_done.txt'), common_params)    
def step_postsparsifier(input_file, flag_file, params):
    cmd = """
    java {JAVA_OPTS} -cp {CLASS_PATH} org.genemania.engine.apps.PostSparsifier
    -indexDir "{LUCENE_INDEX_DIR}"
    -cachedir "{NETWORK_CACHE_DIR}"
    -log "{LOG_DIR}/PostSparsifier.log"
    """

    cmd = oneline(cmd)
    cmd = cmd.format(**params)
    run_cmd(cmd)
    
    touch(flag_file)
    
@follows(step_postsparsifier)
@files(os.path.join(flag_dir, 'postsparsifier_done.txt'), os.path.join(flag_dir, 'nodedegreecomputer_done.txt'),  common_params)
def step_nodedegreecomputer(input_file, flag_file, params):
    cmd = """
    java {JAVA_OPTS} -cp {CLASS_PATH} org.genemania.engine.apps.NodeDegreeComputer
    -indexDir "{LUCENE_INDEX_DIR}"
    -cachedir "{NETWORK_CACHE_DIR}"
    -log "{LOG_DIR}/NodeDegreeComputer.log"
    """
    
    cmd = oneline(cmd)
    cmd = cmd.format(**params)
    run_cmd(cmd)
    
    touch(flag_file)
    
@follows(step_nodedegreecomputer)
@files(os.path.join(flag_dir, 'nodedegreecomputer_done.txt'), os.path.join(flag_dir, 'annocachebuilder_done.txt'), common_params)
def step_annocachebuilder(input_file, flag_file, params):
    cmd = """
    java {JAVA_OPTS} -cp {CLASS_PATH} org.genemania.engine.apps.AnnotationCacheBuilder
    -indexDir "{LUCENE_INDEX_DIR}"
    -cachedir "{NETWORK_CACHE_DIR}"
    -annodir "{SRCDB_DIR}/GoCategories"
    -log "{LOG_DIR}/AnnotationCacheBuider.log"
    """
    
    cmd = oneline(cmd)
    cmd = cmd.format(**params)
    run_cmd(cmd)
    
    touch(flag_file)

@follows(step_annocachebuilder)
@files(os.path.join(flag_dir, 'annocachebuilder_done.txt'), os.path.join(flag_dir, 'fastweightcachebuilder_done.txt'), common_params)
def step_fastweightcachebuilder(input_file, flag_file, params):
    cmd = """
    java {JAVA_OPTS} -cp {CLASS_PATH} org.genemania.engine.apps.FastWeightCacheBuilder
    -indexDir "{LUCENE_INDEX_DIR}"
    -cachedir "{NETWORK_CACHE_DIR}"
    -qdir "{SRCDB_DIR}/GoCategories"
    -log "{LOG_DIR}/FastWeightCacheBuilder.log"
    """
    
    cmd = oneline(cmd)
    cmd = cmd.format(**params)
    run_cmd(cmd)
    
    touch(flag_file)

@follows(step_fastweightcachebuilder)
@files(os.path.join(flag_dir, 'fastweightcachebuilder_done.txt'), os.path.join(flag_dir, 'enrichmentcategorybuilder_done.txt'), common_params)
def step_enrichmentcategorybuilder(input_file, flag_file, params):
    cmd = """
    java {JAVA_OPTS} -cp {CLASS_PATH} org.genemania.engine.apps.EnrichmentCategoryBuilder
    -indexDir "{LUCENE_INDEX_DIR}"
    -cachedir "{NETWORK_CACHE_DIR}"
    -log "{LOG_DIR}/EnrichmentCategoryBuilder.log"
    """
    
    cmd = oneline(cmd)
    cmd = cmd.format(**params)
    run_cmd(cmd)
    
    touch(flag_file)

@follows(step_enrichmentcategorybuilder)
@files(os.path.join(flag_dir, 'enrichmentcategorybuilder_done.txt'), os.path.join(flag_dir, 'attributebuilder_done.txt'), common_params)
def step_attributebuilder(input_file, flag_file, params):
    cmd = """
    java {JAVA_OPTS} -cp {CLASS_PATH} org.genemania.engine.apps.AttributeBuilder
    -indexDir "{LUCENE_INDEX_DIR}"
    -cachedir "{NETWORK_CACHE_DIR}"
    -genericDbDir "{SRCDB_DIR}/generic_db"
    -log "{LOG_DIR}/AttributeBuilder.log"
    """
    
    cmd = oneline(cmd)
    cmd = cmd.format(**params)
    run_cmd(cmd)
    
    touch(flag_file)

@follows(step_attributebuilder)
@files(os.path.join(flag_dir, 'attributebuilder_done.txt'), os.path.join(flag_dir, 'defaultnetworkselector_done.txt'), common_params)
def step_defaultnetworkselector(input_file, flag_file, params):
    cmd = """
    java {JAVA_OPTS} -cp {CLASS_PATH} org.genemania.engine.apps.DefaultNetworkSelector
    -indexDir "{LUCENE_INDEX_DIR}"
    -cachedir "{NETWORK_CACHE_DIR}"
    -log "{LOG_DIR}/DefaultNetworkSelector.log"
    """
    
    cmd = oneline(cmd)
    cmd = cmd.format(**params)
    run_cmd(cmd)
    
    touch(flag_file)

@follows(step_defaultnetworkselector)
@files(os.path.join(flag_dir, 'defaultnetworkselector_done.txt'), os.path.join(flag_dir, 'networkprecombiner_done.txt'), common_params)
def step_networkprecombiner(input_file, flag_file, params):
    cmd = """
    java {JAVA_OPTS} -cp {CLASS_PATH} org.genemania.engine.apps.NetworkPrecombiner
    -indexDir "{LUCENE_INDEX_DIR}"
    -cachedir "{NETWORK_CACHE_DIR}"
    -log "{LOG_DIR}/NetworkPrecombiner.log"
    """
    
    cmd = oneline(cmd)
    cmd = cmd.format(**params)
    run_cmd(cmd)
    
    touch(flag_file)

# run the pipeline to the last step
pipeline_run([step_defaultnetworkselector], verbose=4, multiprocess=1)
