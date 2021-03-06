# -*- coding: UTF-8 -*-
'''
    api tests
    
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

import pytaf_utils
from apilib import ApiLib
import json
import logging
from bs4 import BeautifulSoup


def test_api(args={}):
    # required test_config fields
    settings = args['settings']
    params = args['params']
    var = params.get('var', 'default')
    logging.info("var = %s" % var)
    logging.info("settings = %s" % settings)
    url = settings['url']

    try:
        apilib = ApiLib()
        apilib.some_function()
        return (True, '')
    except:
        return (False, pytaf_utils.formatExceptionInfo())


def test_html_get(args={}):
    ''' example using BeautifulSoup to parse html '''
    settings = args['settings']
    url = settings['url']

    try:
        errors = []
        headers = {}
        url = "www.google.com"
        u = "/index.html"
        lib = ApiLib()
        response = lib.do_get(url, u, args['settings'], headers, False)
        data = response['data']
        soup = BeautifulSoup(data)
        divs = soup.findAll('div')
        for d in divs:
            try:
                logging.info("div style = %s" % d['style'])
            except:
                pass
        return pytaf_utils.verify(len(errors) == 0,
                                'there were errors: %s' % errors)
    except:
        return (False, pytaf_utils.formatExceptionInfo())


def test_simple_get(args={}):
    '''
        example of json parsing from http get
        http://httpbin.org/

        It echoes the data used in your request for any of these types:

        http://httpbin.org/ip Returns Origin IP.
        http://httpbin.org/user-agent Returns user-agent.
        http://httpbin.org/headers Returns header dict.
        http://httpbin.org/get Returns GET data.
        http://httpbin.org/post Returns POST data.
        http://httpbin.org/put Returns PUT data.
        http://httpbin.org/delete Returns DELETE data
        http://httpbin.org/gzip Returns gzip-encoded data.
        http://httpbin.org/status/:code Returns given HTTP Status code.
        http://httpbin.org/redirect/:n 302 Redirects n times.
        http://httpbin.org/cookies Returns cookie data.
        http://httpbin.org/cookies/set/:name/:value Sets a simple cookie.
        http://httpbin.org/basic-auth/:user/:passwd Challenges HTTPBasic Auth.
        http://httpbin.org/hidden-basic-auth/:user/:passwd 404'd BasicAuth.
        http://httpbin.org/stream/:n Streams n–100 lines.
        http://httpbin.org/delay/:n Delays responding for n–10 seconds.
'''
    try:
        errors = []
        headers = {}
        url = "httpbin.org"
        u = "/get"
        lib = ApiLib()
        response = lib.do_get(url, u, args['settings'], headers, False)
        data = json.loads(response['data'])
        logging.info(data)
        origin = data.get('origin', None)
        if origin == None:
            errors.append("did not get expected 'origin' field")
        else:
            logging.info("origin = %s" % origin)

        return pytaf_utils.verify(len(errors) == 0,
                                  'there were errors: %s' % errors)
    except:
        return (False, pytaf_utils.formatExceptionInfo())


def test_simple_post(args={}):
    ''' example of json parsing from http post '''
    try:
        errors = []
        headers = {}
        request = ''
        url = "httpbin.org"
        u = "/post"
        lib = ApiLib()
        response = lib.do_post(url, u, request,
                               args['settings'], headers, False)
        data = json.loads(response['data'])
        logging.info(data)
        origin = data.get('origin', None)
        if origin == None:
            errors.append("did not get expected 'origin' field")
        else:
            logging.info("origin = %s" % origin)

        return pytaf_utils.verify(len(errors) == 0,
                                  'there were errors: %s' % errors)
    except:
        return (False, pytaf_utils.formatExceptionInfo())
