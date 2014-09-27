#import os
import sqlite3
from libpy.model import MdModel   
#from libpy.dbi import ModanDBI  
#from libpy.conf import ModanConf 
   
class MdVersion(MdModel):
    def __init__(self, vid=0, modan_major_version=0, modan_minor_version=0, modan_maintenance_version=0, \
                             db_major_version=0, db_minor_version =0, db_maintenance_version = 0, release_date = '', created_at=''):
        self.id = vid
        self.modan_major_version = modan_major_version
        self.modan_minor_version = modan_minor_version
        self.modan_maintenance_version = modan_maintenance_version
        self.db_major_version = db_major_version
        self.db_minor_version = db_minor_version
        self.db_maintenance_version = db_maintenance_version
        self.release_date = release_date
        self.created_at   = created_at
    
    def find_all(self):
        rv = []
        sql = "SELECT id,modan_major_version, modan_minor_version, modan_maintenance_version, \
                        db_major_version, db_minor_version, db_maintenance_version, release_date, created_at\
                FROM mdversion order by created_at desc"
        cur = self.get_dbi().conn.cursor()
        try:
            for row in cur.execute(sql):
                mdver = MdVersion(vid=row[0], modan_major_version=row[1], modan_minor_version=row[2], modan_maintenance_version=row[3]\
                          ,db_major_version=row[4], db_minor_version=row[5], db_maintenance_version=row[6]\
                          ,release_date=row[7], created_at=row[8])
                rv.append(mdver)
        except sqlite3.OperationalError, ( error_string):
            error_string = str( error_string )
            print error_string
        
        return rv
    
    
    def modan_version(self):
        return str( self.modan_major_version ) + "." + str( self.modan_minor_version ) + "." + str( self.modan_maintenance_version ) 
    
    def db_version(self):
        return str( self.db_major_version ) + "." + str( self.db_minor_version ) + "." + str( self.db_maintenance_version )
    
