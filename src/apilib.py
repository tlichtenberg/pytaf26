#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
    library for api calls
'''
import os
import sys
import logging
import httplib
import urllib
import urllib2
import base64
import thread
import time
import pytaf_utils
from BeautifulSoup import BeautifulSoup

DEBUG = sys.flags.debug


class ApiLib:

    def __init__(self):
        self.field = None

    def some_function(self):
        logging.info("this is one dandy function you got here!")
        return True
    
    def anystring_as_utf8(self, s,accept_utf8_input=False): # accept str or unicode, and output utf-8
        if type(s) is str:
            return s
        else:
            return s.encode('utf-8')
    
    def do_get(self, url, u, settings={}, https=True):
        u = u.replace(" ", "%20")
        api_qa_cert = os.getenv("PYTAF_HOME") + "/resources/cert.pem"
        CERT_FILE = settings.get("cert_file", api_qa_cert) # os.getenv("TEST_HOME") + "/resources/cert.pem"
        content_length = settings.get('content_length', None)
        host = settings.get('host',url)
        content_type = settings.get('content_type', None)
        cookie = settings.get('cookie',None) 
        if DEBUG:
            logging.debug("*** GET *** (thr: %s, t: %s) %s" % (thread.get_ident(), `int(time.time())`, url + u))
        else:
            logging.info("*** GET *** %s" % url + u)
        if https == True:
            conn = httplib.HTTPSConnection(url, cert_file=CERT_FILE)
        else:
            conn = httplib.HTTPConnection(url)
        headers = {}
        if host != None: headers['host'] = host
        if cookie != None: headers['Set-Cookie'] = cookie
        if content_length != None: headers['Content-Length'] = content_length
        if content_type != None: headers['Content-Type'] = content_type
        start_time = time.time()
        logging.debug("%s" % headers)
        conn.request("GET", u, '', headers)
        response = conn.getresponse()
        end_time = time.time()
        logging.debug("%s, %s" % (response.status, response.reason))
        logging.debug("http response time: (thr: %s, t: %s)" %
                (thread.get_ident(), round(float(end_time - start_time), 2)))
        d = response.read().decode()  # read() returns a bytes object
        logging.debug("%s" % d)
        return {"data": d, "status": response.status,
                "reason": response.reason}

    def do_post(self, url, u, request, settings = {}, https=True ):
        u = u.replace(" ", "%20")
        if DEBUG:
            logging.debug("*** POST *** (thr: %s, t: %s) %s" % (thread.get_ident(), `int(time.time())`, url + u))
        else:
            logging.info("*** POST *** %s" % url + u)
        params = self.anystring_as_utf8(request)
        if params: logging.debug("params: %s" % params)
        api_qa_cert = os.getenv("PYTAF_HOME") + "/resources/cert.pem"
        CERT_FILE = settings.get("cert_file", api_qa_cert) # os.getenv("TEST_HOME") + "/resources/cert.pem"
        content_length = settings.get('content_length', None)
        host = settings.get('host',url)
        content_type = settings.get('content_type', None)
        cookie = settings.get('cookie',None) 
        headers = {"Content-type": "text/xml"}
        if content_length != None: headers['Content-Length'] = content_length
        if content_type != None: headers['Content-Type'] = content_type
        if host != None: headers['host'] = host
        if cookie != None: headers['Set-Cookie'] = cookie
        logging.debug("headers: %s" % headers)
        if https == True:
            conn = httplib.HTTPSConnection(url, cert_file=CERT_FILE)
        else:
            conn = httplib.HTTPConnection(url)
        start_time = time.time()
        conn.request("POST", u, params, headers)
        response = conn.getresponse()
        end_time = time.time()
        logging.debug("%s, %s" % (response.status, response.reason))
        logging.debug("http response time: (thr: %s, t: %s)" %
                (thread.get_ident(), round(float(end_time - start_time), 2)))
        d = response.read().decode()  # read() returns a bytes object
        logging.debug("%s" % d)
        return {"data": d, "status": response.status,
                "reason": response.reason}

    def process_url(self, u):
        '''
            make the url python-http-happy by stripping off the front part
        '''
        if u.find("http://") >= 0:
            u = u[7:]
        if u.find("https://") >= 0:
            u = u[8:]
        return u
