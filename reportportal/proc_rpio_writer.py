#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ref:
# https://github.com/reportportal/client-Python/blob/master/reportportal_client/service.py
# https://github.com/reportportal/client-Python
# https://reportportal-piqe-stage.apps.ocp4.prod.psi.redhat.com/ui/#api
#
# restapi steps:
# search for xmls
# import xml and gen runid
# update run tags by runid
# merge all runs by together into on run
# create a filter
# updates the filter
# create dashboard
# add table widget to the dashboard
# add rp dashboard link to mpts run record

'''
script to upload xunit reports to rpio
'''
import logging
import sys
import os
import traceback
from optparse import OptionParser
try:
    from  configparser import SafeConfigParser
except ImportError:
    from  ConfigParser import SafeConfigParser
import pprint
import prow_job
import subprocess
import xml.etree.ElementTree as ET
import xunitparser


__all__ = []
__version__ = 2.1
__date__ = '2019-02-21'
__updated__ = '2020-12-08'


def main(argv=None):
    '''
    main function
    '''

    program_version = "v2.0"
    program_build_date = "%s" % __updated__

    program_version_string = '%%prog %s (%s)' % (program_version, program_build_date)

    if argv is None:

        argv = sys.argv[1:]

        # setup option parser
        parser = OptionParser(version=program_version_string)
        # rp_config.json
        parser.add_option("-c", "--con", dest="configFile", default="",
                      help="defines the config file name")
        # https://raw.githubusercontent.com/openshift/release/master/ci-operator/config/rhpit/interop-tests/rhpit-interop-tests-master__ocp-412-quay37.yaml
        parser.add_option("-j", "--job", dest="testJobConf", default="",
                      help="defines the test job config")
        
        log_choices = ("info", "debug")
        parser.add_option("-l", "--loglevel", type="choice", dest='loglevel',
                          choices=log_choices, default="info",
                          help="defines log level controlling log messaging")

       
        # process options
        (opts, args) = parser.parse_args(argv)

        configfile = opts.configFile
        testjobconfig = opts.testJobConf
        loglevel = opts.loglevel
        
        ajobmanager = prow_job.JobManager(testjobconfig)
        ajob = prow_job.Job(periodic_job_name_partial=ajobmanager.periodic_job_name_partial, config=ajobmanager.job_config)
        resultpath = ajob.fetch_test_artifacts()
        #trim results
        payloaddir = resultpath.split('results')[0]
        
        FORMAT = "%(asctime)s %(levelname)s (%(threadName)s) [%(name)s] %(message)s"
        
        # set logging
        if loglevel == "info":
            logging.basicConfig(level=logging.INFO, format=FORMAT)
        else:
            logging.basicConfig(level=logging.DEBUG)

        # set logger name
        logger = logging.getLogger("rpio_service")

        logger.info('#####start rpio preproc client#####')
        logger.debug('Payload dir is %s ' % payloaddir )
        #prepare the rp_preproc command list
        cmd = ["rp_preproc", "-c", configfile, "-d", payloaddir]
        
        # run rp_preproc client here
        try:
            p = subprocess.Popen(cmd,
                                bufsize=1,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
            with p.stdout:
                log_subprocess_output(p.stdout)
            p.wait() 
            rc = p.returncode
            
        except Exception as ex:
            # Get current system exception
            ex_type, ex_value, ex_traceback = sys.exc_info()
            
            # Extract unformatter stack traces as tuples
            trace_back = traceback.extract_tb(ex_traceback)

            # Format stacktrace
            stack_trace = list()

            for trace in trace_back:
                stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (trace[0], trace[1], trace[2], trace[3]))
                
            logger.error("Exception type : %s " % ex_type.__name__)
            logger.error("Exception message : %s" %ex_value)
            logger.error("Stack trace : %s" % stack_trace)
            logger.error('Failed to write test result to report portal.')

def log_subprocess_output(pipe):
    for line in iter(pipe.readline, b''): # b'\n'-separated lines
        logging.info('got line from subprocess: %r', line)
        



        
if __name__ == "__main__":
    sys.exit(main())
