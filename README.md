pytaf26
=======

python test automation framework, version for python 2.6

pytaf
    by tom lichtenberg
    
    Pytaf is a general purpose python test automation framework. 
    The framework can be used to run a variety of tests, including browser tests (using Selenium) and
    api tests (using Http)
    
    Pytaf on Windows setup:
    -----------------------
    Python2.6 
    other installers for Windows can be found at
        http://www.lfd.uci.edu/~gohlke/pythonlibs/, 
       specifically the Windows64 bit installers for python 2.6 modules
    
    run: python-2.6.amd64 (exe to install python 2.6)
    run: ez_setup_26 (installs python setuptools)
    run: MySQL-python-1.2.2.win-amd64-py2.6 (exe to install the python mysql module)
    
    run: python setup.py install:   
         selenium-2.XX.tar.gz (tar zxvf, cd into the new folder and run 'python setup.py install)
         BeautifulSoup-3.2.0  (used for html parsing, needed for API tests, including Web Services and External Control Protocol)
    
    Using Pytaf
    -----------
    
            Set the environment variable PYTAF_HOME to where you checked out the code - e.g. ~/github/pytaf26.
    
            The main module is src/pytaf.py and takes a number of command line arguments:
                '-b', '--browser', default=None, type='string
                '-c', '--config_file', default='', type='string'
                '-d', '--db', default='false', type='string'
                '-e', '--excluded', default=None, type='string'
                '-g', '--grid_address', default=None, type='string'
                '-m', '--modules', default=None, type='string'
                '-t', '--test', default='', type='string'
                '-u', '--url', default=None, type='string'
                '-y', '--test_type', default='None', type='string'
                '-z', '--loadtest_settings', default=None, type='string'
    
                -b, --browser is used for Selenium tests to specify the browser type
                -c, --config is required and all other arguments are optional. The config file must reside in $TEST_HOME/config
                -d, --db defines whether to write the test results to the database. this should be set to false except for nightly regression tests
                -e, --excluded to optionally exclude a test or tests (comma-separated list)
                -g, --grid_address is used to override the test_host:test_port settings for the Selenium Server
                -m, --modules if specified denotes a comma-separated list of modules to be included from the config file
                -t, --test is set to None (by default), in which case p_test will attempt to run all the 
                        tests in the test config file, otherwise it will attempt to run the test(s) specified 
                        (multiple tests are set with a comma-separated list of their names)
                -u, --url is used to override the url in the config file settings. 
                -y, --test_type is used to determine whether to run a locally running selenium server (if "selx") or "load" for load testing
                -z, --loadtest_settings is a colon-separated string for load tests including test_duration:max_threads:ramp_steps:ramp_delay:throttle_rate (e.g. 3600:1000:10:60:1 for run a load test for 6 hours, ramping up to 1000 threads in 10 steps, with a step every 60 seconds, and a 1-second delay added to each thread after it completes its test)
    
    
                EXAMPLES:
                   non-web test
                     cd %PYTAF_HOME%/src
                     python pytaf.py -c api_config.json -t test_api
    
                   web test: for running selenium tests locally:
                    in a terminal window:
                      cd %PYTAF_HOME%/lib
                      java -jar selenium-server-standalone-2.24.1.jar
                    then in another terminal window:
                      python pytaf.py -c webtest_config.json -t test_web -b *firefox
                      
    Overriding Config Files
    -----------------------
    
    There are situations where we might need to vary a test configuration 
    from one platform to another. For example, we need to have different 
    settings for different browsers or for different Roku Players, but we 
    don't want to duplicate the entire config file just to alter a few things. 
    
    While this can be handled, in most cases, by command-line options, an 
    alternate and more cleaner method is to use "override" config files. 
    These are config files which include an "import" statement which tells 
    pytaf to import the more general config file, while overriding any settings 
    which are in the override file.
    
    For example, the web_admin_config.json file includes all of the settings, 
    test names and parameters for the admin.roku.qa.com web site. You could pass 
    this config file to pytaf and by using the -b option, override the default 
    browser setting. Or you could use a web_admin_ie9_config.json file, which looks like this:
    
      {
      "import": "web_admin_config.json",
      "settings": 
      { 
         "browser": "*ie9",
         "testrail_testsuite": "Automation_Web_IE9_Windows7"
      }
    
    The entire web_admin_config.json file will be loaded, but its 'browser' and 
    'testrail_testsuite' settings will be overridden by those in the web_admin_ie9_config.json file
    
    Instead of using the -e command-line option to exclude certain tests from the 
    test run, the override config file can contain an 'additional_excludes' section 
    which will perform the same function. For example, from web_admin_ie9_config.json:
    
       "additional_excludes":
       [  
          "test_admin_tos",
          "test_admin_autolink"              
       ] 
    
    These tests will be excluded from the test run
    
    It is also possible to override parameters for specific tests, for example:
    
       "test_overrides":
       {
          "test_owner_add_private_channel_invalid_code": { "bad_code" : "AAAAACHECKITOUT" }
       }
    
    This example would replace the param 'bad_code' which was originally defined in the imported config file
    for the test named test_owner_add_private_channel_invalid_code

    -------------------
    py.test integration
    -------------------

    pytaf can be run via py.test
  
  invoke using long commands (--config, --test) as the short commands would be intercepted by py.test
  example:
     py.test --config api_config.json  --test test_pytest_integration
    
