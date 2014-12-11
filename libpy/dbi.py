#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from sqlalchemy import create_engine
import wx

from libpy.conf import ModanConf
from sqlalchemy.orm import sessionmaker
from libpy.modan_dbclass import *

class ModanDBI:
    def __init__(self):
        #print "init"
        conf = ModanConf()
        #print conf.item
        app = wx.GetApp()
        dbfilepath = app.GetDBFilePath()

        try:
            # self.conn = sqlite.connect(db_file)
            self.conn = create_engine('sqlite:///' + dbfilepath, echo=True)
            print "conn done"
            if not os.path.isfile(dbfilepath):
                Base.metadata.create_all(self.conn)
            print "file shoudl be made"
            self.Session = sessionmaker(bind=self.conn)
            print "session class"
            #self.conn = sqlite3.connect(db_file)
        except:
            print "Database error : check %s" % dbfilepath
            raise