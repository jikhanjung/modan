#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary
import datetime
import math
import wx
import zlib
from sqlalchemy.orm import relationship, backref
Base = declarative_base()

class MdLandmark(object):
    selected = False
    dim = 2
    coords = []
    def __init__( self, coords):
        self.coords = [float(x) for x in coords]
        self.dim = len(self.coords)
class MdObject(Base):
    __tablename__ = 'mdobject'
    id = Column(Integer, primary_key=True)
    objname = Column(String,default='')
    objdesc = Column(String,default='')
    scale = Column(Float,default=1.0)
    landmark_str = Column(String,default='')
    dataset_id = Column(Integer, ForeignKey("mddataset.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime)
    image = relationship("MdImage", order_by="MdImage.id", backref="mdobject")
    centroid_size = -1
    property_list = relationship("MdProperty", order_by="MdProperty.id", backref="mdobject")

    landmark_list = []
    has_image = False

    def pack_landmark(self):
        # error check
        self.landmark_str = "\n".join( [",".join([ str(x) for x in lm.coords[:lm.dim] ]) for lm in self.landmark_list] )

    def unpack_landmark(self):
        self.landmark_list = []
        #print "[", self.landmark_str,"]"
        lm_list = self.landmark_str.split("\n")
        for lm in lm_list:
            if lm <> "":
                self.landmark_list.append(MdLandmark(lm.split(",")))

    def get_centroid_size(self,refresh=False):
        return 0

    def get_centroid_coord(self):
        c = MdLandmark([0,0,0])
        if ( len(self.landmark_list) == 0 ):
            self.unpack_landmark()
        if ( len(self.landmark_list) == 0 ):
            return c
        sum_of_x = 0
        sum_of_y = 0
        sum_of_z = 0
        for lm in ( self.landmark_list ):
            sum_of_x += lm.coords[0]
            sum_of_y += lm.coords[1]
            if len(lm.coords) == 3:
                sum_of_z += lm.coords[2]
        lm_count = len(self.landmark_list)
        c.coords[0] = sum_of_x / lm_count
        c.coords[1] = sum_of_y / lm_count
        if len(lm.coords) == 3:
            c.coords[2] = sum_of_z / lm_count
        return c

    def get_centroid_size(self, refresh=False):
        if ( len(self.landmark_list) == 0 ):
            self.unpack_landmark()
        if ( len(self.landmark_list) == 0 ):
            return -1
        if ( ( self.centroid_size > 0 ) and ( refresh == False ) ):
            return self.centroid_size
        centroid = self.get_centroid_coord()
        #print "centroid:", centroid.xcoord, centroid.ycoord, centroid.zcoord
        sum_of_x_squared = 0
        sum_of_y_squared = 0
        sum_of_z_squared = 0
        sum_of_x = 0
        sum_of_y = 0
        sum_of_z = 0
        lm_count = len(self.landmark_list)
        for lm in self.landmark_list:
            sum_of_x_squared += ( lm.coords[0] - centroid.coords[0]) ** 2
            sum_of_y_squared += ( lm.coords[1] - centroid.coords[1]) ** 2
            if len(lm.coords) == 3:
                sum_of_z_squared += ( lm.coords[2] - centroid.coords[2]) ** 2
            sum_of_x += lm.coords[0] - centroid.coords[0]
            sum_of_y += lm.coords[1] - centroid.coords[1]
            if len(lm.coords) == 3:
                sum_of_z += lm.coords[2] - centroid.coords[2]
        centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared
        #centroid_size = sum_of_x_squared + sum_of_y_squared + sum_of_z_squared \
        #              - sum_of_x * sum_of_x / lm_count \
        #              - sum_of_y * sum_of_y / lm_count \
        #              - sum_of_z * sum_of_z / lm_count
        #print centroid_size
        centroid_size = math.sqrt(centroid_size)
        self.centroid_size = centroid_size
        #centroid_size = float( int(  * 100 ) ) / 100
        return centroid_size

    def move(self, x, y, z):
        for lm in self.landmark_list:
            lm.coords[0] = lm.coords[0] + x
            lm.coords[1] = lm.coords[1] + y
            if len(lm.coords) == 3:
                lm.coords[2] = lm.coords[2] + z

    def move_to_center(self):
        centroid = self.get_centroid_coord()
        self.move(-1 * centroid.coords[0], -1 * centroid.coords[1], -1 * centroid.coords[2])

    def rescale(self, size):
        for lm in self.landmark_list:
            lm.coords = [ x * size for x in lm.coords ]

    def rescale_to_unitsize(self):
        centroid_size = self.get_centroid_size(True)
        self.rescale(( 1 / centroid_size ))

    def rotate_2d(self, theta):
        self.rotate_3d(theta, 'Z')
        return

    def rotate_3d(self, theta, axis):
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        r_mx = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        if ( axis == 'Z' ):
            r_mx[0][0] = cos_theta
            r_mx[0][1] = sin_theta
            r_mx[1][0] = -1 * sin_theta
            r_mx[1][1] = cos_theta
        elif ( axis == 'Y' ):
            r_mx[0][0] = cos_theta
            r_mx[0][2] = sin_theta
            r_mx[2][0] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        elif ( axis == 'X' ):
            r_mx[1][1] = cos_theta
            r_mx[1][2] = sin_theta
            r_mx[2][1] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        #print "rotation matrix", r_mx

        for lm in self.landmark_list:
            x_rotated = lm.coords[0] * r_mx[0][0] + lm.coords[1] * r_mx[1][0] + lm.coords[2] * r_mx[2][0]
            y_rotated = lm.coords[0] * r_mx[0][1] + lm.coords[1] * r_mx[1][1] + lm.coords[2] * r_mx[2][1]
            z_rotated = lm.coords[0] * r_mx[0][2] + lm.coords[1] * r_mx[1][2] + lm.coords[2] * r_mx[2][2]
            lm.coords[0] = x_rotated
            lm.coords[1] = y_rotated
            lm.coords[2] = z_rotated

    def trim_decimal(self, dec=4):
        factor = math.pow(10, dec)

        for lm in self.landmark_list:
            lm.coords[0] = float(round(lm.coords[0] * factor)) / factor
            lm.coords[1] = float(round(lm.coords[1] * factor)) / factor
            lm.coords[2] = float(round(lm.coords[2] * factor)) / factor

    def print_landmarks(self, text=''):
        print "[", text, "] [", str(self.get_centroid_size()), "]"
        #    lm= self.landmarks[0]
        for lm in self.landmark_list:
            print lm.coords[0], lm.coords[1], lm.coords[2]
            #break
            #lm= self.landmarks[1]
            #print lm.xcoord, ", ", lm.ycoord, ", ", lm.zcoord

    def sliding_baseline_registration(self, baseline):
        csize = self.get_centroid_size()
        self.bookstein_registration(baseline, csize)

    def bookstein_registration(self, baseline, rescale=-1):
        #c = self.get_centroid_coord()
        #print "centroid:", c.xcoord, ", ", c.ycoord, ", ", c.zcoord

        if len(baseline) == 3:
            point1 = baseline[0]
            point2 = baseline[1]
            point3 = baseline[2]
        elif len(baseline) == 2:
            point1 = baseline[0]
            point2 = baseline[1]
            point3 = None
        point1 = point1 - 1
        point2 = point2 - 1
        if ( point3 != None ):
            point3 = point3 - 1

        #self.print_landmarks("before any processing");

        center = MdLandmark([0,0,0])
        center.coords[0] = ( self.landmark_list[point1].coords[0] + self.landmark_list[point2].coords[0] ) / 2
        center.coords[1] = ( self.landmark_list[point1].coords[1] + self.landmark_list[point2].coords[1] ) / 2
        center.coords[2] = ( self.landmark_list[point1].coords[2] + self.landmark_list[point2].coords[2] ) / 2
        self.move(-1 * center.coords[0], -1 * center.coords[1], -1 * center.coords[2])

        #self.print_landmarks("translation");
        #self.scale_to_univsize()
        xdiff = self.landmark_list[point1].coords[0] - self.landmark_list[point2].coords[0]
        ydiff = self.landmark_list[point1].coords[1] - self.landmark_list[point2].coords[1]
        zdiff = self.landmark_list[point1].coords[2] - self.landmark_list[point2].coords[2]
        #print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff

        size = math.sqrt(xdiff * xdiff + ydiff * ydiff + zdiff * zdiff)
        #print "size: ", size
        #print "rescale: ", rescale
        if ( rescale < 0 ):
            self.rescale(( 1 / size ))
        elif ( rescale > 0 ):
            self.rescale(( 1 / rescale ))

        #self.print_landmarks("rescaling");

        if ( point3 != None ):
            xdiff = self.landmark_list[point1].coords[0] - self.landmark_list[point2].coords[0]
            ydiff = self.landmark_list[point1].coords[1] - self.landmark_list[point2].coords[1]
            zdiff = self.landmark_list[point1].coords[2] - self.landmark_list[point2].coords[2]
            cos_val = xdiff / math.sqrt(xdiff * xdiff + zdiff * zdiff)
            #print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff
            #print "cos val: ", cos_val
            theta = math.acos(cos_val)
            #print "theta: ", theta, ", ", theta * 180/math.pi
            if ( zdiff < 0 ):
                theta = theta * -1
            self.rotate_3d(-1 * theta, 'Y')

        #self.print_landmarks("rotate along xz plane");

        xdiff = self.landmark_list[point1].coords[0] - self.landmark_list[point2].coords[0]
        ydiff = self.landmark_list[point1].coords[1] - self.landmark_list[point2].coords[1]
        zdiff = self.landmark_list[point1].coords[2] - self.landmark_list[point2].coords[2]

        size = math.sqrt(xdiff * xdiff + ydiff * ydiff)
        cos_val = xdiff / size
        #print "x, y, z diff: ", xdiff, ",", ydiff, ",", zdiff
        #print "cos val: ", cos_val
        theta = math.acos(cos_val)
        #print "theta: ", theta, ", ", theta * 180/math.pi
        if ( ydiff < 0 ):
            theta = theta * -1
        self.rotate_2d(-1 * theta)

        if ( point3 != None ):
            xdiff = self.landmark_list[point3].coords[0]
            ydiff = self.landmark_list[point3].coords[1]
            zdiff = self.landmark_list[point3].coords[2]
            size = math.sqrt(ydiff ** 2 + zdiff ** 2)
            cos_val = ydiff / size
            theta = math.acos(cos_val)
            if ( zdiff < 0 ):
                theta = theta * -1
            self.rotate_3d(-1 * theta, 'X')
    def copy(self):
        rv = MdObject()
        rv.id = self.id
        rv.objname = self.objname
        rv.objdesc = self.objdesc
        rv.scale = self.scale
        rv.landmark_str = self.landmark_str
        rv.dataset_id = self.dataset_id
        rv.created_at = self.created_at
        rv.unpack_landmark()
        return rv

dataset_propertyname = Table('dataset_propertyname', Base.metadata,
    Column('dataset_id',Integer,ForeignKey('mddataset.id')),
    Column('propertyname_id',Integer,ForeignKey('mdpropertyname.id'))
)

class MdDataset(Base):
    __tablename__ = 'mddataset'
    id = Column(Integer, primary_key=True)
    dsname = Column(String,default='')
    dsdesc = Column(String,default='')
    dimension = Column(Integer,default=2)
    wireframe = Column(String,default='')
    baseline = Column(String,default='')
    polygons = Column(String,default='')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime)
    object_list = relationship("MdObject", order_by="MdObject.id", backref="dataset")
    propertyname_list = relationship( "MdPropertyName", secondary=dataset_propertyname, backref='dataset_list' )
    edge_list = []
    baseline_point_list = []

    def pack_wireframe(self, edge_list = []):
        if edge_list == []:
            edge_list = self.edge_list

        for points in edge_list:
            points.sort( key = int )
        edge_list.sort()

        new_edges = []
        for points in edge_list:
            #print points
            if len( points ) != 2:
                continue
            new_edges.append( "-".join( [ str(x) for x in points ] ) )
        self.wireframe = ",".join( new_edges )
        return self.wireframe

    def unpack_wireframe(self, wireframe = ''):
        if wireframe == '' and self.wireframe != '' :
            wireframe = self.wireframe

        self.edge_list = []
        if wireframe == '':
            return []

        #print wireframe
        for edge in wireframe.split( "," ):
            has_edge = True
            if edge != '':
                #print edge
                verts = edge.split( "-" )
                int_edge = []
                for v in verts:
                    try:
                        v = int(v)
                    except:
                        has_edge = False
                        #print "Invalid landmark number [", v, "] in wireframe:", edge
                    int_edge.append( v )

                if has_edge:
                    if len( int_edge ) != 2:
                        pass #print "Invalid edge in wireframe:", edge
                    self.edge_list.append( int_edge )

        return self.edge_list
    def pack_polygons(self, polygon_list = []):
        #print polygon_list
        if polygon_list == []:
            polygon_list = self.polygon_list
        for polygon in polygon_list:
            # print polygon
            polygon.sort( key = int )
        polygon_list.sort()

        new_polygons = []
        for polygon in polygon_list:
            #print points
            new_polygons.append( "-".join( [ str(x) for x in polygon ] ) )
        self.polygons = ",".join( new_polygons )
        return self.polygons

    def unpack_polygons(self, polygons = ''):
        if polygons == '' and self.polygons != '' :
            polygons = self.polygons

        self.polygon_list = []
        if polygons == '':
            return []

        for polygon in polygons.split( "," ):
            if polygon != '':
                self.polygon_list.append( [ (int(x)) for x in polygon.split( "-" )]  )

        return self.polygon_list

    def get_edge_list(self):
        return self.edge_list

    def pack_baseline(self, baseline_point_list = []):
        if len( baseline_point_list ) == 0 and len( self.baseline_point_list ) > 0:
            baseline_point_list = self.baseline_point_list
        #print baseline_points
        self.baseline = ",".join( [ str(x) for x in baseline_point_list ] )
        #print self.baseline
        return self.baseline

    def unpack_baseline( self, baseline = '' ):
        if baseline == '' and self.baseline != '':
            baseline = self.baseline

        self.baseline_point_list = []
        if self.baseline == '':
            return []

        self.baseline_point_list = [ (int(x)) for x in self.baseline.split(",") ]
        return self.baseline_point_list

    def get_baseline_points( self ):
        return self.baseline_point_list

class MdPropertyName(Base):
    __tablename__ = 'mdpropertyname'
    id = Column(Integer, primary_key=True)
    propertyname = Column(String,default='')
    def __init__(self,name):
        self.propertyname = name

class MdProperty(Base):
    __tablename__ = 'mdproperty'
    id = Column(Integer, primary_key=True)
    object_id = Column(Integer, ForeignKey("mdobject.id"), nullable=False)
    propertyname_id = Column(Integer, ForeignKey("mdpropertyname.id"), nullable=False)
    property = Column(String,default='')
    def __init__(self,property,mdobject=None,propertyname=None):
        if mdobject:
            self.object_id = mdobject.id
        if propertyname:
            self.propertyname_id = propertyname.id
        self.property = property

class MdImage(Base):
    __tablename__ = 'mdimage'
    id = Column(Integer, primary_key=True)
    imagepath = Column(String)
    ppmm = Column(Integer)
    object_id = Column(Integer, ForeignKey("mdobject.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime)

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
class MdCategory(Base):
    __tablename__ = 'mdcategory'
    id = Column(Integer, primary_key=True)
