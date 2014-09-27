#from data import Tag, Link, Comment
#import sys#,re

import sqlite3
from libpy.model import MdModel   
   
class MdWireframe(MdModel):
  def __init__(self, id=0, wfname='', wfdesc='', edges='', created_at=''):
    self.id = id
    self.wfname = wfname
    self.wfdesc = wfdesc
    self.edges= edges
    self.edge_list = []
    self.created_at = created_at
    if edges != '' :
      self.parse_edges( edges )

  def parse_edges( self, edge_text = '' ):
    
    if edge_text == '' and self.edges != '' :
      edge_text = self.edges
    if edge_text.find( "\n" ) > 0 :
      edge_text = self.process_wireframe_textarea( edge_text )

    self.edge_list = []
    if edge_text == '':
      return
    #print edge_text
    
    for edge in edge_text.split( "," ):
      if edge != '':
        self.edge_list.append( [ int(x) for x in edge.split( "-" )]  )

  def process_wireframe_textarea(self, edge_text):
    new_edges = []
    edges = edge_text.split( "\n" )
    for edge in edges:
      edge = edge.strip()
      points = edge.split( " " )
      if len( points ) > 2 :
        points = points[-2:-1]
      elif len( points ) < 2:
        continue
      new_edges.append( "-".join( points ) )
    self.edges = ",".join( new_edges )
    return self.edges
  
  def make_edge_text_from_list(self,edge_list):
    new_edges = []
    for points in edge_list:
      new_edges.append( "-".join( points ) )
    return ",".join( new_edges )

  def find(self):
    sql = "SELECT id,wfname,wfdesc,edges, \
            created_at FROM mdwireframe WHERE id=?"
    cursor = self.get_dbi().conn.cursor()
    for row in cursor.execute(sql, (str(self.id),)):
      self.id = row[0]
      self.wfname= row[1]
      self.wfdesc= row[2]
      self.edges= row[3]
      self.created_at = row[4]
      #cur = self.get_dbi().conn.cursor()
    return self

  def find_by_name(self, wfname=''):
    rv = []
    wn = wfname
    sql = "SELECT id, wfname, wfdesc, edges, created_at from mdwireframe where wfname = ?"
    cur = self.get_dbi().conn.cursor()
    for row in cur.execute(sql, (wn,)):
      wf = MdWireframe( id=row[0],wfname=row[1], wfdesc=row[2], \
                  edges=row[3], created_at=row[4])
      rv.append(wf)
    return rv

  def find_by_dataset_id(self, dsid=''):
    #return
    id= dsid
    #print "dsid in find_by_dataset_id: ", dsid
    sql = "SELECT w.id,w.wfname,w.wfdesc,w.edges,w.created_at FROM mdwireframe w, mddataset d where d.id=? and d.wireframe_id = w.id"
    cur = self.get_dbi().conn.cursor()
    for row in cur.execute(sql, (id,)):
      self.id = row[0]
      self.wfname= row[1]
      self.wfdesc= row[2]
      self.edges= row[3]
      self.created_at = row[4]
      #cur = self.get_dbi().conn.cursor()
    return self

  def find_all(self):
    rv = []
    sql = "SELECT id,wfname,wfdesc,edges,created_at FROM mdwireframe"
    cur = self.get_dbi().conn.cursor()
    for row in cur.execute(sql):
      ds = MdWireframe( id=row[0],wfname=row[1], wfdesc=row[2], \
                  edges=row[3], created_at=row[4])
      rv.append(ds)
    return rv

  def insert_with_cursor(self, cursor):
    try:
      sql = "INSERT INTO mdwireframe(wfname, wfdesc,edges ) VALUES (?,?,?)"
      cursor.execute(sql, (self.wfname, self.wfdesc, self.edges ))
      return cursor.lastrowid
    except sqlite3.OperationalError, e:
      #print "a"
      print e
      raise
    else:
      print "insert error"

  def insert(self):
    #if( self.nickname == '' ): self.set_nickname()
    try:
      cur = self.get_dbi().conn.cursor()
      cur.execute("INSERT INTO mdwireframe\
              (wfname, wfdesc, edges ) VALUES (?,?,?)",
              (self.wfname, self.wfdesc, self.edges ))
      self.id = cur.lastrowid
      self.get_dbi().conn.commit()
    except:
      print "Error occurred while inserting wireframe"
      raise
      
  def delete(self):
    try:
      cursor = self.get_dbi().conn.cursor()
      sql = "DELETE FROM mdwireframe WHERE id=?"
      cursor.execute(sql,(str(self.id),))
      self.get_dbi().conn.commit()
    except:
      print "Error in delete wireframe"
      raise

  def update(self):
    try:
      #print "gonna update"
      cursor = self.get_dbi().conn.cursor()
      cursor.execute("UPDATE mdwireframe SET wfname=?, wfdesc=?, edges=?\
                      WHERE id=?", 
                      ( self.wfname, self.wfdesc, self.edges, 
                       str(self.id)))
      self.get_dbi().conn.commit()
      #print "commit completed"

    except:
      print "Error in update wireframe"
      raise
