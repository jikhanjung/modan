#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import wx
from gui.main_frame import ModanFrame
from libpy.modan_version import MODAN_VERSION
from libpy.dbi import ModanDBI
from libpy.conf import ModanConf
import sys

class ModanGUI(wx.App):
    def OnInit(self):
        ''' initiate frame '''
        self.version = MODAN_VERSION

        self.InitPath()
        #print "homepath:", self.homepath


        #self.dbpath = self.homepath
        
        #sys.stdout = open(os.path.join(self.homepath,"modan_stdout.log"), "w", 0)
        #sys.stderr = open(os.path.join(self.homepath,"modan_stderr.log"), "w")

        self.session = None
        self.CheckDB()
        self.frame = ModanFrame(None, -1, 'Modan ' + self.version )
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True

    def InitPath(self):
        #windows = True
        if os.name=='nt':
            from win32com.shell import shell, shellcon
            #print shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
            self.homepath = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
            #print self.homepath
        else:
            self.homepath = os.path.expanduser("~")

        conf = ModanConf()
        db_name = conf.item['db_name'] or "modan.moa"
        self.dbpath = os.path.join( self.homepath, "DiploSoft", "Modan", "DB" )

        if not os.path.isdir(self.dbpath):
            try:
                os.makedirs(self.dbpath)
            except OSError:
                if not os.path.isdir(self.dbpath):
                    raise

        self.dbfilepath = os.path.join( self.dbpath, db_name )
        #print self.dbpath, self.dbfilepath

    def SetDBFilePath(self, dbfilepath, refresh = False ):
        self.dbfilepath = dbfilepath
        #self.frame
        if( refresh ):
            self.frame.refresh_tree()
        return True

    def GetDBFilePath(self ):
        return self.dbfilepath

    def CheckDB( self, dbfilepath = ''  ):
        ## check if DB file can be opened
        self.dbi = None
        try:
            self.dbi = ModanDBI()
        except:
            if False:
                print "creating new db file.."
            else:
                wx.MessageBox( "Can't open default DB file. Designate a file for saving your data." )
                newpath = self.open_file_dialog( "Designate a DB file" )
                if( newpath == '' ):
                    wx.MessageBox( 'Invalid DB file. Closing application.' )
                    exit()
                wx.GetApp().SetDBFilePath( newpath )
                print "new path:", newpath
            try:
                self.dbi = ModanDBI()
            except:
                print "serious error!"
                raise

    def open_file_dialog(self, message='Choose a file', mode='open'):
        """

        :rtype : string
        """
        wildcard = "Modan DB file (*.moa)|*.moa|" \
                   "All files (*.*)|*.*"
        # fileDialog = wx.FileDialog(None, "Choose a file", os.getcwd(),
        #                 "", wildcard, wx.SAVE | wx.OVERWRITE_PROMPT | wx.CHANGE_DIR )
        if mode == 'save':
            dialog_style = wx.SAVE | wx.OVERWRITE_PROMPT
        else:
            dialog_style = wx.OPEN

        file_dialog = wx.FileDialog(self.frame, message, "", "", wildcard, dialog_style)
        newpath = ''
        if file_dialog.ShowModal() == wx.ID_OK:
            newpath = file_dialog.GetPath()
            #wx.MessageBox( self.filename )
        file_dialog.Destroy()
        return newpath
    def get_session(self):
        if self.session is None:
            self.session =self.dbi.Session()

        #print "Session in get_session:", self.session
        return self.session
# standard decorator style

app = ModanGUI(0)

from sqlalchemy import event
@event.listens_for(app.session, 'after_attach')
def receive_after_attach(session, instance):
    #print session, instance
    pass

    # ... (event handling logic) ...

app.MainLoop()
