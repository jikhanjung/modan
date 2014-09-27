#from data import Tag, Link, Comment
#import sys#,re
from libpy.model import MdModel
import math
from libpy.model_mdlandmark import MdLandmark  
from libpy.model_mdwireframe import MdWireframe
from libpy.model_mdimage import MdImage 
  
class MdObject(MdModel):
  def __init__(self, id=0, objname='', objdesc='', scale='', dataset_id=0, \
               group1='', group2='',group3='',group4='',group5='',group6='',group7='',group8='',group9='',group10='',created_at=''):
    self.selected = False
    self.visible = True
    self.has_image = False
    self.id = id
    self.dataset_id = dataset_id
    self.objname = objname
    self.objdesc = objdesc
    self.scale = scale
    self.group1 = group1
    self.group2 = group2
    self.group3 = group3
    self.group4 = group4
    self.group5 = group5
    self.group6 = group6
    self.group7 = group7
    self.group8 = group8
    self.group9 = group9
    self.group10 = group10
    self.group_list = []
    self.group_list.append( group1 )
    self.group_list.append( group2 )
    self.group_list.append( group3 )
    self.group_list.append( group4 )
    self.group_list.append( group5 )
    self.group_list.append( group6 )
    self.group_list.append( group7 )
    self.group_list.append( group8 )
    self.group_list.append( group9 )
    self.group_list.append( group10 )
    self.centroid_size = -1
    #self.lmcount = lmcount
    self.created_at = created_at
    self.image = ''

    self.landmarks = []
    if self.id > 0:
      self.load_image()
    #self.group_list= []
    #self.unpack_grouplist()
    
  def insert(self):

    try:
      #print self.group_list
      cur = self.get_dbi().conn.cursor()
      cur.execute("INSERT INTO mdobject \
              (objname, objdesc, scale, group1, group2, group3, group4, group5, group6, group7, group8, group9, group10, dataset_id ) VALUES \
              (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (self.objname, self.objdesc, self.scale, self.group_list[0], self.group_list[1], self.group_list[2], self.group_list[3], self.group_list[4], self.group_list[5], self.group_list[6],
               self.group_list[7], self.group_list[8], self.group_list[9], self.dataset_id ))
      self.id = cur.lastrowid

      # insert landmarks
      for lm in self.landmarks:
        lm.object_id = self.id
        lm.dataset_id = self.dataset_id
        lm.insert_with_cursor(cur)
      if self.has_image:
        self.image.object_id = self.id
        self.image.insert_with_cursor(cur)

      self.get_dbi().conn.commit()
    except:
      self.get_dbi().conn.rollback()
      print "Error in insert mdobject"
      raise

    
  def delete(self):
    try:
      cursor = self.get_dbi().conn.cursor()
      sql = "DELETE FROM mdobject WHERE id=?"
      cursor.execute(sql,(str(self.id),))
      
      lm = MdLandmark()
      lm.delete_with_cursor_and_object_id(cursor, self.id)
      #lm.clean_with_cursor(cursor)
      img = MdImage()
      img.delete_with_cursor_and_object_id(cursor, self.id)

      self.get_dbi().conn.commit() 
    except:
      self.get_dbi().conn.rollback()
      print "Error in delete MdObject"
      raise
    return True

  def update(self):
    try:
      cursor = self.get_dbi().conn.cursor()
      cursor.execute("UPDATE mdobject SET objname=?, objdesc=?, scale=?, group1=?, group2=?, group3=?, group4=?, group5=?, group6=?,\
      group7=?, group8=?, group9=?, group10=?, dataset_id=? \
                      WHERE id=?", 
                      (self.objname, self.objdesc, self.scale, self.group_list[0], self.group_list[1], self.group_list[2], self.group_list[3], self.group_list[4], self.group_list[5], self.group_list[6],
               self.group_list[7], self.group_list[8], self.group_list[9], self.dataset_id, str(self.id)))

      # delete and insert landmarks
      lm = MdLandmark()
      lm.delete_with_cursor_and_object_id(cursor, self.id )
      if( len(self.landmarks) ):
        for l in self.landmarks:
          l.object_id = self.id
          l.dataset_id = self.dataset_id
          l.insert_with_cursor(cursor)

      img = MdImage()
      img.delete_with_cursor_and_object_id (cursor, self.id )
      if( self.has_image ):
        self.image.object_id = self.id
        self.image.insert_with_cursor(cursor)
      self.get_dbi().conn.commit()

    except:
      self.get_dbi().conn.rollback()
      print "Error in update MdObject"
      raise

  def find(self):
    sql = "SELECT id,objname,objdesc,scale,group1,group2,group3,group4,group5,group6,group7,group8,group9,group10,dataset_id,\
            created_at FROM mdobject WHERE id=?"
    cursor = self.get_dbi().conn.cursor()
    for row in cursor.execute(sql, (str(self.id),)):
      self.id = row[0]
      self.objname = row[1]
      self.objdesc = row[2]
      self.scale = row[3]
      for j in range(10):
        #eval( "self.group" + str(j) + " = row["+str(j+4)+"]" )# + str(j) ) = row[j+4]
        self.group_list[j] = row[j+4]
      self.dataset_id = row[14]
      self.created_at = row[15]
      self.load_landmarks()
      self.load_image()
    return self

  def copy(self):
    rv = MdObject()
    rv.id = self.id
    rv.objname = self.objname
    rv.objdesc = self.objdesc
    rv.scale = self.scale
    rv.group1 = self.group1
    rv.group2 = self.group2
    rv.group3 = self.group3
    rv.group4 = self.group4
    rv.group5 = self.group5
    rv.group6 = self.group6
    rv.group7 = self.group7
    rv.group8 = self.group8
    rv.group9 = self.group9
    rv.group10 = self.group10
    rv.group_list[:] = self.group_list[:]
    rv.dataset_id = self.dataset_id
    rv.created_at = self.created_at
    rv.load_landmarks()
    rv.load_image()
    return rv
    

  def find_all(self):
    rv = []
    sql = "SELECT id,objname,objdesc,scale,dataset_id,group1,group2,group3,group4,group5,group6,group7,group8,group9,group10,created_at\
            FROM mdobject"
    cur = self.get_dbi().conn.cursor()
    for row in cur.execute(sql):
      mdobject = MdObject(id=row[0], objname=row[1], objdesc=row[2],scale=row[3], dataset_id=row[4], 
                          group1=row[5],\
                          group2=row[6],group3=row[7],group4=row[8],group5=row[9],group6=row[10],group7=row[11],group8=row[12],\
                          group9=row[13],group10=row[14],
                          create_at=row[15])
      rv.append(mdobject)
    return rv

  def find_by_dataset_id(self,dataset_id):
    #print "dsid: [" + dataset_id + "]"
    dsid = dataset_id
    rv = []
    sql = "SELECT id,objname,objdesc,scale,dataset_id,group1,group2,group3,group4,group5,group6,group7,group8,group9,group10,created_at \
            FROM mdobject where dataset_id=? order by id "
    cur = self.get_dbi().conn.cursor()
    for row in cur.execute(sql, (str(dsid),) ):
      mdobject = MdObject(id=row[0], objname=row[1], objdesc=row[2],scale=row[3], dataset_id=row[4], group1=row[5],\
                          group2=row[6],group3=row[7],group4=row[8],group5=row[9],group6=row[10],group7=row[11],group8=row[12],\
                          group9=row[13],group10=row[14],create_at=row[15])
      rv.append(mdobject)
    return rv

  def find_with_cursor_and_dataset_id(self,cur, dataset_id):
    dsid = dataset_id
    rv = []
    sql = "SELECT id,objname,objdesc,scale,dataset_id,group1,group2,group3,group4,group5,group6,group7,group8,group9,group10,created_at \
            FROM mdobject where dataset_id=? order by id "
    for row in cur.execute(sql, (str(dsid),) ):
      mdobject = MdObject(id=row[0], objname=row[1], objdesc=row[2],scale=row[3], dataset_id=row[4], group1=row[5],\
                          group2=row[6],group3=row[7],group4=row[8],group5=row[9],group6=row[10],group7=row[11],group8=row[12],\
                          group9=row[13],group10=row[14],created_at=row[15])
      rv.append(mdobject)
    return rv

  def find_by_dataset_name(self,dataset_name):
    #print "dsid: [" + dataset_id + "]"
    dsname = dataset_name
    rv = []
    sql = "SELECT o.id,o.objname,o.objdesc,o.scale,o.dataset_id,o.group1,o.group2,o.group3,o.group4,o.group5,o.group6,o.group7,o.group8,o.group9,o.group10,o.created_at \
            FROM mdobject o, mddataset d where o.dataset_id=d.id and d.dsname = ? order by o.id "
    cur = self.get_dbi().conn.cursor()
    for row in cur.execute(sql, (str(dsname),) ):
      mdobject = MdObject(id=row[0], objname=row[1], objdesc=row[2],scale=row[3], dataset_id=row[4], group1=row[5],\
                          group2=row[6],group3=row[7],group4=row[8],group5=row[9],group6=row[10],group7=row[11],group8=row[12],\
                          group9=row[13],group10=row[14],created_at=row[15])
      rv.append(mdobject)
    return rv

  def load_image(self):
    img = MdImage()
    img_list = img.find_by_object_id( self.id )
    #print img_list
    if len( img_list ) > 0:
      self.image = img_list[0]
      self.has_image = True
    else:
      self.image = ''
      self.has_image = False
    #print "has_image:", self.has_image
    return

  def attach_image(self, image):
    if image.ClassName == 'wxImage':
      self.image = MdImage()
      self.image.set_image_object( image )
      self.image.object_id = self.id
      self.has_image = True
    elif image.ClassName == 'MdImage':
      self.image = image
      self.has_image = True
    return self.image

  def get_image(self):
    if self.image.ClassName == 'MdImage':
      return self.image

  def load_landmarks(self):
    #cur = self.get_dbi().conn.cursor()
    c = MdLandmark()
    self.landmarks = c.find_by_object_id(self.id)

  def get_dataset(self ):
    if self.dataset_id <= 0 :
      return
    
    from libpy.model_mddataset import MdDataset 
    ds = MdDataset()
    ds.id = self.dataset_id
    return ds.find()
    
  def get_centroid_coord(self):
    c = MdLandmark()
    if( len( self.landmarks ) == 0 ):
      self.load_landmarks()
    if( len( self.landmarks ) == 0 ):
      return c
    sum_of_x = 0
    sum_of_y = 0
    sum_of_z = 0
    for lm in ( self.landmarks ):
      sum_of_x += lm.xcoord
      sum_of_y += lm.ycoord
      sum_of_z += lm.zcoord
    lm_count = len( self.landmarks )
    c.xcoord = sum_of_x / lm_count  
    c.ycoord = sum_of_y / lm_count  
    c.zcoord = sum_of_z / lm_count
    return c
  
  def get_centroid_size(self, refresh = False):
    if( len( self.landmarks ) == 0 ):
      self.load_landmarks()
    if( len( self.landmarks ) == 0 ):
      return -1
    if( ( self.centroid_size > 0 ) and ( refresh == False ) ):
      return self.centroid_size
    centroid = self.get_centroid_coord()
    #print "centroid:", centroid.xcoord, centroid.ycoord, centroid.zcoord
    sum_of_x_squared = 0
    sum_of_y_squared = 0
    sum_of_z_squared = 0
    sum_of_x = 0
    sum_of_y = 0
    sum_of_z = 0
    lm_count = len( self.landmarks )
    for lm in ( self.landmarks ):
      sum_of_x_squared += ( lm.xcoord - centroid.xcoord ) ** 2
      sum_of_y_squared += ( lm.ycoord - centroid.ycoord ) ** 2
      sum_of_z_squared += ( lm.zcoord - centroid.zcoord ) ** 2
      #sum_of_y_squared += lm.ycoord * lm.ycoord
      #sum_of_z_squared += lm.zcoord * lm.zcoord
      sum_of_x += lm.xcoord - centroid.xcoord 
      sum_of_y += lm.ycoord - centroid.ycoord
      sum_of_z += lm.zcoord - centroid.zcoord
    centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared 
    #centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared \
    #              - sum_of_x * sum_of_x / lm_count \
    #              - sum_of_y * sum_of_y / lm_count \
    #              - sum_of_z * sum_of_z / lm_count
    #print centroid_size
    centroid_size = math.sqrt( centroid_size )
    self.centroid_size = centroid_size
    #centroid_size = float( int(  * 100 ) ) / 100
    return centroid_size

  def move(self, x, y, z):
    for lm in ( self.landmarks ):
      lm.xcoord = lm.xcoord + x
      lm.ycoord = lm.ycoord + y
      lm.zcoord = lm.zcoord + z

  def move_to_center(self):
    centroid = self.get_centroid_coord()
    self.move( -1 * centroid.xcoord, -1 * centroid.ycoord, -1 * centroid.zcoord )

  def rescale(self, size ):
    for lm in ( self.landmarks ):
      lm.xcoord = lm.xcoord * size
      lm.ycoord = lm.ycoord * size
      lm.zcoord = lm.zcoord * size

  def rescale_to_unitsize(self):
    centroid_size = self.get_centroid_size( True )
    self.rescale( ( 1 / centroid_size ) )
  
  def rotate_2d(self, theta ):
    self.rotate_3d( theta, 'Z' )
    return
  
  def rotate_3d( self, theta, axis ):
    cos_theta = math.cos( theta )
    sin_theta = math.sin( theta )
    r_mx = [ [1,0,0],[0,1,0],[0,0,1] ]
    if( axis == 'Z' ):
      r_mx[0][0] = cos_theta
      r_mx[0][1] = sin_theta
      r_mx[1][0] = -1 * sin_theta
      r_mx[1][1] = cos_theta
    elif( axis == 'Y' ):
      r_mx[0][0] = cos_theta
      r_mx[0][2] = sin_theta
      r_mx[2][0] = -1 * sin_theta
      r_mx[2][2] = cos_theta
    elif( axis == 'X' ):
      r_mx[1][1] = cos_theta
      r_mx[1][2] = sin_theta
      r_mx[2][1] = -1 * sin_theta
      r_mx[2][2] = cos_theta
    #print "rotation matrix", r_mx

    for lm in ( self.landmarks ):
      x_rotated = lm.xcoord * r_mx[0][0] + lm.ycoord * r_mx[1][0] + lm.zcoord * r_mx[2][0]
      y_rotated = lm.xcoord * r_mx[0][1] + lm.ycoord * r_mx[1][1] + lm.zcoord * r_mx[2][1]
      z_rotated = lm.xcoord * r_mx[0][2] + lm.ycoord * r_mx[1][2] + lm.zcoord * r_mx[2][2]
      lm.xcoord = x_rotated
      lm.ycoord = y_rotated
      lm.zcoord = z_rotated
  def trim_decimal(self, dec = 4):
    factor = math.pow( 10, dec )
    
    for lm in ( self.landmarks ):
      lm.xcoord = float( round( lm.xcoord * factor ) ) / factor 
      lm.ycoord = float( round( lm.ycoord * factor ) ) / factor 
      lm.zcoord = float( round( lm.zcoord * factor ) ) / factor 
  def print_landmarks(self, text = ''):
    print "[", text, "] [", str( self.get_centroid_size() ), "]"
#    lm= self.landmarks[0]
    for lm in self.landmarks:
      print lm.xcoord, lm.ycoord, lm.zcoord
      #break
    #lm= self.landmarks[1]
    #print lm.xcoord, ", ", lm.ycoord, ", ", lm.zcoord
    
  def sliding_baseline_registration( self, baseline ):
    csize = self.get_centroid_size()
    self.bookstein_registration(baseline, csize)
    
  def bookstein_registration(self, baseline, rescale = -1 ):
    #c = self.get_centroid_coord()  
    #print "centroid:", c.xcoord, ", ", c.ycoord, ", ", c.zcoord
    
    if len( baseline ) == 3:
      point1 = baseline[0]
      point2 = baseline[1]
      point3 = baseline[2]
    elif len( baseline ) == 2:
      point1 = baseline[0]
      point2 = baseline[1]
      point3 = None
    point1 = point1 - 1
    point2 = point2 - 1
    if( point3 != None ):
      point3 = point3 - 1
    
    #self.print_landmarks("before any processing");

    center = MdLandmark()
    center.xcoord = ( self.landmarks[point1].xcoord + self.landmarks[point2].xcoord ) / 2
    center.ycoord = ( self.landmarks[point1].ycoord + self.landmarks[point2].ycoord ) / 2
    center.zcoord = ( self.landmarks[point1].zcoord + self.landmarks[point2].zcoord ) / 2
    self.move( -1 * center.xcoord, -1 * center.ycoord, -1 * center.zcoord )

    #self.print_landmarks("translation");
    #self.scale_to_univsize()
    xdiff = self.landmarks[point1].xcoord - self.landmarks[point2].xcoord
    ydiff = self.landmarks[point1].ycoord - self.landmarks[point2].ycoord
    zdiff = self.landmarks[point1].zcoord - self.landmarks[point2].zcoord
    #print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff
    
    size = math.sqrt( xdiff * xdiff + ydiff * ydiff + zdiff * zdiff )
    #print "size: ", size
    #print "rescale: ", rescale
    if( rescale < 0 ):
      self.rescale( ( 1 / size ) )
    elif( rescale > 0 ):
      self.rescale( ( 1 / rescale ) )
      
    #self.print_landmarks("rescaling");
    
    if( point3 != None ):
      xdiff = self.landmarks[point1].xcoord - self.landmarks[point2].xcoord
      ydiff = self.landmarks[point1].ycoord - self.landmarks[point2].ycoord
      zdiff = self.landmarks[point1].zcoord - self.landmarks[point2].zcoord
      cos_val = xdiff / math.sqrt( xdiff * xdiff + zdiff * zdiff ) 
      #print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff
      #print "cos val: ", cos_val
      theta = math.acos( cos_val )
      #print "theta: ", theta, ", ", theta * 180/math.pi
      if( zdiff < 0 ):
        theta = theta * -1
      self.rotate_3d( -1 * theta, 'Y' )

    #self.print_landmarks("rotate along xz plane");

    xdiff = self.landmarks[point1].xcoord - self.landmarks[point2].xcoord
    ydiff = self.landmarks[point1].ycoord - self.landmarks[point2].ycoord
    zdiff = self.landmarks[point1].zcoord - self.landmarks[point2].zcoord
    
    size = math.sqrt( xdiff * xdiff + ydiff * ydiff )
    cos_val = xdiff / size 
    #print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff
    #print "cos val: ", cos_val
    theta = math.acos( cos_val )
    #print "theta: ", theta, ", ", theta * 180/math.pi
    if( ydiff < 0 ):
      theta = theta * -1
    self.rotate_2d( -1 * theta )

    if( point3 != None ):
      xdiff = self.landmarks[point3].xcoord
      ydiff = self.landmarks[point3].ycoord
      zdiff = self.landmarks[point3].zcoord
      size = math.sqrt( ydiff ** 2 + zdiff** 2)
      cos_val = ydiff / size
      theta = math.acos( cos_val )
      if( zdiff < 0 ):
        theta = theta * -1
      self.rotate_3d( -1 * theta, 'X' )

    #self.print_landmarks("rotate along xy plane");
from libpy.model_mddataset import MdDataset 
    