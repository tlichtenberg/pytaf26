#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
    library for api calls
    
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
import logging
import httplib
import urllib
import urllib2
import base64
import thread
import time
import json
from lxml import etree
from lxml import objectify
from lxml.etree import tostring
from datetime import datetime
import pytaf_utils
from bs4 import BeautifulSoup

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
        CERT_FILE = settings.get("cert_file", api_qa_cert) 
        if DEBUG:
            logging.debug("*** GET *** (thr: %s, t: %s) %s" % (thread.get_ident(), `int(time.time())`, url + u))
        else:
            logging.info("*** GET *** %s" % url + u)
        if https == True:
            conn = httplib.HTTPSConnection(url, cert_file=CERT_FILE)
        else:
            conn = httplib.HTTPConnection(url)
        headers = self.get_headers(url, "", settings)        
        logging.info("headers = %s:" % headers)
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
        headers = self.get_headers(url, request, settings)        
        logging.info("headers = %s:" % headers)
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
    
    def do_curl_xml(self, url, u, request, settings = {}, curl_method= "POST", https=True, ignore_certs=False, connection_timeout=60, do_log=True):
        return self.do_curl(url, u, request, settings, curl_method, https, "xml", ignore_certs, connection_timeout, do_log)

    def do_curl_json(self, url, u, request, settings = {}, curl_method= "POST", https=True, ignore_certs=False, connection_timeout=60, do_log=True):
        return self.do_curl(url, u, request, settings, curl_method, https, "json", ignore_certs, connection_timeout, do_log)
    
    def do_curl_str(self, url, u, request, settings = {}, curl_method= "POST", https=True, ignore_certs=False, connection_timeout=60, do_log=True):
        return self.do_curl(url, u, request, settings, curl_method, https, "str", ignore_certs, connection_timeout, do_log)
    
    def do_curl_raw(self, url, u, request, settings = {}, curl_method= "POST", https=True, ignore_certs=False, connection_timeout=60, do_log=True):
        return self.do_curl(url, u, request, settings, curl_method, https, "raw", ignore_certs, connection_timeout, do_log)
        
    def do_curl(self, url, u, request, settings = {}, curl_method= "POST", https=True, return_type="json", ignore_certs=False, connection_timeout=60, do_log=True):
        response = { "data": "", "status": "", "reason": "", "headers": "" }
        rheaders = ""
        status = ""
        reason = ""
        
        # settings['httplib'] can override the use of pycurl and redirect to httlib, just as settings['webdriver'] can redirect selenium to webdriver for browser tests
        if pytaf_utils.str2bool(settings.get('httplib', 'false')) == True:
            if curl_method.upper() == "POST":
                logging.info("using httplib to POST instead of pycurl due to settings['httplib']")
                return self.do_post(url, u, request, settings, https, connection_timeout, do_log)
            elif curl_method.upper() == "GET":
                logging.info("using httplib to GET instead of pycurl due to settings['httplib']")
                return self.do_get(url, u, settings, https, connection_timeout, do_log)
        
        try:
            import pycurl
        except:
            return response
        
        try:         
            # handle json stuff
            if type(request) == dict:
                request = json.dumps(request)
            if len(request) > 0:
                if do_log: 
                    logging.info("request = %s" % request)
            
            # setup response stuff
            import StringIO
            body = StringIO.StringIO()
            response_headers = StringIO.StringIO()
            c = pycurl.Curl()
            if https:
                if url.find("http") < 0:
                    the_url = "https://" + url + u
                else:
                    the_url = url + u
                if settings.get('use_ssl', False) == True:
                    c.setopt(c.SSLVERSION, c.SSLVERSION_SSLv3)
                else: 
                    c.setopt(c.SSLVERSION, c.SSLVERSION_TLSv1)
                    
                if settings.get('verify_peer', True) == False:
                    c.setopt(c.SSL_VERIFYPEER, False);    
            else:
                if url.find("http") < 0:
                    the_url = "http://" + url + u
                else:
                    the_url = url + u
            c.setopt(c.WRITEFUNCTION, body.write)
            c.setopt(c.HEADERFUNCTION, response_headers.write)
            
            # optional bitrate limiting
            if settings.get("bitrate_limit", None) != None:
                c.setopt(c.MAX_RECV_SPEED_LARGE, int(settings.get("bitrate_limit")))
            
            # handle method types
            if curl_method == "POST":
                c.setopt(c.POST, 1)
                c.setopt(c.POSTFIELDS, str(request))
            elif curl_method == "PUT":
                c.setopt(c.CUSTOMREQUEST, "PUT")
                c.setopt(c.POSTFIELDS, str(request))
            elif curl_method == "DELETE":
                c.setopt(c.CUSTOMREQUEST, "DELETE")
                # c.setopt(c.POSTFIELDS, str(request))
            #else: # "GET"
            #    c.setopt(c.GET, 1) # no such setting. pyCurl defaults to GET
                   
            # set basic cURL options   
            c.setopt(c.URL, str(the_url))
            # c.VERBOSE is way too verbose - only enable for temporary debugging
            #if DEBUG: c.setopt(c.VERBOSE, 1)
            c.setopt(c.FOLLOWLOCATION, 1)
            c.setopt(c.MAXREDIRS, 5)
            c.setopt(c.CONNECTTIMEOUT, connection_timeout)
            #c.setopt(c.TIMEOUT, connection_timeout)
            
            # handle optional cert stuff
            CERT_FILE, CACERT, KEY_FILE = self.get_cert_paths(settings) 
            if ignore_certs == False:
                if CERT_FILE:
                    c.setopt(c.SSLCERT, str(CERT_FILE)) 
                    c.setopt(c.SSLCERTTYPE, 'PEM')          
                    
                    if CACERT:
                        c.setopt(c.CAINFO, str(CACERT)) 
            
                    if KEY_FILE:
                        c.setopt(c.SSLKEY, str(KEY_FILE))
                        c.setopt(c.SSLKEYTYPE, "PEM")
                else:
                    #logging.debug('ignore certs')
                    c.setopt(c.SSL_VERIFYHOST, False);  
                    c.setopt(c.SSL_VERIFYPEER, False); 
            else:
                c.setopt(c.SSL_VERIFYHOST, False);  
                c.setopt(c.SSL_VERIFYPEER, False);       
               
            # set headers  
            headers = self.get_headers(url, request, settings)        
            if do_log: logging.info("headers = %s:" % headers)
            c.setopt(pycurl.HTTPHEADER, headers)            
            # display request params, if any
            if do_log:
                if (curl_method == "POST" or curl_method == "PUT") and len(request) > 0: 
                    logging.critical("*** %s *** [%s] %s (%s)" % (curl_method, datetime.now().strftime("%H:%M.%S"), the_url, request))
                else:
                    logging.critical("*** %s *** [%s] %s" % (curl_method, datetime.now().strftime("%H:%M.%S"), the_url))
            # send it
            c.perform()
            
            # get the response
            if return_type != "raw":
                response = body.getvalue().decode("utf-8")
            else:
                response = body.getvalue()
            rheaders = response_headers.getvalue().decode("utf-8")
            rheaders_array = rheaders.split("\n")
            status = rheaders_array[0][rheaders_array[0].index(" "):rheaders_array[0].index(" ") + 4].strip()
            reason = rheaders_array[0][rheaders_array[0].index(" ") + 4:].strip()
            if do_log: 
                logging.info("http status = %s, %s" % (status,reason))
            if do_log: 
                if len(response) > 0: 
                    logging.info("response = %s:" % response)
            c.close()
        except Exception as inst:
            logging.error(inst)
            
        if return_type == "json":
            return response
        if return_type == "raw":
            return { "data": response, "status": status, "reason": reason, "headers": rheaders } 
        elif return_type == "xml":
            try:
                data = objectify.fromstring(response)
                return { "data": data, "status": status, "reason": reason, "headers": rheaders } 
            except Exception as inst:
                logging.debug(inst)
                try:
                    data = objectify.fromstring(str(response)) # converts from unicode if needed
                    return { "data": data, "status": status, "reason": reason, "headers": rheaders } 
                except Exception as inst2:
                    logging.debug(inst2)
                    return { "data": "", "status": status, "reason": reason, "headers": rheaders } 
        else:
            return { "data": response, "status": status, "reason": reason, "headers": rheaders } 
        
    def get_headers(self, url, request, settings):
        headers = []
        dev_id = settings.get('dev_id', None)
        serial_number = settings.get('linked_serial_number', None)  # Giga XD linked to auto_test@roku.com on qa domain
        model_number = settings.get('linked_model_number', None) 
        culture_code = settings.get('culture_code', None)
        content_type = settings.get('content_type', 'text/xml')
        content_length = settings.get('content_length', None)
        reserved_version = settings.get('reserved_version', None) 
        host = settings.get('host', url)
        
        if host != None: h = "Host: %s" % host;  headers.append(str(h))
        if content_type != None: h = "Content-Type: %s" % content_type;  headers.append(str(h))
        if dev_id != None: h = "X-Roku-Reserved-Dev-Id: %s" % dev_id;  headers.append(str(h))
        if serial_number != None: h = "X-Roku-Reserved-Serial-Number: %s" % serial_number;  headers.append(str(h))
        if model_number != None: h = "X-Roku-Reserved-Model-Number: %s" % model_number;  headers.append(str(h))
        if reserved_version != None: h = "X-Roku-Reserved-Version: %s" % reserved_version; headers.append(str(h))
        if culture_code != None: h = "X-Roku-Reserved-Culture-Code: %s" % culture_code; headers.append(str(h))      
        if content_length != None: 
            h = "Content-Length: %s" % content_length
            headers.append(str(h))
        elif request and len(request) > 0: # not needed for GET, where request can be None or ""
            h = "Content-Length: %s" % len(request)
            headers.append(str(h))
        headers.append("Accept: */*") 
        headers.append("Expect:")
        # any additional headers can be passed in within the settings object
        additional_headers = settings.get("headers", [])
        for h in additional_headers:
            headers.append(str(h))  
        return headers         
        
    def get_cert_paths(self, settings):
        test_home = os.getenv("TEST_HOME")        
        CERT_FILE = settings.get("cert_file", None)
        if CERT_FILE != None and CERT_FILE.find(test_home) < 0:  
            CERT_FILE = test_home + CERT_FILE
            
        CACERT= settings.get("cacert", None)
        if CACERT != None and CACERT.find(test_home) < 0: 
            CACERT = test_home + CACERT  
        
        KEY_FILE = settings.get("key_file", None)
        if KEY_FILE != None and KEY_FILE.find(test_home) < 0:
            KEY_FILE = test_home + KEY_FILE  
        
        return CERT_FILE, CACERT, KEY_FILE
