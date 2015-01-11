#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from sqlalchemy import create_engine
import wx

from libpy.conf import ModanConf
from sqlalchemy.orm import sessionmaker
from libpy.modan_dbclass import *

from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class ModanDBI:
    Session = None
    def __init__(self):
        #print "init"
        conf = ModanConf()
        #print conf.item
        app = wx.GetApp()
        dbfilepath = app.GetDBFilePath()

        try:
            # self.conn = sqlite.connect(db_file)
            self.conn = create_engine('sqlite:///' + dbfilepath, echo=True)
            #print "conn done"
            if not os.path.isfile(dbfilepath):
                Base.metadata.create_all(self.conn)
            #print "file shoudl be made"
            self.Session = sessionmaker(bind=self.conn)
            #print "session class"
            #self.conn = sqlite3.connect(db_file)
        except:
            print "Database error : check %s" % dbfilepath
            raise

