# -*- coding: utf-8 -*-
"""Warnings/errors used within Psychopy for testing and handling situations.
"""
# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import traceback, sys, warnings #python built-ins
from psychopy import logging

#1xxx runtime errors (dropped a frame, impossible to render that stim...)
#2xxx Builder errors (sanity checking user inputs)
#3xxx App errors (failed to load file...)
#4xxx data errors (can't save, duplicate files...)
#5xxx connection errors (internet/proxies...)

stdWarnings = {
    #1xxx runtime errors
    1001:{'msg':'Dropped a frame', 'info':'PsychoPy had too much processing to do between two window.flip() commands'},
    1002:{"msg":"The stimulus you tried to draw was incredibly small",
        "info":"Have you set the size to be, say, 0.5, with units of 'pix'"},

    #2xxx builder errors
    2001:{'msg':"You have a constant variable",
        'info':"""Your Builder component %s has a parameter that is set to be constant
            but looks like a variable value""" %('f')},
    2002:{"msg": "Syntax error compiling",
        "info":"""There was a syntax error while compiling your script.
If you have any custom code (e.g. a code component then this is likely the source of
the problem. If not then we might need to see the output of the error to work out what happened"""},

    #3xxx app errors
    3001:{'msg':"Failed to load file",
        "info":"That file failed to load"}

    #4xxx data errors

    #5xxx connection errors
    }

def warn(code, obj=None, msg="", trace=None):
    """Generate a warning for either a standard logging target or for a custom warnings target (in which case
    the formatting is controlled by that target not by us).
    If sys.stderr is currently a traditional (text) standard error then we need to format a traditional warning string
    and then send a:
        - psychopy.logging.warning() giving the basic warning string (like a standard Python warning)
        - psychopy.logging.debug() message giving the traceback of the warning
    The nice thing about this is that while in  debugging mode you'll get more info about where your warnings are
    coming from.
    :param code: a number (for a standard PsychoPy warning stored in warnings.stdWarnings)
    :param obj: the object (e.g. variable) about which the warning is occuring
    :param msg: override the message that this warning code typically generates
    :param trace: a custom traceback to use (otherwise deduce it). This should be of the form generated by traceback.format_stack()
    """
    if not msg:
        msg = stdWarnings[code]['msg']
    if not trace:
        trace = traceback.format_stack()[:-1]
    #if we have a psychopy warning instead of a file-like stderr then pass on the raw info
    if hasattr(sys.stderr, 'receiveWarning'):
        sys.stderr.receiveWarning(code, obj, msg, trace)
        return

    #otherwise we need to format the warning into a string for write()
    warnStr = '%s: %s' %(code, msg)
    traceStr = 'Warning trace (%s):\n' %(code)
    for entry in trace:
        traceStr += entry
    logging.warning(warnStr)
    logging.debug(traceStr)

class _BaseErrorHandler(object):
    """A base class for error (and warning) handlers to receive PsychoPy standard
    warnings as well as Python Exceptions.
    Subclass this for any actual handler (e.g. wx diaog to handle warnings)
    """
    def __init__(self):
        """Create the handler, assign and keep track of previous stderr
        """
        self.errList = []
        self.autoFlush=True

    def setStdErr(self):
        """Set self to be sys.stderr.
        Can be reverted with unsetStdErr()
        """
        self.origErr = sys.stderr
        sys.stderr = self

    def unsetStdErr(self):
        """Revert stderr to be the previous sys.stderr when self.setStdErr()
        was last called
        """
        if self==sys.stderr:
            sys.stderr = self.origErr

    def flush(self):
        """This is the key function to override. Flush needs to handle a list
        of errs/warnings that could be strings (Python Exceptions) or dicts
        such as:
            {'code':1001,'obj':stim, 'msg':aString, 'trace':listOfStrings}
        An ErrorHandler might simply collect warnings until the flush()
        method is called
        """
        if hasattr(self, 'errList'):
            for err in self.errList:
                print(err)
            self.errList = []

    def receiveWarning(self, code, obj, msg, trace):
        """Implement this to handle PsychoPy warnings (sent by warnings.warn())
        instead of Python Exceptions. This function should ONLY be called by
        warnings.warn
        :param code: a numeric code referring to a key in psychopy.warnings.stdWarnings
        :param obj: None or an object to which the warning refers
        :param msg: The basic text about the warning
        :param trace: a stack trace (list of strings) to be displayed if desired
        """
        self.errList.append({'code':code,'obj':obj, 'msg':msg, 'trace':trace})

    def write(self, toWrite):
        """This is needed for any Python Exceptions, which assume the stderr
        is a file-like object. But we might well simply store the message for
        printing later.
        """
        self.errList.append(toWrite)
        if self.autoFlush:
            self.flush()

    def __del__(self):
        """Make sure any current warnings are flushed and then revert the
        """
        self.flush()
        self.unsetStdErr()

if __name__ == '__main__':
    #deliberately cause a pp error inside a function
    #handler = ErrorHandler()
    warn(2002, obj='')
    logging.console.setLevel(logging.DEBUG)
    warn(2001)
    print('got beyond the first warning')
#    sys.stderr.presentErrs()