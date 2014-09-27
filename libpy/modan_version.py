MODAN_VERSION = "0.1.8"
DB_VERSION = "0.1.8"

import fnmatch
import os
from libpy.dbi import ModanDBI  
from libpy.model_mdversion import MdVersion

class VersionControl():
    def check_version(self):
        mv = MdVersion()
        ver_list = mv.find_all()
        if len( ver_list ) == 0:
            db_file_version = "0.0.0"
        else:
            db_file_version = ver_list[0].db_version()
        #print db_file_version
        while( db_file_version < DB_VERSION ):
            print db_file_version, "to", DB_VERSION
            db_file_version = self.migrate_db( db_file_version )
  
    def migrate_db(self, from_ver ):
        #print from_ver
        dbi = ModanDBI()
        file_path1 = os.path.join('.','config' ) 
        fname = 'schema.sqlite3_' + str( from_ver ) + '_to_*.sql'
        last_fname = ''
        for ffile in os.listdir( file_path1 ):
            if fnmatch.fnmatch( ffile, fname ):
                if ffile > last_fname:
                    last_fname = ffile
        
        if( os.access( file_path1, os.F_OK ) ) : file_path = os.path.join( file_path1, last_fname ) 
        print file_path
        f = open( file_path, 'r' )
        sql = f.read()
        f.close()
        
        print sql
        
        dbi.conn.executescript( sql )
        dbi.conn.commit()
        
        l = last_fname.split( '_' )
        v = l[-1].split( '.' ) 
        v.pop()
        v = ".".join( v )
        print "Migrate from " + str( from_ver ) + " to " + str( v ) + "..."
        return v
