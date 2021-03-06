#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    test utility methods
    
    Copyright (C) 2012  Tom Lichtenberg

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
'''

import os
import httplib
import urllib
import urllib2
import base64
import json
import MySQLdb
from datetime import datetime
from datetime import date, timedelta
import sys
import traceback
import time
import random
import thread
import logging
from operator import itemgetter

DEBUG = sys.flags.debug


def verify(expression, message):
    ''' called by tests for pass and fail '''
    print(expression)
    if expression == -1 or expression == False:
        error_message = message
        logging.error("Error: %s" % error_message)
        return (False, error_message)
    else:
        error_message = ''
        return (True, error_message)


def get_date_string(offset=0):
    ''' get the date, offset in days (1 for yesterday, 2 for two days ago'''
    d = date.today() - timedelta(offset)
    datestr = d.strftime('%m%d%y')
    return datestr


def anystring_as_utf8(s, accept_utf8_input=False):
    if type(s) is str:
        return s
    else:
        return s.encode('utf-8')


def str2bool(v):
    '''convert string to boolean
    '''
    return v.lower() in ("yes", "true", "t", "1")


def bool2str(v=True):
    '''convert boolean to string
    '''
    if v:
        return "true"
    else:
        return "false"


def get_params(config, test):
    '''
       get params for a test from the test config file
    '''
    # print "test: ", test
    test_includes = config['tests']['includes']
    for i in range(0, len(test_includes)):
        included_methods = test_includes[i]['methods']
        for k in range(0, len(included_methods)):
            test_name = included_methods[k]['name']
            if test_name == test:
                params = included_methods[k]['params']
                logging.debug("test case params: %s" % params)
                return params
    return None


def get_all_modules(config={}):
    '''
       get list of modules (python test files) from the test config file
    '''
    # print "test: ", test
    modules = []
    try:
        test_includes = config['tests']['includes']
        for i in range(0, len(test_includes)):
            modules.append(test_includes[i]['module'])
    except:
        pass
    return modules


def get_all_tests(config, modules=[], load_test=False):
    '''
        get an array of all the test names in the config file

        for load tests, add the test name as many times as its load_mix value
        i.e. once for "load_mix = 1", zero for "load_mix = 0",
        10 for "load_mix = 10"
        this will determine the probability of the test being called
    '''
    module_names = []
    for m in modules:
        module_names.append(str(m.__name__))
    settings = config['settings']
    global_load_mix = settings.get("load_mix", 1)
    tests = []
    test_includes = config['tests']['includes']
    for i in range(0, len(test_includes)):
        # if this module is not to be included,
        # skip to the next test_includes item
        module = test_includes[i]['module']
        if module in module_names:
            included_methods = test_includes[i]['methods']
            for k in range(0, len(included_methods)):
                test_name = included_methods[k]['name']
                if load_test == True:
                    # params can override load_mix per test
                    params = included_methods[k]['params']
                    load_mix = params.get("load_mix", global_load_mix)
                    for i in range(int(load_mix)):
                        logging.debug('appending %s' % test_name)
                        tests.append(test_name)
                    load_mix = global_load_mix   # reset
                else:  # for non-load test. just add the test case!
                    logging.debug('appending %s' % test_name)
                    tests.append(test_name)
    return tests


def post_results(results=[], settings={}, db_config={},
                 total_passed=0, total_failed=0):
    db = db_config.get('db', {})
    database = db.get("db_name", 'automation')
    host = db.get("db_host", 'localhost')
    user = db.get("db_user", 'root')
    password = db.get("db_password", '5ecre3t!')
    conn = MySQLdb.Connection(db=database, host=host, user=user, passwd=password)
    mysql = conn.cursor()    

    t = str(datetime.now())
    dates = t.rsplit(' ', 2)
    created_at = dates[0] + " " + dates[1]
    for i in range(0, len(results)):
        try:
            # required fields
            test_method = results[i]['test_method']
            module = results[i]['module']
            status = results[i]['status']
            message = results[i].get('message', '')
            sql = """ INSERT INTO test_results (test_method, module, status, message, date) VALUES ('%s', '%s', '%s', '%s', '%s') """ % (test_method, module, status, message, created_at)
            print(sql)
            mysql.execute(sql)
        except:
            logging.error("SQL Error: %s" % formatExceptionInfo())
            continue

    mysql.close()
    conn.close()


def formatExceptionInfo(level=6):
    error_type, error_value, trbk = sys.exc_info()
    tb_list = traceback.format_tb(trbk, level)
    s = "Error: %s \nDescription: %s \nTraceback:" % (error_type.__name__,
                                                      error_value)
    for i in tb_list:
        s += "\n" + i
    return s
