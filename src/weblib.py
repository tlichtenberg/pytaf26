#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
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

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
import pytaf_utils

class WebLib:
    def __init__(self, settings):
        browser = settings.get('browser', '*firefox,10,Windows')
        browser_fields = browser.split(',')
        if len(browser_fields) == 3:
            browser_name = browser_fields[0]
            browser_version = browser_fields[1] 
            browser_platform = browser_fields[2]
        else:
            browser_name = browser_fields[0]
            browser_version = ''
            browser_platform = ''
        selenium_host = settings.get('selenium_host', 'localhost')
        selenium_port = settings.get('selenium_port', '4444')
        self.driver = None    
        webdriver_url = "http://%s:%s/wd/hub" % (selenium_host, selenium_port)
        logging.info("webdriver_url = %s" % webdriver_url)
        try:
            if browser_name.find("firefox") >= 0 or browser_name.find("*chrome") >= 0:
                dc = DesiredCapabilities.FIREFOX              
            elif browser_name.find("*googlechrome") >= 0:
                dc = DesiredCapabilities.CHROME
                dc["chrome.switches"] = ["--ignore-certificate-errors"]
            elif browser_name.find("*mock") >= 0:
                dc = DesiredCapabilities.HTMLUNIT
            elif browser_name.find("android") >= 0:
                dc = DesiredCapabilities.ANDROID
            elif browser_name.find("*ie") >= 0:
                dc = DesiredCapabilities.INTERNETEXPLORER
            else:  # default to Firefox
                dc = DesiredCapabilities.FIREFOX
                             
            if browser_version != '':
                dc['version'] = browser_version
            if browser_platform != '':
                dc['platform'] = browser_platform
            self.driver = webdriver.Remote(webdriver_url, dc)
        except:
            print(pytaf_utils.formatExceptionInfo())
