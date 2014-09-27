import unittest
import sys
sys.path.append('..')
sys.path.append('.')
from libpy.dbi import ModanDBI  

class DbInstanceTestCase( unittest.TestCase ):
    testname = [ "Test Name 1", "Test Name 2" ]
    testdesc = [ "Description test row 1", "Description for test row 2"]
    testid = -1
  
    def setUp(self):
        self.dbi = ModanDBI()
    def test_01_Dbi(self):
        '''Check DBI class'''
        assert( self.dbi.__class__, 'libpy.dbi.ModanDBI' )
    def test_02_Connection(self):
        '''Check Connection'''
        assert( self.dbi.conn.__class__, 'sqlite3.Connection' )
    def test_03_Cursor(self):
        '''Check Cursor'''
        assert( self.dbi.conn.cursor().__class__, 'sqlite3.Cursor' )
    def test_04_CreateTable(self):
        '''Create table test'''
        cur = self.dbi.conn.cursor()
        rv = cur.execute( "create table test_table ( \
              id integer not null primary key autoincrement, \
              testname text not null, \
              testdesc text not null \
              )" )
        #print rv
        assert( rv.__class__, 'sqlite3.Cursor' )
    def test_05_InsertRow(self):
        '''Insert row test'''
        cur = self.dbi.conn.cursor()
        rv = cur.execute( "insert into test_table ( testname, testdesc ) \
             values ( ?, ? )", ( self.testname[0], self.testdesc[0] ) )
        self.dbi.conn.commit()
        if( rv.lastrowid > 0 ):
            self.testid = rv.lastrowid
        #print "testid: ", str( self.testid )
        assert( rv.lastrowid > 0 )
    
    def test_06_CheckCount(self):
        '''Confirm inserted row count'''
        cur = self.dbi.conn.cursor()
        for rs in cur.execute( "select count(*) from test_table" ):
            row_count = rs[0]
        #print "row_count: [" + str( row_count ) + "]"
        #print "testid: ", str( self.testid )
        assert( row_count, 1 )
    
    def test_07_CheckContent(self):
        '''Confirm inserted row content'''
        cur = self.dbi.conn.cursor()
        ( fetched_name, fetched_desc ) = ( "", "" )
        #print "id : ", str( self.testid ) 
        for rs in cur.execute( "select id, testname, testdesc from test_table " ):
            fetched_name = rs[1]
            fetched_desc = rs[2]
        #print "fetch:", fetched_name
        #print "orig_name:", self.testname[0]
        self.assertEqual( fetched_name, self.testname[0] )
        self.assertEqual( fetched_desc, self.testdesc[0] )
        
    def test_08_UpdateRow(self):
        '''Check update row'''
        #assert( self.id > 0 )
        try:
            cur = self.dbi.conn.cursor()
            cur.execute( "update test_table set testname = ? \
              , testdesc = ?", ( self.testname[1], self.testdesc[1] ) )
            self.dbi.conn.commit()
            ( fetched_name, fetched_desc ) = ( "", "" )
            for rs in cur.execute( "select id, testname, testdesc from test_table " ):
                fetched_name = rs[1]
                fetched_desc = rs[2]
            assert( fetched_name == self.testname[1] and fetched_desc == self.testdesc[1] )
        except:
            raise
    
    def test_09_DeleteRow(self):
        '''Check delete row'''
        cur = self.dbi.conn.cursor()
        cur.execute( "delete from test_table" )
        self.dbi.conn.commit()
        for rs in cur.execute( "select count(*) from test_table" ):
            rs = rs[0]
        assert( rs, 0 )
        
    def test_10_DropTable(self):
        '''Check drop table'''
        cur = self.dbi.conn.cursor()
        rv = cur.execute( "drop table test_table" )
        #print rv
        assert( rv.__class__, 'sqlite3.Cursor' )
      
    def tearDown(self):
        self.dbi = None
  
#  def suite(self):

from libpy.model_mddataset import MdDataset
from libpy.model_mdobject import MdObject
from libpy.model_mdlandmark import MdLandmark

class MdObjectTestCase( unittest.TestCase ):
    def setUp(self):
        self.obj = MdObject()
        self.ds = MdDataset()
        self.ds.dsname = "Test dataset"
        self.ds.dsdesc = "test for mdObject"
        self.ds.insert()
        return
    def test_01_ObjectBasicOperation(self):
        ''' Testing MdObject basic operation '''
        self.obj.objname = 'Test Object'
        self.obj.objdesc = 'Insert test'
        self.obj.dataset_id = self.ds.id
        self.obj.insert()
        #print "ds id:", self.ds.id
        assert( self.obj.id > 0 )
        objid = self.obj.id
        
        ''' Dataset check ''' 
        ds = MdDataset()
        ds.id = self.obj.dataset_id
        ds.find()
        self.assertEqual( ds.dsname, self.ds.dsname )
        
        ''' Check insert result '''
        obj2 = MdObject()
        obj2.id = objid
        obj2.find()
        self.assertEqual( obj2.objname, self.obj.objname )
        
        ''' Test update '''
        self.obj.id = objid
        self.obj.find()
        self.assertEqual( self.obj.id, objid )
        self.obj.dsdesc = 'Update test'
        self.obj.update()
        obj2 = MdObject()
        obj2.id = objid
        obj2.find()
        self.assertEqual( obj2.objdesc, self.obj.objdesc )
        
        ''' test delete '''
        self.obj.id = objid
        self.obj.find()
        rv = self.obj.delete()
        self.assertTrue( rv )
        obj2 = MdObject()
        obj2.id = objid
        rv = obj2.find()
        self.assertEqual( obj2.objname, '' )
    
    def test_02_ObjectLandmarkOperation(self):
        ''' Testing MdObject landmark operation '''
        self.obj.objname = 'Test Object'
        self.obj.objdesc = 'landmark test'
        self.obj.dataset_id = self.ds.id
        
        self.obj.landmarks.append( MdLandmark( lmseq=10,xcoord=0.5,ycoord=-0.5,zcoord=0.4 ) )
        self.obj.landmarks.append( MdLandmark( lmseq=20,xcoord=0.4,ycoord=-0.6,zcoord=0.7 ) )
        self.obj.landmarks.append( MdLandmark( lmseq=30,xcoord=0.3,ycoord=-0.1,zcoord=0.11 ) )
        self.obj.landmarks.append( MdLandmark( lmseq=40,xcoord=0.2,ycoord=-0.6,zcoord=0.2 ) )
        self.obj.landmarks.append( MdLandmark( lmseq=50,xcoord=0.1,ycoord=-0.3,zcoord=0.9 ) )
        
        self.obj.insert()
        #print "ds id:", self.ds.id
        assert( self.obj.id > 0 )
        objid = self.obj.id
        
        obj2 = MdObject()
        obj2.id = objid
        obj2.find()
        obj2.set_landmarks()
        
        self.assertEqual( len( self.obj.landmarks ), len( obj2.landmarks ) )
        
        obj2.landmarks = []
        obj2.update()
        
        self.obj.set_landmarks()
        self.assertEqual( 0, len( self.obj.landmarks ) )
        
        self.assertTrue( self.obj.delete() )
        
        
    def tearDown(self):
        self.obj = None
        self.ds.delete()
        self.ds = None

class MdDatasetTestCase( unittest.TestCase ):
    dsid = -1
    def setUp(self):
        self.ds = MdDataset()
        return
    def test_01_DatasetBasicOperation(self):
        ''' Testing MdDataset basic operation '''
        self.ds.dsname = 'Test Dataset'
        self.ds.dsdesc = 'Insert test'
        self.ds.dimension = 3
        self.ds.groupname = ''
        self.ds.wireframe_id = -1
        self.ds.baseline = ''
        self.ds.insert()
        #print "ds id:", self.ds.id
        assert( self.ds.id > 0 )
        self.dsid = dsid = self.ds.id
        
        ''' Check insert result '''
        ds2 = MdDataset()
        ds2.id = dsid
        ds2.find()
        self.assertEqual( ds2.dsname, self.ds.dsname )
        
        ''' Test update '''
        self.ds.id = dsid
        self.ds.find()
        self.assertEqual( self.ds.id, dsid )
        self.ds.dsdesc = 'Update test'
        self.ds.update()
        ds2 = MdDataset()
        ds2.id = dsid
        ds2.find()
        self.assertEqual( ds2.dsdesc, self.ds.dsdesc )
        
        ''' test delete '''
        self.ds.id = dsid
        self.ds.find()
        rv = self.ds.delete()
        self.assertTrue( rv )
        ds2 = MdDataset()
        ds2.id = dsid
        rv = ds2.find()
        self.assertEqual( ds2.dsname, '' )
    
    def test_02_dummy(self):
        print self.dsid
    
    def tearDown(self):
        self.ds = None



if __name__ == "__main__":
    suite1 = unittest.TestLoader().loadTestsFromTestCase(DbInstanceTestCase)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(MdDatasetTestCase)
    suite3 = unittest.TestLoader().loadTestsFromTestCase(MdObjectTestCase)
    alltest = unittest.TestSuite( [suite1, suite2, suite3])
    unittest.TextTestRunner(verbosity=2).run(alltest)
    #unittest.main()