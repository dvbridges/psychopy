#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import yaml
import os
import time

"""
The Alerts module is part of the alerts package for used for generating alerts during PsychoPy integrity checks.
The Alerts module contains several classes for creation, storage and provision of alerts.

Attributes
----------
catalogue : AlertCatalogue
    For loading alert catalogues, or definitions of each alert, from a yaml file.
    Each catalogue entry has a code key, with values of code, category, msg, and url.
root: AlertLog
    A storage class for storage and provision of alerts. AlertsLog has a write and flush method,
    for adding each alert to storage, and flushing for releasing the information and clearing the alerts container.
master: MasterLog
    The MasterLogs responsibility is to store all logs in master alerts logfiles.
    MasterLog appends to the current process' alerts logfile each time the AlertLog is flushed.
"""

class AlertCatalogue():
    """A class for loading alerts from the alerts catalogue yaml file"""
    def __init__(self):
        self.alert = self.load("alertsCatalogue.yml")

    def load(self, fileName):
        """Loads alert catalogue yaml file

        Parameters
        ----------
        fileName: str
            The name of the alerts catalogue yaml file

        Returns
        -------
        dict
            The alerts catalogue as a Python dictionary
        """
        # Load alert definitions
        alertsYml = Path(os.path.dirname(os.path.abspath(__file__))) / fileName
        with open('{}'.format(alertsYml), 'r') as ymlFile:
            return yaml.load(ymlFile, Loader=yaml.SafeLoader)

class AlertLog():
    """The AlertLog storage class for storage and provision of alert data.
    The AlertLog stores data for only a single call to compile script, before being
    flushed to the display, and written to the MasterLog.
    """
    def __init__(self):
        self.alertLog = []

    def write(self, alert):
        """Write to alertLog container

        Parameters
        ----------
        alert: AlertEntry object
            The AlertEntry object instantiated using an alert code
        """
        self.alertLog.append((alert))

    def flush(self):
        for i in self.alertLog:
            # Print to stdOutFrame
            msg = ("AlertLogger: {name} | "
                   "Code: {code} | "
                   "Category: {cat} | "
                   "Message: {msg} | "
                   "Component: {obj}".format(name=i.name,
                                             code=i.code,
                                             cat=i.cat,
                                             msg=i.msg,
                                             obj=i.obj))
            master.write(msg)  # Write to log file
            print(msg)  # Send to terminal or stdOutFrame
        self.alertLog = []  # reset alertLog

class MasterLog():
    """The MasterLog writes all alerts created during the current Python process
    to a log file on each flush of the AlertLog class. The MasterLog will only
    store 5 most recent alert log files.
    """
    def __init__(self):
        self.logFolder = Path(os.path.dirname(os.path.abspath(__file__))) / "alertLogs"
        self.alertLogFile = self.logFolder / "alertLogFile_{}.log".format(time.strftime("%Y.%m.%d.%H.%M.%S"))
        if not self.logFolder.exists():
            self.logFolder.mkdir(parents=True)
        else:
            # Store only 5 most recent alert log files
            logs = [log for log in self.logFolder.glob('*.log')]
            if len(logs) >= 5:
                os.remove(logs[0])

    def write(self, msg):
        with open("{}".format(self.alertLogFile), 'a+') as fp:
            fp.write(msg + '\n')

class AlertEntry():
    """An Alerts data class holding alert data as attributes

    Attributes
    ----------
    name: str
        Name of the AlertLogger
    code: int
        The 4 digit code for retrieving alert from AlertCatalogue
    cat: str
        The category of the alert
    msg: str
        The alert message
    url: str
        A URL for pointing towards information resources for solving the issue
    obj: object
        The object related to the alert e.g., TextComponent object.

    Parameters
    ----------
    name: str
        The name of the AlertLogger instantiating the AlertEntry
    code: int
            The 4 digit code for retrieving alert from AlertCatalogue
    obj: object
        The object related to the alert e.g., TextComponent object.
    """
    def __init__(self, name, code, obj):
        self.name = name
        self.code = catalogue.alert[code]['code']
        self.cat = catalogue.alert[code]['cat']
        self.msg = catalogue.alert[code]['msg']
        self.url = catalogue.alert[code]['url']
        self.obj = obj

class AlertLogger():
    """The Alerts logging class used for writing to AlertLog class

    Parameters
    ----------
    name: str
        Logger name e.g., Experiment, Builder, Coder etc
    """
    def __init__(self, name):
        self.name = name

    def write(self, code, obj=object):
        """Write to AlertLog

        Parameters
        ----------
        code: int
            The 4 digit code for retrieving alert from AlertCatalogue
        obj: object
            The object related to the alert e.g., TextComponent object
        """
        root.write(AlertEntry(self.name, code, obj))

    def flush(self):
        root.flush()

# Create catalogue
catalogue = AlertCatalogue()
# Create log objects
root = AlertLog()
master = MasterLog()