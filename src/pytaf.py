'''
    test driver
    
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
import sys
sys.path.append(os.getenv('PYTAF_HOME'))
import optparse
import json
import pytaf_utils
import time
import datetime
import thread
import logging
from load_runner import LoadRunnerManager
from optparse import (OptionParser,BadOptionError,AmbiguousOptionError)

DEBUG = sys.flags.debug

class PassThroughOptionParser(OptionParser):
    """
    An unknown option pass-through implementation of OptionParser.

    When unknown arguments are encountered, bundle with largs and try again,
    until rargs is depleted.  

    sys.exit(status) will still be called if a known argument is passed
    incorrectly (e.g. missing arguments or bad argument types, etc.)        
    """
    def _process_args(self, largs, rargs, values):
        while rargs:
            try:
                OptionParser._process_args(self,largs,rargs,values)
            except (BadOptionError,AmbiguousOptionError), e:
                largs.append(e.opt_str)

class Pytaf:
    ''' Python2.6 test driver capable of running any arbitrary python
        methods in modules defined by json config files '''
    def __init__(self):
        ''' results object is used for collecting test results for output
            and database reporting '''
        self.results = []

    def setup(self, args):
        # Parse command line options
        parser = PassThroughOptionParser()
        parser.add_option('-b', '--browser', default=None, type='string')
        parser.add_option('-c', '--config_file', default=None, type='string')
        parser.add_option('-d', '--db', default="false", type='string')
        parser.add_option('-e', '--excluded', default=None, type='string')
        parser.add_option('-g', '--grid_address', default=None, type='string')
        parser.add_option('-l', '--logfile', default=None, type='string')
        parser.add_option('-m', '--modules', default=None, type='string')
        parser.add_option('-t', '--test', default=None, type='string')
        parser.add_option('-u', '--url', default=None, type='string')
        parser.add_option('-y', '--test_type', default=None, type='string')
        parser.add_option('-z', '--loadtest_settings', default=None,
                                                       type='string')
        options, args_out = parser.parse_args(args)

        if options.config_file == None:
            print('-c (--config_file) is required')
            sys.exit(-1)

        if options.logfile != None:
            ''' redirect stdout to the logfile '''
            f = open(options.logfile, "a", 0)
            sys.stdout = f

        if options.excluded != None:
            ''' build a list of tests explicitly excluded from the
            command-line option '''
            excluded_list = options.excluded.split(',')
        else:
            excluded_list = None

        ''' load the config file '''
        try:
            config_path = os.getenv('PYTAF_HOME') + os.sep + "config" + os.sep
            f = open("%s%s" % (config_path, options.config_file), 'r').read()
            config = json.loads(f)
            
            # allow for the possibility of nested config files
            test_overrides = {}
            config_to_import = config.get('import', None)
            if config_to_import != None:
                top_config = config
                f = open("%s%s" % (config_path, config_to_import), 'r').read()           
                imported_config = json.loads(f)
                # let any original config 'settings' override the imported config's settings by merging the dictionaries 
                new_settings = dict(imported_config['settings'].items() + top_config['settings'].items())
                # the new, merged config's settings
                config['settings'] = new_settings
                config['tests'] = imported_config['tests']

                # the params dictionary of individual tests can be overridden, e.g.
                # "test_overrides":
                #   {
                #     "test_owner_add_private_channel_invalid_code": { "bad_code" : "AAAAACHECKITOUT" }
                #   }
                try:
                    test_overrides = top_config.get('test_overrides', {})
                    print('test_overrides = %s' % test_overrides)
                except Exception as inst:
                    print('eh ? %s' % inst)
                
                # additional excludes can be added to the base config file's excluded tests list, e.g:
                #"additional_excludes":
                #   [  
                #      "test_owner_manage_subscriptions"
                #   ]
                additional_excludes = top_config.get('additional_excludes', [])
                if excluded_list == None and len(additional_excludes) > 0:
                    excluded_list = additional_excludes
                else:
                    for excluded in additional_excludes:
                        excluded_list.append(excluded)                                 
        except:
            print(pytaf_utils.formatExceptionInfo())
            print("problem with config file %s%s" %
                  (config_path, options.config_file))
            sys.exit()

        config['settings']['config_file'] = options.config_file
        
        try:  # try to open the default db_config file
            f2 = open("%s%s" % (config_path, "db_config.json"), 'r').read()
            db_config = json.loads(f2)
        except:
            db_config = {}

        # command-line -u overrides config file for url
        if options.url != None:
            config['settings']['url'] = options.url  # for browser tests

        # command-line -b overrides config file for browser
        # can be in the form of 'Firefox' or 'Firefox,10,WINDOWS'
        if options.browser != None:
            config['settings']['browser'] = options.browser

        # command-line -g overrides config file setting for test_host (and optionally test_port as well)
        # used for selenium_grid or local selenium server
        if options.grid_address != None:
            if options.grid_address.find(":") >= 0:
                g = options.grid_address.split(":")
                config['settings']['test_host'] = g[0]
                config['settings']['test_port'] = int(g[1])
            else:
                config['settings']['test_host'] = options.grid_address

        # reset the settings object for passing on to test methods
        settings = config['settings']
        
        # initialize the root logger
        self.setup_logger(settings)

        # dynamically import all modules found in the config file
        if options.modules == None:
            modules_array = pytaf_utils.get_all_modules(config)
        else:  # only load the specified module(s) from the config file
            modules_array = options.modules.split(",")
        logging.debug('modules: %s' % modules_array)
        mapped_modules = map(__import__, modules_array)

        passed = 0
        failed = 0

        if options.test_type == 'load':
            '''
             the command-line may override load_test_settings with
             -z --loadtest_settings in the form of
             duration:max_threads:ramp_steps:ramp_interval:throttle_rate
             e.g. 3600,500,10,30,1
             which would run the load test for 1 hour (3600 seconds)
             ramping up to a total of 500 threads in 10 steps
             (each step would add 50 threads (500/10))
             and these batches of threads would be added in
             30 second installments (approximately)
             the final value (throttle_rate=1) is used to
             brake the entire load test operation by sleeping for
             that amount (in seconds) between chunks of test case allocations
            '''
            if options.loadtest_settings != None:
                p = options.loadtest_settings.split(",")
                if len(p) == 5:
                    config['settings']['load_test_settings'] = \
                    {"duration": int(p[0]),
                     "max_threads": int(p[1]),
                     "ramp_steps": int(p[2]),
                     "ramp_interval": int(p[3]),
                     "throttle_rate": int(p[4])}
                else:
                    logging.fatal('load test settings are not complete.')
                    logging.fatal('they must be in the form of' \
                'duration:max_threads:ramp_steps:ramp_interval:throttle_rate')
                    sys.exit(-1)
            # now start the load test
            passed, failed = self.do_load_test(mapped_modules, config)
        # if --test is specified, try and get the params and run each one
        elif options.test != None:
            ts = options.test.split(",")
            for i in range(0, len(ts)):
                test = ts[i]
                if self.test_excluded(test, excluded_list) == False:
                    params = pytaf_utils.get_params(config, test)
                    if params == None:
                        logging.fatal("could not find params for test %s" % test)
                        sys.exit()
                    else:
                        if test_overrides.get(test, None):
                            params = dict(params.items() + test_overrides[test].items())
                        status = self.do_test(mapped_modules, settings,
                                              test, params)
                        if status == True:
                            passed = passed + 1
                        else:
                            failed = failed + 1
                else:
                    logging.info("%s is on the excluded list" % test)
        # if --test is not specified, collect and run all the
        # tests in the config file
        else:
            tests = pytaf_utils.get_all_tests(config, mapped_modules)
            for test in tests:
                if self.test_excluded(test, excluded_list) == False:
                    params = pytaf_utils.get_params(config, test)
                    if params != None:
                        if test_overrides.get(test, None):
                            params = dict(params.items() + test_overrides[test].items())
                        status = self.do_test(mapped_modules, settings,
                                              test, params)
                        if status == True:
                            passed = passed + 1
                        else:
                            failed = failed + 1
                else:
                    logging.info("%s is on the excluded list" % test)

        logging.info("---------------")
        logging.info("Tests Run: %s" % (passed + failed))
        logging.info("Passed:    %s" % passed)
        logging.info("Failed:    %s" % failed)

        print_results = []
        for r in self.results:
            print_results.append(r['status'] + " " + r['test_method'])

        for r in sorted(print_results):
            logging.info(r)

        # post results to the database
        if pytaf_utils.str2bool(options.db) == True:
            pytaf_utils.post_results(self.results, settings,
                                     db_config, passed, failed)

    def test_excluded(self, test, excluded_list):
        if excluded_list != None:
            for e in excluded_list:
                if test == e:
                    return True
        return False

    def do_test(self, modules, settings, test, params):
        result = (False, "error")
        start_time = end_time = elapsed_time = 0
        found_module = None
        test_was_found = False
        for m in modules:
            try:
                logging.debug("do test %s from module %s" % (test, m))
                methodToCall = getattr(m, test)
                found_module = str(m)
                test_was_found = True
                start_time = int(time.time())
                logging.info("------------")
                logging.info(" starting test: %s" % test)
                if settings.get('browser', None):
                    logging.critical(" browser:       %s" % settings['browser'])
                logging.info(" config file:   %s" % settings['config_file'])
                logging.info(" start time:    %s" % datetime.datetime.now())
                logging.info("------------")
                args = {"settings": settings, "params": params}
                result = methodToCall(args)
                end_time = int(time.time())
                elapsed_time = end_time - start_time
            except:
                logging.debug("exception from methodToCall: %s" %
                          sys.exc_info()[0])
                continue

        if test_was_found == False:
            logging.error('error: pytaf did not find the test case (%s) \
            in the modules defined in the config file (%s)' %
            (test, str(modules)))
            return

        # tests return (True|False, String)
        error_message = str(result[1])  # could be Exception, hence the cast
        status = result[0]

        try:
            if status == True:  # any return value except False is PASSED
                status_string = "PASSED"
            else:
                status_string = "FAILED"

            module_string = ""
            if found_module != None:
                idx1 = found_module.rfind(os.sep) + 1
                idx2 = found_module.find(".py")
                module_string = found_module[idx1:idx2]

            self.results.append({"test_method":  test,
                                 "status": status_string,
                                 "message": error_message[:1024],
                                 "module": module_string})

            if status != False:
                result_str = "RESULT ===> PASSED: %s" % test
            else:
                result_str = "RESULT ===> FAILED: %s, %s" % \
                (test, pytaf_utils.anystring_as_utf8(error_message))
            if elapsed_time > 0:
                result_str = "%s, elapsed time: %s seconds" % \
                (result_str, str(elapsed_time))
            logging.info("%s\n---------------" % result_str)
        except:
            logging.error(pytaf_utils.formatExceptionInfo())

        return status

    def do_load_test(self, modules, config):
        '''
        intent is to run tests randomly (on multiple threads)
        calculated by threads and rate,
        for the period of duration (in minutes)
        '''
        # get a list of all the test method names from the config file
        tests = pytaf_utils.get_all_tests(config, modules, True)
        logging.debug('found these tests: %s' % tests)

        manager = LoadRunnerManager(config, tests)
        tests_run, passed, failed = manager.start()

        count = 0
        for (total, completed) in tests_run.items():
            count = count + completed
            logging.info(completed, total)
        logging.info("------------\n%s tests run" % str(count))

        return passed, failed
    
    def setup_logger(self, settings):
        # initialize the root logger
        # all modules can use it by calling logging.debug(),
        # logging.info(), logging.warning() or logging.error()
        FORMAT = '%(levelname)s:%(message)s'
        level = settings.get('log_level', 'info')  
        log_file = settings.get('log_file', None)
        date_tag = datetime.datetime.now().strftime("%Y-%m-%d")
        if log_file != None:
            log_file = "%s_%s" % (log_file, date_tag)
        if DEBUG:  # python -d overrides log_level in settings
            if log_file == None:
                logging.basicConfig(format=FORMAT, level=logging.DEBUG)
            else:
                logging.basicConfig(format=FORMAT, level=logging.DEBUG, filename=log_file, filemode='w')
        else:
            if level.lower() == 'debug':
                if log_file == None:
                    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
                else:
                    logging.basicConfig(format=FORMAT, level=logging.DEBUG, filename=log_file, filemode='w')
            elif level.lower() == 'info':
                if log_file == None:
                    logging.basicConfig(format=FORMAT, level=logging.INFO)
                else:
                    logging.basicConfig(format=FORMAT, level=logging.INFO, filename=log_file, filemode='w')
            elif level.lower() == 'warning':
                if log_file == None:
                    logging.basicConfig(format=FORMAT, level=logging.WARNING)
                else:
                    logging.basicConfig(format=FORMAT, level=logging.WARNING, filename=log_file, filemode='w')
            else:
                if log_file == None:
                    logging.basicConfig(format=FORMAT, level=logging.ERROR)
                else:
                    logging.basicConfig(format=FORMAT, level=logging.ERROR, filename=log_file, filemode='w')

if __name__ == "__main__":
    pytaf = Pytaf()
    pytaf.setup(sys.argv[1:])
