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


import os, sys, time, subprocess

class JobQueue(object):
    '''
    run multiple jobs, n at a time locally.
    only use from a single thread, no locking
    in here. Basically queue everything up first,
    then call run() which will wait till everything is
    run. Eg with 4 local cpu cores, do:

      jq = JobQueue(4)
      jq.submit(['cmd','arg,'arg'])
      jq.submit(['cmd','arg','arg'])
      ...
      jq.run()

    '''
    
    # num of secs we sleep between checking if any
    # jobs are done
    POLL_INTERVAL = 1.0

    # print debug output
    DEBUG = 0

    def __init__(self, n, cwd=None):
        '''n is max number of active jobs,
        the rest wait in the queue
        '''

        self.n = n
        self.cwd=cwd
        self.queue = []
        self.active_jobs = []

        # suppose i should store the outputs ... maybe later
        self.stdouts = {}
        self.stderrs = {}
        self.rcs = {}

    def submit(self, cmd):
        print "queuing:", cmd
        self.queue.append(cmd)

    def run(self):

        for cmd in self.queue:
            # wait till space, then run job
            self._wait_size_le(self.n-1)
            self._submit_job(cmd)

        # wait till queue empty
        self._wait_size_le(0)
        
    def _wait_size_le(self, k):
        '''only return if queue size is
        less than or equal to k
        '''

        while 1:
            if len(self.active_jobs) <= k:
                return
            else:
                if JobQueue.DEBUG:
                    print "waiting queue size is", len(self.active_jobs)
                time.sleep(JobQueue.POLL_INTERVAL)
                self._poll_jobs()

    def _submit_job(self, cmd):
        '''fire off the job
        '''

        if self.cwd is not None:
            # using subprocess.PIPE for stdout and stderr will cause
            # a hang when the output is too large to be buffered.
            # so don't do
            #
            #  stdout=subprocess.PIPE, stderr=subprocess.PIPE
            #
            job = subprocess.Popen(cmd, cwd=self.cwd)
        
        else: # umm, how do you explicity say use default cwd so i don't have to do this?
            job = subprocess.Popen(cmd)

        self.active_jobs.append(job)

    def _poll_jobs(self):
        '''run through the jobs and pick off
        any that are done
        '''

        for job in self.active_jobs:
            if job.poll() is not None:
                rc = job.poll()
                print "job finished with rc", rc
                # if we wanted to save the outputs, 
                # could do something like:
                #
                #    stdout, stderr = job.communicate()
                #
                #    self.rcs[job] = rc
                #    self.stdouts[job] = stdout
                #    self.stderrs[job] = stderr
                #
                # but there's this problem with hangs on large
                # outputs, plus with lots of jobs it would add up
                # to memory use in this process ...
                self.active_jobs.remove(job)

def test():
    '''this test is only good
    on a unix box
    '''

    jq = JobQueue(2)
    cmd1 = 'ls -larth'.split(' ')
    cmd2 = ['pwd']
    cmd3 = ['df', '-h']
    cmd4 = ['sleep', '10']
    cmd5 = ['sleep', '10']
    cmd6 = ['sleep', '10']
    cmd7 = ['sleep', '10']

    jq.submit(cmd1)
    jq.submit(cmd2)
    jq.submit(cmd3)
    jq.submit(cmd4)
    jq.submit(cmd5)
    jq.submit(cmd6)
    jq.submit(cmd7)
    
    jq.run()

if __name__ == '__main__':
    test()
