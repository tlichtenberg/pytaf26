'''
  py.test wrapper class
  allows pytaf to be run via py.test
  
  invoke using long commands (--config, --test) as the short commands would be intercepted by py.test
  example:
     py.test --config api_config.json  --test test_pytest_integration

'''

import sys
from pytaf import Pytaf

def pytest_addoption(parser):
    ''' add ptest command-line options '''
    # print "called addoption to allow for custom command line options"
    parser.addoption("--config", action="store", help="json config file")
    parser.addoption("--browser", action="store", help="json config file")
    parser.addoption("--config_file", action="store", help="json config file")
    parser.addoption("--db", default="false", type="string", help="json config file")
    parser.addoption("--excluded", action="store", help="json config file")
    parser.addoption("--log_file", action="store", help="json config file")
    parser.addoption("--grid_address", action="store", help="json config file")
    parser.addoption("--log_level", action="store", help="json config file")
    parser.addoption("--modules", action="store", help="json config file")
    parser.addoption("--root_directory", action="store", help="json config file")
    parser.addoption("--suite", action="store", help="json config file")
    parser.addoption("--test", action="store", help="json config file")
    parser.addoption("--url", action="store", help="json config file")
    parser.addoption("--fw_version", action="store", help="json config file")
    parser.addoption("--webdriver", action="store", help="json config file")
    parser.addoption("--extra", action="store", help="json config file")
    parser.addoption("--loadtest_settings", action="store", help="json config file")

def pytest_configure(config):
    ''' unused '''
    print "called pytest_configure"
    #if config.option.config:
    #    print "called configure with %s" % config

def pytest_cmdline_preparse(args):
    #print args
    ''' instantiate Pytaf and invoke with command-line args 
        sys.exit prevents py.test from doing anything of its own
        we may want to change that in the future to allow py.test output or other integrations
    '''
    pytaf = Pytaf()
    pytaf.setup(args)
    sys.exit(0)