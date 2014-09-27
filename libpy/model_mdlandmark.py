#===============================================================================
# #from data import Tag, Link, Comment 
#===============================================================================
#import sys#,re
from libpy.model import MdModel
#from model_mddataset import MdDataset
#from model_mdobject import MdObject
   
class MdLandmark(MdModel):
  def __init__(self, id=0, dataset_id=0, object_id=0, lmseq=0, xcoord=0, ycoord=0, zcoord=0, created_at=''):
    self.selected = False
    self.id = id
    self.object_id = object_id
    self.lmseq = int( lmseq )
    self.xcoord = float( xcoord )
    self.ycoord = float( ycoord )
    if zcoord != '':
      self.zcoord = float( zcoord )
    else:
      self.zcoord = 0.0
    self.created_at = created_at
 
  def delete(self):
    try:
      cursor = self.get_dbi().conn.cursor()
      sql = "DELETE FROM mdlandmark WHERE id=?"
      cursor.execute(sql,(str(self.id),))
      
      self.get_dbi().conn.commit()
    except:
      print "Error in delete MdLandmark"
      raise

  def delete_with_cursor_and_object_id( self, cur, objid ):
    sql = "DELETE FROM mdlandmark WHERE object_id=?"
    cur.execute(sql, (objid,))

  def update(self):
    try:
      cursor = self.get_dbi().conn.cursor()
      cursor.execute("UPDATE mdlandmark SET lmseq=?, xcoord=?, ycoord=?,\
                      zcoord=?\
                      WHERE id=?", 
                      (self.lmseq, self.xcoord, self.ycoord, self.zcoord, 
                       str(self.id)))
      
    except:
      print "Error in update MdLandmark"
      raise

  def insert_with_cursor(self, cursor):
    sql = "INSERT INTO mdlandmark (object_id, dataset_id,lmseq, xcoord,ycoord,zcoord) VALUES (?,?,?,?,?,?)"
    cursor.execute(sql, (self.object_id, self.dataset_id, self.lmseq, self.xcoord, self.ycoord, self.zcoord))
    return cursor.lastrowid

  def insert(self):
    #if( self.lmseq == '' ): self.lmseq()
    try:
      cur = self.get_dbi().conn.cursor()
      cur.execute("INSERT INTO mdlandmark\
              (object_id, dataset_id, lmseq, xcoord, ycoord, zcoord)\
              VALUES (?,?,?,?,?,?)",
              (self.object_id, self.dataset_id, self.lmseq,
              self.xcoord, self.ycoord, self.zcoord ))
      self.id = cur.lastrowid

      self.get_dbi().conn.commit()
    except:
      print "Error in insert MdLandmark"
      raise

  def find(self):
    sql = "SELECT id,object_id,dataset_id,lmseq,xcoord,ycoord,zcoord,\
            created_at FROM mdlandmark WHERE id=?"
    cursor = self.get_dbi().conn.cursor()
    for row in cursor.execute(sql, (str(self.id),)):
      self.id = row[0]
      self.object_id = row[1]
      self.dataset_id = row[2]
      self.lmseq = row[3]
      self.xcoord = row[4]
      self.ycoord = row[5]
      self.zcoord = row[6]
      self.created_at = row[7]
    return self
      
  def find_by_object_id(self, object_id):
    rv = []
    sql = "SELECT id,object_id,dataset_id,lmseq,xcoord,ycoord,zcoord,\
            created_at FROM mdlandmark WHERE object_id=? order by lmseq"
    cur = self.get_dbi().conn.cursor()
    for row in cur.execute(sql,(str(object_id),)):
      lm = MdLandmark(id=row[0], object_id=row[1], dataset_id=row[2],
                  lmseq=row[3], xcoord=row[4], ycoord=row[5],
                  zcoord=row[6], created_at=row[7])
      rv.append(lm)

    return rv
