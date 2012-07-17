#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
    web tests (selenium webdriver tests)
    
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

import sys
import logging
import pytaf_utils
from weblib import WebLib

DEBUG = sys.flags.debug

def test_web(args={}):
    try:
        # initialize the error strings array
        errors = []

        # parse the global settings and test method
        # params from the args provided
        settings = args['settings']
        params = args['params']

        # do some selenium specific test stuff ...
        goto_url = params.get('url', 'http://www.google.com')
        lib = WebLib(settings)
        lib.driver.get(goto_url)
        element = lib.driver.find_element_by_id('gbqfq')
        if element == None:
            errors.append('did not find the google input element')
        else:
            logging.info('found the google input element')

        # call the utility method to verify the absence or errors or
        # pack up the error messages if any
        return pytaf_utils.verify(len(errors) == 0,
                                  'there were errors: %s' % errors)
    except Exception as inst:
        logging.error(inst)
        # fail on any exception and include a stack trace
        return (False, pytaf_utils.formatExceptionInfo())
    finally:
        # cleanup
        lib.driver.quit()
