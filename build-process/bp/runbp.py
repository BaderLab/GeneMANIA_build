#!/usr/bin/env python
import subprocess, os, sys, shutil
import create_config
import smtplib
import signal
import time
from configobj import ConfigObj
from datetime import datetime

logdir = 'logs'
dbcfg = None
curr_stage = None
proc_list = []

def stage1():
	'''
	Build annotations and ID mapping files
	'''
	print '[STAGE 1]'
	curr_stage = 1
	currdir = os.getcwd()

	# scripts to run for this stage
	s1 = os.path.join(currdir, '1.build_annot.sh')
	s2 = os.path.join(currdir, '1.build_id.sh')

	print '[Building annotations]'
	f1 = open(os.path.join(logdir, 'build_annot.log'), 'w')
	p1 = subprocess.Popen([s1], shell=False, stdout=f1, stderr=f1)

	print '[Building IDs]'
	f2 = open(os.path.join(logdir, 'build_id.log'), 'w')
	p2 = subprocess.Popen([s2], shell=False, stdout=f2, stderr=f2)

	global proc_list
	proc_list = [p1, p2]

	# loop until both subprocesses complete
	while True:
		time.sleep(1)
		if p1.poll() != None and p2.poll() != None:
			break

	return [p1.returncode, p2.returncode]


def stage2():
	'''
	Import various data sources
	'''
	print '[STAGE 2]'
	curr_stage = 2
	currdir = os.getcwd()

	# scripts to run for this stage
	s1 = os.path.join(currdir, '2.import_geo.sh')
	s2 = os.path.join(currdir, '2.import_i2d.sh')
	s3 = os.path.join(currdir, '2.import_pc.sh')
	s4 = os.path.join(currdir, '2.import_biogrid.sh')
	s5 = os.path.join(currdir, '2.import_attribute_legacy.sh')
	s6 = os.path.join(currdir, '2.import_spd.sh')
	s7 = os.path.join(currdir, '2.import_static.sh')
	#s8 = os.path.join(currdir, '2.import_microcosm.sh')
	s9 = os.path.join(currdir, '2.import_iref.sh')
	#s10 = os.path.join(currdir, '2.map_geo.sh')
        s11 = os.path.join(currdir,'2.import_attribute_gmt.sh')

	print '[Importing GEO]'
	f1 = open(os.path.join(logdir, 'import_geo.log'), 'w')
	p1 = subprocess.Popen([s1], shell=False, stdout=f1, stderr=f1)

	print '[Importing I2D]'
	f2 = open(os.path.join(logdir, 'import_i2d.log'), 'w')
	p2 = subprocess.Popen([s2], shell=False, stdout=f2, stderr=f2)

	print '[Importing Pathway Commons]'
	f3 = open(os.path.join(logdir, 'import_pc.log'), 'w')
	p3 = subprocess.Popen([s3], shell=False, stdout=f3, stderr=f3)

	print '[Importing BioGRID]'
	f4 = open(os.path.join(logdir, 'import_biogrid.log'), 'w')
	p4 = subprocess.Popen([s4], shell=False, stdout=f4, stderr=f4)

	print '[Importing legacy atttributes]'
	f5 = open(os.path.join(logdir, 'import_legacyattr.log'), 'w')
	p5 = subprocess.Popen([s5], shell=False, stdout=f5, stderr=f5)
        
        print '[Importing new atttributes]'
	f11 = open(os.path.join(logdir, 'import_newattr.log'), 'w')
	p11 = subprocess.Popen([s11], shell=False, stdout=f11, stderr=f11)

	print '[Importing Shared Protein Domains]'
	f6 = open(os.path.join(logdir, 'import_spd.log'), 'w')
	p6 = subprocess.Popen([s6], shell=False, stdout=f6, stderr=f6)

	print '[Importing Static Data]'
	f7 = open(os.path.join(logdir, 'import_static.log'), 'w')
	p7 = subprocess.Popen([s7], shell=False, stdout=f7, stderr=f7)

	#print '[Importing Microcosm]'
	#f8 = open(os.path.join(logdir, 'import_microcosm.log'), 'w')
	#p8 = subprocess.Popen([s8], shell=False, stdout=f8, stderr=f8)

	print '[Importing iRefIndex]'
	f9 = open(os.path.join(logdir, 'import_iref.log'), 'w')
	p9 = subprocess.Popen([s9], shell=False, stdout=f9, stderr=f9)

	#print '[Mapping GEO]'
	#f10 = open(os.path.join(logdir, 'map_geo.log'), 'w')
	#p10 = subprocess.Popen([s10], shell=False, stdout=f10, stderr=f10)

	global proc_list
	proc_list = [p1, p2, p3, p4, p5, p6, p7, p9, p11] #,p5, p8, p10]

	# wait for all subprocesses to finish
	plist = [p1, p2, p3, p4, p5, p6, p7, p9,p11] #,p5, p8, p10]
	all_proc_done = False
	while not all_proc_done: 
		time.sleep(1)
		for p in plist: 
			if p.poll() == None:
				all_proc_done = False
				break
			else:
				all_proc_done = True

	return [
		p1.returncode, p2.returncode, p3.returncode, 
		p4.returncode, p6.returncode, 
		p7.returncode, p9.returncode,p5.returncode,
                p11.returncode
    ]
	#	p5.returncode, p8.returncode, p10.returncode
	#]


def stage3():
	'''
	Build metadata
	'''
	print '[STAGE 3]'
	curr_stage = 3
	currdir = os.getcwd()

	# scripts to run for this stage
	#s1 = os.path.join(currdir, '3.build_metadata.sh')
	s1 = os.path.join(currdir, '3.do_stage.sh')

	print '[Running stage 3]'
	f1 = open(os.path.join(logdir, 'stage3.log'), 'w')
	p1 = subprocess.Popen([s1], shell=False, stdout=f1, stderr=f1)

	global proc_list
	proc_list = [p1]

	# loop until subprocess completes
	while True:
		time.sleep(1)
		if p1.poll() != None:
			break

	return [p1.returncode]


def stage4():
	'''
	Set default networks
	'''
	print '[STAGE 4]'
	curr_stage = 4
	currdir = os.getcwd()

	# scripts to run for this stage
	s1 = os.path.join(currdir, '4.set_default_networks.sh')

	print '[Setting default networks]'
	f1 = open(os.path.join(logdir, 'set_default_networks.log'), 'w')
	p1 = subprocess.Popen([s1], shell=False, stdout=f1, stderr=f1)

	global proc_list
	proc_list = [p1]

	# loop until subprocess completes
	while True:
		time.sleep(1)
		if p1.poll() != None:
			break

	return [p1.returncode]


def stage5():
	'''
	Build networks
	'''
	print '[STAGE 5]'
	curr_stage = 5
	currdir = os.getcwd()

	# scripts to run for this stage
	s1 = os.path.join(currdir, '5.build_networks.sh')

	print '[Building networks]'
	f1 = open(os.path.join(logdir, 'build_networks.log'), 'w')
	p1 = subprocess.Popen([s1], shell=False, stdout=f1, stderr=f1)

	global proc_list
	proc_list = [p1]

	# loop until subprocess completes
	while True:
		time.sleep(1)
		if p1.poll() != None:
			break

	return [p1.returncode]

def stage6():
	'''
	Extract
	'''
	print '[STAGE 6]'
	curr_stage = 6
	currdir = os.getcwd()

	# scripts to run for this stage
	s1 = os.path.join(currdir, '6.extract.sh')

	print '[Extract]'
	f1 = open(os.path.join(logdir, 'extract.log'), 'w')
	p1 = subprocess.Popen([s1], shell=False, stdout=f1, stderr=f1)

	global proc_list
	proc_list = [p1]

	# loop until subprocess completes
	while True:
		time.sleep(1)
		if p1.poll() != None:
			break

	return [p1.returncode]


def stage7():
	'''
	Build final artifacts
	'''
	print '[STAGE 7]'
	curr_stage = 7
	currdir = os.getcwd()

	# scripts to run for this stage
	s1 = os.path.join(currdir, '7.build_final_artifacts.sh')

	print '[Building final artifacts]'
	f1 = open(os.path.join(logdir, 'build_final_artifacts.log'), 'w')
	p1 = subprocess.Popen([s1], shell=False, stdout=f1, stderr=f1)

	global proc_list
	proc_list = [1]

	# loop until subprocess completes
	while True:
		time.sleep(1)
		if p1.poll() != None:
			break

	return [p1.returncode]


def stage8():
	'''
	Generate data dump
	'''
	print '[STAGE 8]'
	curr_stage = 8
	currdir = os.getcwd()

	# scripts to run for this stage
	s1 = os.path.join(currdir, '8.dump_data.sh')

	print '[Dumping data]'
	f1 = open(os.path.join(logdir, 'dump_data.log'), 'w')
	p1 = subprocess.Popen([s1], shell=False, stdout=f1, stderr=f1)

	global proc_list
	proc_list = [1]

	# loop until subprocess completes
	while True:
		time.sleep(1)
		if p1.poll() != None:
			break

	return [p1.returncode]


def check_results(results):
	'''
	Check the return code of the scripts executed in a particular stage. 
	If a non-zero return code is found, it means that script failed. 
	Return False if a script failed, return True if all scripts passed.
	'''
	for r in results:
		if r != 0: 
			return False
	return True


def send_email(subject, message):
	config = ConfigObj(dbcfg)
	toaddr = config['BuildScriptsConfig']['email_to']
	password = config['BuildScriptsConfig']['google_p']
        smtp_server = config['BuildScriptsConfig']['smtp_server']
	fromaddr = config['BuildScriptsConfig']['google_u']

	subject = config['BuildScriptsConfig']['revision'] + ': ' + subject

	email = ('Subject: %s\r\nFrom: %s\r\nTo: %s\r\n\r\n%s' % 
		(subject, fromaddr, ', '.join(toaddr), message))

        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.ehlo()
        server.login(fromaddr, password)
        header = ('Subject: %s\r\nFrom: %s\r\nTo: %s\r\n\r\n' % 
            (subject, fromaddr, ', '.join(toaddr)))
        email = ''.join([header, message])
        server.sendmail(fromaddr, toaddr, email)
        server.close()


def signal_handler(signal, frame):
	print 'Caught SIGINT, cleaning up'
	global proc_list
	for process in proc_list:
		process.kill()


def main(args):

	if len(args) < 3:
		print 'usage: %s db.cfg [all|1|2|3|4|5|6|7]' % args[0]
		sys.exit(0)

	signal.signal(signal.SIGINT, signal_handler)

	stages = args[2:]
	print 'The following stages will be processed:', stages

	global dbcfg
	dbcfg = args[1]
	create_config.create_script_config(dbcfg)

        #copy the db.cfg file over the SRCDB directory
        config = ConfigObj(dbcfg)
        srcdb = config['BuildScriptsConfig']['srcdb']
        destcfg = os.path.join(srcdb,"db.cfg")
                                
        srccfg = os.path.join(os.getcwd(),"db.cfg")
        shutil.copy(srccfg,destcfg)

	if not os.path.exists(logdir): 
		os.mkdir(logdir)
	else:
		# rename the current logdir
		old_logdir = logdir + "." + datetime.now().strftime("%Y%m%d%H%M%S")
		print 'Backing up logs to', old_logdir
		os.rename(logdir, old_logdir)
		os.mkdir(logdir)

	# run each of the stages. In many cases each subsequent stage depends on the 
	# previous stage to complete successfully. We shouldn't continue if any of the 
	# previous stages fail to complete. 
	if '1' in stages or 'all' in stages:
		if not check_results(stage1()): 
			print 'A step failed in STAGE 1, quitting build process.'
			send_email('Stage 1 failed', 'Something broke in stage 1')
			sys.exit(0)

	if '2' in stages or 'all' in stages:
		if not check_results(stage2()): 
			print 'A step failed in STAGE 2, quitting build process.'
			send_email('Stage 2 failed', 'Something broke in stage 2')
			sys.exit(0)

	if '3' in stages or 'all' in stages: 
		if not check_results(stage3()): 
			print 'A step failed in STAGE 3, quitting build process.'
			send_email('Stage 3 failed', 'Something broke in stage 3')
			sys.exit(0)

	if '4' in stages or 'all' in stages:
		if not check_results(stage4()): 
			print 'A step failed in STAGE 4, quitting build process.'
			send_email('Stage 4 failed', 'Something broke in stage 4')
			sys.exit(0)

	if '5' in stages or 'all' in stages:
		if not check_results(stage5()):
			print 'A step failed in STAGE 5, quitting build process.'
			send_email('Stage 5 failed', 'Something broke in stage 5')
			sys.exit(0)

	if '6' in stages or 'all' in stages:
		if not check_results(stage6()):
			print 'A step failed in STAGE 6, quitting build process.'
			send_email('Stage 6 failed', 'Something broke in stage 6')
			sys.exit(0)

	if '7' in stages or 'all' in stages:
		if not check_results(stage7()):
			print 'A step failed in STAGE 7, quitting build process.'
			send_email('Stage 7 failed', 'Something broke in stage 6')
			sys.exit(0)

	if '8' in stages or 'all' in stages:
		if not check_results(stage8()):
			print 'A step failed in STAGE 8, quitting build process.'
			send_email('Stage 8 failed', 'Something broke in stage 8')
			sys.exit(0)

	print 'Everything seems fine.'
	send_email('Build process completed', ''.join(['The following stages completed successfully: ', str(stages)]))


if __name__ == '__main__':
	main(sys.argv)
