#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import wx.html2

import re
import locale
from psychopy.localization import _translate
from psychopy.warnings import _BaseErrorHandler
from psychopy.projects import pavlovia
from psychopy import logging
from psychopy.app import stdOutRich
from . import sync


class BaseFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.Center()
        # set up menu bar
        self.menuBar = wx.MenuBar()
        self.fileMenu = self.makeFileMenu()
        self.menuBar.Append(self.fileMenu, _translate('&File'))
        self.SetMenuBar(self.menuBar)

    def makeFileMenu(self):
        fileMenu = wx.Menu()
        app = wx.GetApp()
        keyCodes = app.keys
        # add items to file menu
        fileMenu.Append(wx.ID_CLOSE,
                        _translate("&Close View\t%s") % keyCodes['close'],
                        _translate("Close current window"))
        self.Bind(wx.EVT_MENU, self.closeFrame, id=wx.ID_CLOSE)
        # -------------quit
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_EXIT,
                        _translate("&Quit\t%s") % keyCodes['quit'],
                        _translate("Terminate the program"))
        self.Bind(wx.EVT_MENU, app.quit, id=wx.ID_EXIT)
        return fileMenu

    def closeFrame(self, event=None, checkSave=True):
        self.Destroy()

    def checkSave(self):
        """If the app asks whether everything is safely saved
        """
        return True  # for OK


class PavloviaMiniBrowser(wx.Dialog):
    """This class is used by to open an internal browser for the user stuff
    """
    style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
    def __init__(self, parent, user=None, loginOnly=False, logoutOnly=False,
                 style=style, *args, **kwargs):
        # create the dialog
        wx.Dialog.__init__(self, parent, style=style, *args, **kwargs)
        # create browser window for authentication
        self.browser = wx.html2.WebView.New(self)
        self.loginOnly = loginOnly
        self.logoutOnly = logoutOnly
        self.tokenInfo = {}

        # do layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.browser, 1, wx.EXPAND, 10)
        self.SetSizer(sizer)
        if loginOnly:
            self.SetSize((600, 600))
        else:
            self.SetSize((700, 600))
        self.CenterOnParent()

        # check there is a user (or log them in)
        if not user:
            self.user = pavlovia.getCurrentSession().user
        if not user:
            self.login()
        if not user:
            return None

    def logout(self):
        self.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.checkForLogoutURL)
        self.browser.LoadURL('https://gitlab.pavlovia.org/users/sign_out')

    def login(self):
        self._loggingIn = True
        authURL, state = pavlovia.getAuthURL()
        self.browser.Bind(wx.html2.EVT_WEBVIEW_ERROR, self.onConnectionErr)
        self.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.checkForLoginURL)
        self.browser.LoadURL(authURL)

    def setURL(self, url):
        self.browser.LoadURL(url)

    def gotoUserPage(self):
        if self.user:
            url = self.user.attributes['web_url']
            self.browser.LoadURL(url)

    def gotoProjects(self):
        self.browser.LoadURL("https://pavlovia.org/projects.html")

    def onConnectionErr(self, event):
        if 'INET_E_DOWNLOAD_FAILURE' in event.GetString():
            self.EndModal(wx.ID_EXIT)
            raise Exception("{}: No internet connection available.".format(event.GetString()))

    def checkForLoginURL(self, event):
        url = event.GetURL()
        if 'access_token=' in url:
            self.tokenInfo['token'] = self.getParamFromURL(
                'access_token', url)
            self.tokenInfo['tokenType'] = self.getParamFromURL(
                'token_type', url)
            self.tokenInfo['state'] = self.getParamFromURL(
                'state', url)
            self._loggingIn = False  # we got a log in
            self.browser.Unbind(wx.html2.EVT_WEBVIEW_LOADED)
            pavlovia.login(self.tokenInfo['token'])
            if self.loginOnly:
                self.EndModal(wx.ID_OK)
        elif url == 'https://gitlab.pavlovia.org/dashboard/projects':
            # this is what happens if the user registered instead of logging in
            # try now to do the log in (in the same session)
            self.login()
        else:
            logging.info("OAuthBrowser.onNewURL: {}".format(url))

    def checkForLogoutURL(self, event):
        url = event.GetURL()
        if url == 'https://gitlab.pavlovia.org/users/sign_in':
            if self.logoutOnly:
                self.EndModal(wx.ID_OK)

    def getParamFromURL(self, paramName, url=None):
        """Takes a url and returns the named param"""
        if url is None:
            url = self.browser.GetCurrentURL()
        return url.split(paramName + '=')[1].split('&')[0]


class PavloviaCommitDialog(wx.Dialog):
    """This class will be used to brings up a commit dialog
    (if there is anything to commit)"""

    def __init__(self, *args, **kwargs):

        # pop kwargs for Py2 compatibility
        changeInfo = kwargs.pop('changeInfo', '')
        initMsg = kwargs.pop('initMsg', '')

        super(PavloviaCommitDialog, self).__init__(*args, **kwargs)

        # Set Text widgets
        wx.Dialog(None, id=wx.ID_ANY, title="Committing changes")
        self.updatesInfo = wx.StaticText(self, label=changeInfo)
        self.commitTitleLbl = wx.StaticText(self, label='Summary of changes')
        self.commitTitleCtrl = wx.TextCtrl(self, size=(500, -1), value=initMsg)
        self.commitDescrLbl = wx.StaticText(self, label='Details of changes\n (optional)')
        self.commitDescrCtrl = wx.TextCtrl(self, size=(500, 200), style=wx.TE_MULTILINE | wx.TE_AUTO_URL)

        # Set buttons
        self.btnOK = wx.Button(self, wx.ID_OK)
        self.btnCancel = wx.Button(self, wx.ID_CANCEL)

        # Format elements
        self.setToolTips()
        self.setDlgSizers()

    def setToolTips(self):
        """Set the tooltips for the dialog widgets"""
        self.commitTitleCtrl.SetToolTip(
            wx.ToolTip(
                _translate("Title summarizing the changes you're making in these files")))
        self.commitDescrCtrl.SetToolTip(
            wx.ToolTip(
                _translate("Optional details about the changes you're making in these files")))

    def setDlgSizers(self):
        """
        Set the commit dialog sizers and layout.
        """
        commitSizer = wx.FlexGridSizer(cols=2, rows=2, vgap=5, hgap=5)
        commitSizer.AddMany([(self.commitTitleLbl, 0, wx.ALIGN_RIGHT),
                             self.commitTitleCtrl,
                             (self.commitDescrLbl, 0, wx.ALIGN_RIGHT),
                             self.commitDescrCtrl])
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.AddMany([self.btnCancel,
                             self.btnOK])

        # main sizer and layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.updatesInfo, 0, wx.ALL | wx.EXPAND, border=5)
        mainSizer.Add(commitSizer, 1, wx.ALL | wx.EXPAND, border=5)
        mainSizer.Add(buttonSizer, 0, wx.ALL | wx.ALIGN_RIGHT, border=5)
        self.SetSizerAndFit(mainSizer)
        self.Layout()

    def ShowCommitDlg(self):
        """Show the commit application-modal dialog

        Returns
        -------
        wx event
        """
        return self.ShowModal()

    def getCommitMsg(self):
        """
        Gets the commit message for the git commit.

        Returns
        -------
        string:
            The commit message and description.
            If somehow the commit message is blank, a default is given.
        """
        if self.commitTitleCtrl.IsEmpty():
            commitMsg = "_"
        else:
            commitMsg = self.commitTitleCtrl.GetValue()
            if not self.commitDescrCtrl.IsEmpty():
                commitMsg += "\n\n" + self.commitDescrCtrl.GetValue()
        return commitMsg

class IssuesRichText(stdOutRich.StdOutRich):
    """
    Modified StdOutRich class for handling warnings with error codes
    """
    def __init__(self, *args, **kwargs):
        super(IssuesRichText, self).__init__(*args, **kwargs)
        self._prefEncoding = locale.getpreferredencoding()

    def getSringFromErrorList(self, err):
        errorString = ''
        for item in err:
            errorString += "{}\n{}\n{}\n{}\n".format(item['code'], item['obj'], item['msg'], item['trace'][-1])
        return errorString

    def write(self, inStr):
        self.MoveEnd()  # always 'append' text rather than 'writing' it
        # if it comes form a stdout in Py3 then convert to unicode
        inStr = self.getSringFromErrorList(inStr)
        if type(inStr) == bytes:
            try:
                inStr = inStr.decode('utf-8')
            except UnicodeDecodeError:
                inStr = inStr.decode(self._prefEncoding)

        for thisLine in inStr.splitlines(True):
            try:
                thisLine = thisLine.replace("\t", "    ")
            except Exception as e:
                self.WriteText(str(e))
            # if len(re.findall('".*", line.*', thisLine)) > 0:
            #     # this line contains a file/line location so write as URL
            #     # self.BeginStyle(self.urlStyle)  # this should be done with
            #     # styles, but they don't exist in wx as late as 2.8.4.0
            #     self.BeginBold()
            #     self.BeginTextColour(wx.BLUE)
            #     self.BeginURL(thisLine)
            #     self.WriteText(thisLine)
            #     self.EndURL()
            #     self.EndBold()
            #     self.EndTextColour()
            # Get re to find error codes, and format accordingly
            if len(re.findall('200', thisLine)) > 0:
                self.BeginTextColour([0, 150, 0])
                self.WriteText(thisLine)
                self.EndTextColour()
            elif len(re.findall('100', thisLine)) > 0:
                self.BeginTextColour([150, 0, 0])
                self.WriteText(thisLine)
                self.EndTextColour()
            else:
                # line to write as simple text
                self.WriteText(thisLine)
        self.MoveEnd()  # go to end of stdout so user can see updated text
        self.ShowPosition(self.GetLastPosition())

class PavloviaLaunchCenter(wx.Dialog):
    """
    The Pavlovia Launch Dialog. Presents:
        > Project name
        > Git sync status and sync button
        > Issues panel
        > Settings button to launch internal browser
        > Project URL with copy button
    """

    def __init__(self, frame, *args, **kwargs):
        super(PavloviaLaunchCenter, self).__init__(frame, size = (500,600), *args, **kwargs)
        self.errorHandler = None
        self.frame = frame
        # panel = wx.Panel(self, size=(500, 600))

        # Set IssueDLG elements
        self.projectLabel = wx.StaticText(self, label='Project: ', size=(100, 20))
        self.project = wx.TextCtrl(self, value='', size=(300, 20), style=wx.TE_READONLY)
        self.syncPanel = sync.SyncStatusPanel(self, size=(400, 100), id=wx.ID_ANY)
        self.issuePanel = IssuesRichText(self, size=(400,100), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.urlLabel = wx.adv.HyperlinkCtrl(self, size=(300, 20), label=self.projectURL)

        # Create sizers for elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        nameSizer = wx.BoxSizer(wx.HORIZONTAL)
        gitStatusSizer = wx.BoxSizer(wx.HORIZONTAL)
        issueSizer = wx.BoxSizer(wx.HORIZONTAL)
        projectURLSizer = wx.BoxSizer(wx.HORIZONTAL)

        # Add elements to sizers
        nameSizer.Add(self.projectLabel, 1, wx.TOP | wx.BOTTOM | wx.LEFT, border=40)
        nameSizer.Add(self.project, 1, wx.TOP | wx.RIGHT | wx.BOTTOM, border=40)
        gitStatusSizer.Add(self.syncPanel, 1, wx.ALL | wx.CENTER, border=10)
        issueSizer.Add(self.issuePanel, 1, wx.ALL | wx.CENTER, border=20)
        projectURLSizer.Add(self.urlLabel, 1, wx.TOP | wx.BOTTOM | wx.LEFT, border=40)

        # Set sizers
        mainSizer.Add(nameSizer)
        mainSizer.Add(gitStatusSizer, 1, wx.ALIGN_CENTER_HORIZONTAL)
        mainSizer.Add(issueSizer, 1, wx.ALIGN_CENTER_HORIZONTAL)
        mainSizer.Add(projectURLSizer)
        self.SetSizer(mainSizer)

        self.setProject()
        self.setErrorHandler()

    def onURL(self, evt):
        pass

    def setErrorHandler(self):
        self.errorHandler = ErrorHandler()

    @property
    def projectName(self):
        return self.frame.project['id']

    def setProject(self):
        self.project.SetValue(self.projectName)

    def getGitStatus(self):
        pass

    def getIssues(self):
        pass

    def getSettings(self):
        pass

    @property
    def projectURL(self):
        prefix = "https://run.pavlovia.org/"
        project = self.frame.project['id']
        suffix = "/html"
        return "{}{}{}".format(prefix, project, suffix)

class ErrorHandler(_BaseErrorHandler):
    def __init__(self):
        super(ErrorHandler, self).__init__()
        self.setStdErr()
