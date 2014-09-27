import os
import sqlite3
#from pysqlite2 import dbapi2 as sqlite  
from libpy.conf import ModanConf 
import wx
   
class ModanDBI:
  def __init__(self):
    conf = ModanConf()
    app = wx.GetApp()
    if app != None and app.__dict__.has_key( 'dbpath' ):
      db_file = app.GetDbpath()
    else:
      db_file = os.path.join(conf.item['dir_db'],conf.item['db_name'])
      if app != None:
        app.SetDbpath( db_file )
    #print db_file
    try:
      #self.conn = sqlite.connect(db_file)
      self.conn = sqlite3.connect(db_file) 
    except:
      print "Database error : check %s" % db_file
      raise