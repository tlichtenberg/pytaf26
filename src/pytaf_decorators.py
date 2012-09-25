'''
  decorators for ptest test cases
  
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
import sys
import time
import signal
import logging
from threading import Lock
from threading import Thread

class ThreadMethodThread(Thread):
    ''' the watchdog timer thread class used by the timeout decorator'''

    def __init__(self, target, args):
        Thread.__init__(self)
        self.setDaemon(True)
        self.target, self.args = target, args
        self.start()

    def run(self):
        try:
            self.result = self.target(self.args)
            print self.result
        except Exception, e:
            self.exception = e
        except:
            self.exception = Exception()
        else:
            self.exception = None

def timeout(func):
    ''''' the timeout decorator looks for a --timeout command-line argument
          to set the watchdog thread duration, in seconds.
          a function using the timeout decorator will fail and exit if
          the watchdog timer ends before the test does
    '''
    timeout_time = get_arg('--timeout')
    if timeout_time == '':
        timeout_time = 120 # default arg
    def timeout_proxy(args):
        errors = []
        result = ()
        worker = ThreadMethodThread(func, args)
        worker.join(int(timeout_time))
        if worker.isAlive():
            result = (False, 'the test has timed out')
        elif worker.exception is not None:
            result = (False, str(worker.exception))
        else:
            result = worker.result
            
        if result[0] == False:
            errors.append(result[1])
        return pytaf_utils.verify(len(errors) == 0, 'there were errors: %s' % errors)

    return timeout_proxy

def get_arg(which='--repeat'):
    args = sys.argv
    for i in range(len(args)):
        if args[i] == which:
            return args[i+1]
    return ''

def repeat(func):
    ''' 
        a function using the @repeat decorator can be executed repeatedly
        by default the number of executions == 1
        the number of iterations can be overridden by using 
        the command-line argument --repeat followed by a number (e.g. --repeat 10)
    '''
    iterations = get_arg('--repeat')
    if len(iterations) == 0:
        iterations = 1 # default arg
    def wrapper(args):
        results = []
        errors = []
        # run the test repeatedly
        for i in range(int(iterations)):
            print "iteration %s of %s" % (str(i+1), iterations)
            results.append(func(args))
        # collect results and prep any errors
        for result in results:
            #print result
            if result[0] == False:
                errors.append(result[1])
        return pytaf_utils.verify(len(errors) == 0, 'there were errors: %s' % errors)
    return wrapper

def test_duration(func):
    '''Logs the time it takes to execute a function'''    
    def wrapper(args):
        results = []
        errors = []
        start = time.time()
        results.append(func(args))
        elapsed = round((time.time() - start),3)        
        logging.info("[TIMING]:%s took %s seconds" % (func.__name__, elapsed))
            
        for result in results:
            # print result
            if result[0] == False:
                errors.append(result[1])
        return pytaf_utils.verify(len(errors) == 0, 'there were errors: %s' % errors)
    return wrapper

def synchronized(func):
    """ Synchronization decorator. """
    lock = Lock()
    def wrapper(args):
        results = []
        errors = []
        lock.acquire()
        try:
            results.append(func(args))
            for result in results:
                # print result
                if result[0] == False:
                    errors.append(result[1])
            return pytaf_utils.verify(len(errors) == 0, 'there were errors: %s' % errors)
        finally:
            lock.release()

    return wrapper