#!/usr/bin/env python2.5
import sys
sys.path += ['.']

import os
import wx
import sys
import sqlite3
#sys.path.append('libpy')
#sys.path.append('gui')
from gui.main_frame import ModanFrame
from libpy.model_mddataset import MdDataset
from libpy.modan_version import VersionControl, MODAN_VERSION, DB_VERSION

from libpy.dbi import ModanDBI  
#from libpy.conf import ModanConf 
#from libpy.modan_exception import MdException
 
 
class ModanGUI(wx.App):
    def OnInit(self):
        #self.dbpath = ""
        if( len( sys.argv ) > 1 ):
            self.SetDbpath( os.path.join( os.getcwd(), sys.argv[1] ) )
            #  print sys.argv 
        self.version = MODAN_VERSION
        ''' Check DB file '''
        self.CheckDB()
        
        ''' initiate frame '''
        self.frame = ModanFrame(None, -1, 'Modan ' + self.version )
        self.frame.Show(True) 
        self.SetTopWindow(self.frame)

        self.basepath = os.path.expanduser("~")
        
        sys.stdout = open(os.path.join(self.basepath,"modan_stdout.log"), "w", 0)
        sys.stderr = open(os.path.join(self.basepath,"modan_stderr.log"), "w")
        
        return True
    
    def SetDbpath(self, dbpath, refresh = False ):
        self.dbpath = dbpath
        #self.frame
        if( refresh ):
            self.frame.RefreshTree()
        return True
    def GetDbpath(self ):
        #self.frame
        #self.frame.RefreshTree()
        return self.dbpath 
    
    def CheckDB( self, dbpath = ''  ):
        ## check if DB file can be opened
        #dbi = ''
        dbi = ''
        try:
            dbi = ModanDBI()
        except:
            if False:
                print "creating new db file.."
            else:
                wx.MessageBox( "Can't open default DB file. Designate a file for saving your data." )
                newpath = self.OpenFileDialog( "Designate a DB file" )
                if( newpath == '' ):
                    wx.MessageBox( 'Invalid DB file. Closing application.' )
                    exit()
                wx.GetApp().SetDbpath( newpath )
            try:
                dbi = ModanDBI()
            except:
                print "serious error!"
                return
            
        ## 
        
        ds = MdDataset()
        try:
            ds.find_all()
        except sqlite3.OperationalError, ( error_string):
            error_string = str( error_string )
            print error_string
            if( error_string.find( "no such table" ) >= 0 ):
                ## generate tables
                file_path1 = os.path.join('..','config','schema.sqlite3_' + DB_VERSION + '.sql')
                file_path2 = os.path.join('.','config','schema.sqlite3_' + DB_VERSION + '.sql')
                file_path = ''
                if( os.access(file_path1, os.F_OK) ): file_path = file_path1
                elif( os.access(file_path2, os.F_OK) ): file_path = file_path2
                sql_path = file_path
                #print sql_path
                f = open( sql_path, 'r' )
                #print f
                sql = f.read()
                f.close()
                #print sql
                dbi.conn.executescript( sql )
              
        vc = VersionControl()
        vc.check_version()
        # check if tables exist
        #exit()
#    except IOError:
#      print "error"
#    else:
##      print e
#      print "db open error!"

#sys.stdout = open("my_stdout.log", "w")

app = ModanGUI(0)
#print sys.argv[0]
app.MainLoop()
