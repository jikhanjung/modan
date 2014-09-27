#from data import Tag, Link, Comment
#import sys#,re
import math
import numpy
import wx
import zlib

import sqlite3
from libpy.model import MdModel   
from libpy.modan_exception import MdException

class MdImage(MdModel):
  def __init__(self, id=0, imagedata='', width=0,height=0,depth=0,filename='', ppmm='', object_id='', created_at=''):
    self.ClassName = 'MdImage'
    self.id = id
    self.imagedata = imagedata
    self.filename = filename
    self.width = width
    self.height = height
    self.depth = depth
    self.ppmm = ppmm
    self.object_id = object_id
    self.created_at = created_at
    self.image_object = None
  
  def set_image_object( self, image_object ):
    self.image_object = image_object
    if self.image_object.ClassName == 'wxImage':
      self.width = self.image_object.GetWidth()
      self.height = self.image_object.GetHeight()
      data = self.image_object.GetData()
      self.imagedata = zlib.compress( data )

  def get_image_object(self):
    if self.imagedata == '':
      return 
    if self.image_object == None:
      self.image_object = wx.EmptyImage( self.width, self.height )
      self.image_object.SetData( zlib.decompress( self.imagedata ) )
    elif self.image_object.ClassName == 'wxImage' :
      self.image_object.SetData( zlib.decompress( self.imagedata ) )
    return self.image_object

  def find(self):
    sql = "SELECT id, imagedata, width, height, depth, filename, ppmm, object_id, \
            created_at FROM mdimage WHERE id=?"
    cursor = self.get_dbi().conn.cursor()
    for row in cursor.execute(sql, (str(self.id),)):
      self.id = row[0]
      self.imagedata = row[1]
      self.width = row[2]
      self.height = row[3]
      self.depth = row[4]
      self.filename= row[5]
      self.ppmm= row[6]
      self.object_idi= row[7]
      self.created_at = row[8]
      #cur = self.get_dbi().conn.cursor()
    return self

  def find_by_object_id(self, object_id=''):
    rv = []
    sql = "SELECT id, imagedata, width, height, depth, filename, ppmm, object_id, created_at FROM mdimage where object_id=?"
    cur = self.get_dbi().conn.cursor()
    #print object_id
    for row in cur.execute(sql, (object_id,)):
      image = MdImage( id=row[0],imagedata=row[1],width=row[2], height=row[3], depth=row[4], filename=row[5], ppmm=row[6], \
                  object_id=row[7], created_at=row[8])
      rv.append(image)
      #print row[0], row[2], row[3], row[5]
    return rv
  def find_all(self):
    rv = []
    sql = "SELECT id,imagedata, width, height, depth, filename, ppmm, object_id, created_at FROM mdimage"
    cur = self.get_dbi().conn.cursor()
    for row in cur.execute(sql):
      image = MdImage( id=row[0],imagedata=row[1],width=row[2], height=row[3], depth=row[4], filename=row[5], ppmm=row[6], \
                  object_id=row[7], created_at=row[8])
      rv.append(image)
    return rv

  def insert(self):
    #if( self.nickname == '' ): self.set_nickname()
    try:
      #print "insert dataset"
      cur = self.get_dbi().conn.cursor()
      cur.execute("INSERT INTO mdimage\
              (imagedata, width, height, depth, filename, ppmm, object_id ) VALUES (?,?,?,?,?,?,?)",
              (sqlite3.Binary(self.imagedata), self.width, self.height, self.depth, self.filename, self.ppmm, self.object_id))
      self.id = cur.lastrowid
      self.get_dbi().conn.commit()
    except:
      print "Error in insert Dataset"
      raise

  def insert_with_cursor(self,cur):
    #if( self.nickname == '' ): self.set_nickname()
    try:
      #print "insert dataset"
      cur.execute("INSERT INTO mdimage\
              (imagedata, width, height, depth, filename, ppmm, object_id ) VALUES (?,?,?,?,?,?,?)",
              (sqlite3.Binary(self.imagedata), self.width, self.height, self.depth, self.filename, self.ppmm, self.object_id))
      self.id = cur.lastrowid
    except:
      print "Error in insert Dataset"
      raise
      
      
  def delete(self):
    try:
      cursor = self.get_dbi().conn.cursor()
      sql = "DELETE FROM mdimage WHERE id=?"
      cursor.execute(sql,(str(self.id),))
      
      #lm = Landmark()
      #lm.delete_with_cursor_and_mdobject(cursor, self)
      #lm.clean_with_cursor(cursor)

      self.get_dbi().conn.commit()
    except:
      print "Error in delete Dataset"
      raise
    return True

  def delete_with_cursor_and_object_id(self,cursor,object_id):
    try:
      #cursor = self.get_dbi().conn.cursor()
      sql = "DELETE FROM mdimage WHERE object_id=?"
      cursor.execute(sql,(str(object_id),))
      
      #lm = Landmark()
      #lm.delete_with_cursor_and_mdobject(cursor, self)
      #lm.clean_with_cursor(cursor)

      #self.get_dbi().conn.commit()
    except:
      print "Error in delete Dataset"
      raise
    return True

  def update(self):
    try:
      #print "gonna update"
      cursor = self.get_dbi().conn.cursor()
      cursor.execute("UPDATE mdimage SET imagedata=?, width=?, height=?, depth=?, filename=?, ppmm=?,\
                      object_id=? \
                      WHERE id=?", 
                      (self.imagedata, self.width, self.height, self.depth, self.filename, self.ppmm, self.object_id,
                       str(self.id)))
      #print "update executed"
      # delete and insert landmarks
    except:
      print "Error in update Dataset"
      raise


    self.get_dbi().conn.commit()
  