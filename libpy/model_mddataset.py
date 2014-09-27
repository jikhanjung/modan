#from data import Tag, Link, Comment
#import sys#,re
import math
import numpy

import sqlite3
from libpy.model import MdModel   
from libpy.model_mdlandmark import MdLandmark
from libpy.modan_exception import MdException
   
class MdDataset(MdModel):
    def __init__(self, dsid=0, dsname='', dsdesc='', dimension='', groupname='', wireframe='', baseline='',polygons='',created_at=''):
        self.id = dsid
        self.dsname = dsname  
        self.dsdesc = dsdesc
        self.dimension = dimension
        self.groupname = groupname 
        self.wireframe = wireframe
        self.baseline = baseline
        self.polygons = polygons
        self.created_at = created_at
        self.reference_shape = None
    
        self.polygon_list = []
        self.objects = []
        self.edge_list = []
        self.baseline_points = []
        self.groupname_list = []
        
        if polygons != '':
            self.unpack_polygons( polygons )
        if groupname != '':
            self.unpack_groupname( groupname )
        if wireframe != '':
            self.unpack_wireframe( wireframe )
        if baseline != '':
            self.unpack_baseline( baseline )

    def copy(self):
        ds = MdDataset()
        ds.id = self.id
        ds.dsname = self.dsname
        ds.dsdesc = self.dsdesc
        ds.dimension = self.dimension
        ds.groupname = self.groupname
        ds.wireframe = self.wireframe
        ds.baseline = self.baseline
        ds.polygons = self.polygons
        ds.created_at = self.created_at
        ds.unpack_groupname()
        ds.unpack_polygons()
        ds.unpack_wireframe()
        ds.unpack_baseline()
        return ds

    def find(self):
        sql = "SELECT id,dsname,dsdesc,dimension,groupname,wireframe,baseline,polygons,\
                created_at FROM mddataset WHERE id=?"
        cursor = self.get_dbi().conn.cursor()
        for row in cursor.execute(sql, (str(self.id),)):
            self.id = row[0]
            self.dsname = row[1]
            self.dsdesc = row[2]
            self.dimension = row[3]
            self.groupname = row[4]
            self.wireframe = row[5]
            self.baseline= row[6]
            self.polysonge= row[7]
            self.created_at = row[8]
            self.unpack_groupname()
            self.unpack_wireframe()
            self.unpack_baseline()
            self.unpack_polygons()
            #cur = self.get_dbi().conn.cursor()
        return self

    def find_by_name(self, dsname=''):
        rv = []
        dn = dsname
        sql = "SELECT id, dsname, dsdesc, dimension, groupname, wireframe, baseline,polygons,created_at FROM mddataset where dsname=?"
        cur = self.get_dbi().conn.cursor()
        for row in cur.execute(sql, (dn,)):
            ds = MdDataset( dsid=row[0],dsname=row[1], dsdesc=row[2], \
                        dimension=row[3], groupname=row[4], wireframe=row[5], baseline=row[6],polygons=row[7],created_at=row[8])
            ds.unpack_groupname()
            ds.unpack_wireframe()
            ds.unpack_baseline()
            ds.unpack_polygons()
            rv.append(ds)
        return rv
  
    def find_all(self):
        rv = []
        sql = "SELECT id,dsname,dsdesc,dimension,groupname,wireframe,baseline,polygons,created_at FROM mddataset"
        cur = self.get_dbi().conn.cursor()
        for row in cur.execute(sql):
            ds = MdDataset( dsid=row[0],dsname=row[1], dsdesc=row[2], \
                        dimension=row[3], groupname=row[4], wireframe=row[5], baseline=row[6],polygons=row[7],created_at=row[8])
            ds.unpack_groupname()
            ds.unpack_wireframe()
            ds.unpack_baseline()
            ds.unpack_polygons()
            rv.append(ds)
        return rv

    def insert(self):
        #if( self.nickname == '' ): self.set_nickname()
        try:
            rds = self.find_by_name( dsname=self.dsname )
            if( len( rds ) > 0 ):
                print "already existing dataset name!"
                raise sqlite3.OperationalError( 'already existing dataset name' )
            if len( self.edge_list ) > 0 and self.wireframe == '':
                self.pack_wireframe()
            if len( self.groupname_list ) > 0 and self.groupname == '':
                self.pack_groupname()
            if len( self.baseline_points ) > 0 and self.baseline == '':
                self.pack_baseline()
            if len( self.polygon_list ) > 0 and self.polygons == '':
                self.pack_polygons()
            #print "insert dataset"
            cur = self.get_dbi().conn.cursor()
            cur.execute("INSERT INTO mddataset\
                    (dsname, dsdesc, dimension, groupname,wireframe,baseline,polygons) VALUES (?,?,?,?,?,?,?)",
                    (self.dsname, self.dsdesc, self.dimension, self.groupname,self.wireframe,self.baseline,self.polygons))
            self.id = cur.lastrowid
            self.get_dbi().conn.commit()
        except:
            print "Error in insert Dataset"
            raise
        
    def update(self):
        try:
            #print "gonna update"
            if len( self.edge_list ) > 0 and self.wireframe == '':
                self.pack_wireframe()
            if len( self.groupname_list ) > 0 and self.groupname == '':
                self.pack_groupname()
            if len( self.baseline_points ) > 0 and self.baseline == '':
                self.pack_baseline()
            if len( self.polygon_list ) > 0 and self.polygons == '':
                self.pack_polygons()
            cursor = self.get_dbi().conn.cursor()
            cursor.execute("UPDATE mddataset SET dsname=?, dsdesc=?, dimension=?,\
                            groupname=?,wireframe=?,baseline=?,polygons=? \
                            WHERE id=?", 
                            (self.dsname, self.dsdesc, self.dimension, self.groupname,self.wireframe, self.baseline,self.polygons,
                             str(self.id)))
            #print "update executed"
            # delete and insert landmarks
        except:
            print "Error in update Dataset"
            raise
        
        self.get_dbi().conn.commit()
    
    def delete(self):
        try:
            cursor = self.get_dbi().conn.cursor()
            sql = "DELETE FROM mddataset WHERE id=?"
            cursor.execute(sql,(str(self.id),))
            
            self.get_dbi().conn.commit()
        except:
            print "Error in delete Dataset"
            raise
        return True

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

    def pack_groupname(self, groupname_list = []):
        if groupname_list == []:
            groupname_list = self.groupname_list

        self.groupname = ",".join( groupname_list )
        return self.groupname

    def unpack_groupname(self, groupname = ''):
        if groupname == '' and self.groupname != '' :
            groupname = self.groupname

        self.groupname_list = []
        if groupname == '':
            return []

        self.groupname_list = self.groupname.split( "," )
    
        return self.groupname_list

    def get_edge_list(self):
        return self.edge_list
  
    def pack_baseline(self, baseline_points = []):
        if len( baseline_points ) == 0 and len( self.baseline_points ) > 0:
            baseline_points = self.baseline_points
        #print baseline_points
        self.baseline = ",".join( [ str(x) for x in baseline_points ] )
        #print self.baseline
        return self.baseline

    def unpack_baseline( self, baseline = '' ):
        if baseline == '' and self.baseline != '':
            baseline = self.baseline
    
        self.baseline_points = []
        if self.baseline == '':
            return []
    
        self.baseline_points = [ (int(x)) for x in self.baseline.split(",") ]
        return self.baseline_points

    def get_baseline_points( self ):
        return self.baseline_points

    def load_objects( self ):
        from libpy.model_mdobject import MdObject
        cur = self.get_dbi().conn.cursor()
        mo = MdObject()
        self.objects = mo.find_with_cursor_and_dataset_id(cur,self.id)

    def set_reference_shape(self, shape ):
        self.reference_shape = shape
  
    def rotate_gls_to_reference_shape( self, object_index ):
        num_obj = len( self.objects )
        if( num_obj == 0 or num_obj - 1 < object_index  ):
            return
        
        mo = self.objects[object_index]
        nlandmarks = len( mo.landmarks )
        target_shape = numpy.zeros((nlandmarks,3))
        reference_shape = numpy.zeros((nlandmarks,3))
        
        i = 0
        for lm in ( mo.landmarks ):
            target_shape [i] = ( lm.xcoord, lm.ycoord, lm.zcoord )
            i += 1
    
        i = 0
        for lm in ( self.reference_shape.landmarks ):
            reference_shape [i] = ( lm.xcoord, lm.ycoord, lm.zcoord )
            i += 1
    
        rotation_matrix = self.rotation_matrix( reference_shape, target_shape )
        #print rotation_matrix
        #target_transposed = numpy.transpose( target_shape )
        #print target_transposed
        #print rotation_matrix.shape
        #print target_transposed.shape
        rotated_shape = numpy.transpose( numpy.dot( rotation_matrix, numpy.transpose( target_shape ) ) )
        
        #print rotated_shape
    
        i = 0
        for lm in ( mo.landmarks ):
            ( lm.xcoord, lm.ycoord, lm.zcoord ) = ( rotated_shape[i,0], rotated_shape[i,1], rotated_shape[i,2] )
            i+=1

    def rotation_matrix(self, ref, target ):
    #assert( ref[0] == 3 )
    #assert( ref.shape == target.shape )
    
        correlation_matrix = numpy.dot( numpy.transpose(ref), target )
        v, s, w = numpy.linalg.svd( correlation_matrix )
        s
        is_reflection = ( numpy.linalg.det(v) * numpy.linalg.det(w) ) < 0.0
        if is_reflection:
            v[-1,:] = -v[-1,:]
        return numpy.dot( v, w )

    def get_average_shape( self ):
        from libpy.model_mdobject import MdObject
        object_count = len( self.objects )
        if( object_count == 0 ):
            self.set_objects()
        
        average_shape = MdObject()
        average_shape.landmarks = []
        
        sum_x = []
        sum_y = []
        sum_z = []
        
        for mo in self.objects:
            i = 0
            for lm in mo.landmarks:
                if len( sum_x ) <= i:
                    sum_x.append(0)
                    sum_y.append(0)
                    sum_z.append(0)
                sum_x[i] += lm.xcoord
                sum_y[i] += lm.ycoord
                sum_z[i] += lm.zcoord
                i += 1
        for i in range(len( sum_x )):
            lm = MdLandmark()
            lm.xcoord = float( sum_x[i] ) / object_count
            lm.ycoord = float( sum_y[i] ) / object_count
            lm.zcoord = float( sum_z[i] ) / object_count
            average_shape.landmarks.append( lm )
        if self.id:
            average_shape.dataset_id = self.id
        return average_shape

    def check_objects(self):
        if( len( self.objects ) == 0 ):
            if(  self.id ):
                self.load_objects()
            else:
                raise MdException, "No objects to transform!"
        
        for mo in self.objects:
            mo.load_landmarks()
        
        min_number_of_landmarks = 999
        max_number_of_landmarks = 0
        sum_val = 0
        for mo in self.objects:
            number_of_landmarks = len( mo.landmarks )
            # print number_of_landmarks
            sum_val += number_of_landmarks
            min_number_of_landmarks = min( min_number_of_landmarks, number_of_landmarks )
            max_number_of_landmarks = max( max_number_of_landmarks, number_of_landmarks )
        #average_number_of_landmarks = float( sum_val ) / len( self.objects )
        #print min_number_of_landmarks, max_number_of_landmarks
        if sum_val > 0 and min_number_of_landmarks != max_number_of_landmarks:
            raise MdException, "Inconsistent number of landmarks"
            return

    def procrustes_superimposition(self):
        #print "begin_procrustes"
        try:
            self.check_objects()
        except MdException, e:
            raise e
        
        for mo in self.objects:
            #mo.set_landmarks()
            mo.move_to_center()
            mo.rescale_to_unitsize()
        
        average_shape = None
        previous_average_shape = None
        i = 0
        while( True ):
            i += 1
            #print "progressing...", i
            previous_average_shape = average_shape
            average_shape = self.get_average_shape()
            #average_shape.print_landmarks()
            if( self.is_same_shape( previous_average_shape, average_shape ) and previous_average_shape != None ):
                break
            self.set_reference_shape(average_shape)
            for j in range( len( self.objects ) ):
                self.rotate_gls_to_reference_shape(j)
            #self.objects[0].print_landmarks('aa') 
            #self.objects[1].print_landmarks('bb')  
            #average_shape.print_landmarks('cc')
      
    def is_same_shape(self, shape1, shape2 ):
        if( shape1 == None or shape2 == None ):
            return False
        sum_coord = 0
        for i in range( len( shape1.landmarks ) ):
            sum_coord += ( shape1.landmarks[i].xcoord - shape2.landmarks[i].xcoord ) ** 2
            sum_coord += ( shape1.landmarks[i].ycoord - shape2.landmarks[i].ycoord ) ** 2
            sum_coord += ( shape1.landmarks[i].zcoord - shape2.landmarks[i].zcoord ) ** 2
        #shape1.print_landmarks("shape1")
        #shape2.print_landmarks("shape2")
        sum_coord = math.sqrt( sum_coord )
        #print "diff: ", sum
        if( sum_coord < 10 ** -10 ):
            return True 
        return False

    def resistant_fit_superimposition(self):
        if( len( self.objects ) == 0 ):
            if(  self.id ):
                self.set_objects()
            else:
                raise "No objects to transform!"
                return
        
        for mo in self.objects:
            mo.load_landmarks()
            mo.move_to_center()
        average_shape = None
        previous_average_shape = None
        
        i = 0
        while( True ):
            i += 1
            #print "iteration: ", i
            previous_average_shape = average_shape
            average_shape = self.get_average_shape()
            average_shape.rescale_to_unitsize()
            if( self.is_same_shape( previous_average_shape, average_shape ) and previous_average_shape != None ):
                break
            self.set_reference_shape(average_shape)
            for j in range( len( self.objects ) ):
                self.rotate_resistant_fit_to_reference_shape(j)

    def rotate_vector_2d(self, theta, vec ):
        return self.rotate_vector_3d( theta, vec, 'Z' )
  
    def rotate_vector_3d( self, theta, vec, axis ):
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
    
        x_rotated = vec[0] * r_mx[0][0] + vec[1] * r_mx[1][0] + vec[2] * r_mx[2][0]
        y_rotated = vec[0] * r_mx[0][1] + vec[1] * r_mx[1][1] + vec[2] * r_mx[2][1]
        z_rotated = vec[0] * r_mx[0][2] + vec[1] * r_mx[1][2] + vec[2] * r_mx[2][2]
        vec[0] = x_rotated
        vec[1] = y_rotated
        vec[2] = z_rotated
        return vec

    def rotate_resistant_fit_to_reference_shape( self, object_index ):
        num_obj = len( self.objects )
        if( num_obj == 0 or num_obj - 1 < object_index  ):
            return
        
        target_shape = self.objects[object_index]
        nlandmarks = len( target_shape.landmarks )
        #target_shape = numpy.zeros((nlandmarks,3))
        reference_shape = self.reference_shape    
    
        #rotation_matrix = self.rotation_matrix( reference_shape, target_shape )
    
        #rotated_shape = numpy.transpose( numpy.dot( rotation_matrix, numpy.transpose( target_shape ) ) )
    
        # obtain scale factor using repeated median
        landmark_count = len( reference_shape.landmarks ) 
        inner_tau_array = []
        outer_tau_array = []
        for i in range( landmark_count-1 ):
            for j in range( i+1, landmark_count ):
                target_distance = math.sqrt( ( target_shape.landmarks[i].xcoord - target_shape.landmarks[j].xcoord ) ** 2 + \
                           ( target_shape.landmarks[i].ycoord - target_shape.landmarks[j].ycoord ) ** 2 + \
                           ( target_shape.landmarks[i].zcoord - target_shape.landmarks[j].zcoord ) ** 2 )
                reference_distance = math.sqrt( ( reference_shape.landmarks[i].xcoord - reference_shape.landmarks[j].xcoord ) ** 2 + \
                           ( reference_shape.landmarks[i].ycoord - reference_shape.landmarks[j].ycoord ) ** 2 + \
                           ( reference_shape.landmarks[i].zcoord - reference_shape.landmarks[j].zcoord ) ** 2 )
                tau = reference_distance / target_distance
                inner_tau_array.append( tau )
                median_index = self.get_median_index( inner_tau_array )
            #       print median_index
            #print "tau: ", inner_tau_array
            outer_tau_array.append( inner_tau_array[median_index] )
            inner_tau_array = []
        median_index = self.get_median_index( outer_tau_array ) 
        #print "tau: ", outer_tau_array
        tau_final = outer_tau_array[median_index]
    
        # rescale to scale factor
        #print "index:", object_index
        #print "scale factor:", tau_final
        #target_shape.print_landmarks("before rescale")
        target_shape.rescale( tau_final )
        #target_shape.print_landmarks("after rescale")
        #exit
        
        # obtain rotation angle using repeated median
        inner_theta_array = []
        outer_theta_array = []
        inner_vector_array = []
        outer_vector_array = []
        for i in range( landmark_count -1):
            for j in range( i+1, landmark_count ):
                # get vector
                target_vector = numpy.array( [ target_shape.landmarks[i].xcoord - target_shape.landmarks[j].xcoord, \
                                target_shape.landmarks[i].ycoord - target_shape.landmarks[j].ycoord, \
                                target_shape.landmarks[i].zcoord - target_shape.landmarks[j].zcoord ] )
                reference_vector = numpy.array( [ reference_shape.landmarks[i].xcoord - reference_shape.landmarks[j].xcoord, \
                                reference_shape.landmarks[i].ycoord - reference_shape.landmarks[j].ycoord, \
                                reference_shape.landmarks[i].zcoord - reference_shape.landmarks[j].zcoord ] )
            #       cos_val = ( target_vector[0] * reference_vector[0] + \
            #                   target_vector[1] * reference_vector[1] + \
            #                   target_vector[2] * reference_vector[2] ) \
            #                  / \
            #                  ( math.sqrt( target_vector[0] ** 2 + target_vector[1]**2 + target_vector[2]**2 ) * \
            #                    math.sqrt( reference_vector[0] ** 2 + reference_vector[1]**2 + reference_vector[2]**2 ) )
            #        if( cos_val > 1.0 ):
            #          print "cos_val 1: ", cos_val
            #          print target_vector
            #          print reference_vector
            #          print math.acos( cos_val )
            #          cos_val = 1.0
                cos_val = numpy.vdot( target_vector, reference_vector ) / numpy.linalg.norm( target_vector ) * numpy.linalg.norm( reference_vector )
            #        if( cos_val > 1.0 ):
            #          print "cos_val 2: ", cos_val
            #          cos_val = 1.0
            #        try:
            #          if( cos_val == 1.0 ):
            #            theta = 0.0
            #          else:
                theta = math.acos( cos_val )
            #        except ValueError:
            #          print "acos value error"
            #          theta = 0.0
                inner_theta_array.append( theta )
                inner_vector_array.append( numpy.array( [ target_vector , reference_vector ] ) )
                #print inner_vector_array[-1]
            median_index = self.get_median_index( inner_theta_array )
            #      print inner_vector_array[median_index]
            outer_theta_array.append( inner_theta_array[median_index] )
            outer_vector_array.append( inner_vector_array[median_index] )
            inner_theta_array = []
            inner_vector_array = []
        median_index = self.get_median_index( outer_theta_array )
        # theta_final = outer_theta_array[median_index]
        vector_final = outer_vector_array[median_index]
    #    print vector_final
    
        target_shape = numpy.zeros((1,3))
        reference_shape = numpy.zeros((1,3))
        #print vector_final
        target_shape[0]    = vector_final[0]
        reference_shape[0] = vector_final[1]
    
        rotation_matrix = self.get_vector_rotation_matrix( vector_final[1], vector_final[0] )
    
        #rotation_matrix = self.rotation_matrix( reference_shape, target_shape )
        #print reference_shape
        #print target_shape
        #rotated_shape = numpy.transpose( numpy.dot( rotation_matrix, numpy.transpose( target_shape ) ) )
        #print rotated_shape
        #exit
        target_shape = numpy.zeros((nlandmarks,3))
        i = 0
        for lm in ( self.objects[object_index].landmarks ):
            target_shape [i] = ( lm.xcoord, lm.ycoord, lm.zcoord )
            i += 1
    
        reference_shape = numpy.zeros((nlandmarks,3))
        i = 0
        for lm in ( self.reference_shape.landmarks ):
            reference_shape [i] = ( lm.xcoord, lm.ycoord, lm.zcoord )
            i += 1
    
        rotated_shape = numpy.transpose( numpy.dot( rotation_matrix, numpy.transpose( target_shape ) ) )
        
        #print "reference: ", reference_shape[0]
        #print "target: ", target_shape[0], numpy.linalg.norm(target_shape[0])
        #print "rotation: ", rotation_matrix
        #print "rotated: ", rotated_shape[0], numpy.linalg.norm(rotated_shape[0])
        #print "determinant: ", numpy.linalg.det( rotation_matrix )
    
        i = 0
        for lm in ( self.objects[object_index].landmarks ):
            ( lm.xcoord, lm.ycoord, lm.zcoord ) = ( rotated_shape[i,0], rotated_shape[i,1], rotated_shape[i,2] )
            i+=1
        if( object_index == 0 ):
            pass
            #self.reference_shape.print_landmarks("ref:")
            #self.objects[object_index].print_landmarks(str(object_index))
            #print "reference: ", reference_shape[0]
            #print "target: ", target_shape[0], numpy.linalg.norm(target_shape[0])
            #print "rotation: ", rotation_matrix
            #print "rotated: ", rotated_shape[0], numpy.linalg.norm(rotated_shape[0])
            #print "determinant: ", numpy.linalg.det( rotation_matrix )

    def get_vector_rotation_matrix(self, ref, target ):
        ( x, y, z ) = ( 0, 1, 2 )
        #print ref
        #print target
        #print "0 ref", ref
        #print "0 target", target
        
        ref_1 = ref
        ref_1[z] = 0
        cos_val = ref[x] / math.sqrt( ref[x] ** 2 + ref[z] ** 2 )
        theta1 = math.acos( cos_val )
        if( ref[z] < 0 ):
            theta1 = theta1 * -1
        ref = self.rotate_vector_3d( -1 * theta1, ref, 'Y' )
        target = self.rotate_vector_3d( -1 * theta1, target, 'Y' )
        
        #print "1 ref", ref
        #print "1 target", target
        
        cos_val = ref[x] / math.sqrt( ref[x] ** 2 + ref[y] ** 2 )
        theta2 = math.acos( cos_val )
        if( ref[y] < 0 ):
            theta2 = theta2 * -1
        ref = self.rotate_vector_2d( -1 * theta2, ref )
        target = self.rotate_vector_2d( -1 * theta2, target )
        
        #print "2 ref", ref
        #print "2 target", target
        
        cos_val = target[x] / math.sqrt( ( target[x] ** 2 + target[z] ** 2 ) )
        theta1 = math.acos( cos_val )
        if( target[z] < 0 ):
            theta1 = theta1 * -1
        target = self.rotate_vector_3d( -1 * theta1, target, 'Y' )
        
        #print "3 ref", ref
        #print "3 target", target
        
        cos_val = target[x] / math.sqrt( ( target[x] ** 2 + target[y] ** 2 ) )
        theta2 = math.acos( cos_val )
        if( target[y] < 0 ):
            theta2 = theta2 * -1
        target = self.rotate_vector_2d( -1 * theta2, target )
        
        #print "4 ref", ref
        #print "4 target", target
        
        r_mx1 = numpy.array( [ [1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0] ] )
        r_mx2 = numpy.array( [ [1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0] ] )
        #print "shape:", r_mx1.shape
        #print "r_mx1", r_mx1
        #print "theta1", theta1
        #print "cos theta1", math.cos( theta1 )
        #print "sin theta1", math.sin( theta1 )
        #print "r_mx2", r_mx2
        #print "theta2", theta2
        r_mx1[0][0] = math.cos( theta1 )
        r_mx1[0][2] = math.sin( theta1 )
        r_mx1[2][0] = math.sin( theta1 ) * -1
        r_mx1[2][2] = math.cos( theta1 )
        
        #print "r_mx1", r_mx1
        #print "theta1", theta1
        #print "r_mx2", r_mx2
        #print "theta2", theta2
        
        r_mx2[0][0] = math.cos( theta2 )
        r_mx2[0][1] = math.sin( theta2 )
        r_mx2[1][0] = math.sin( theta2 ) * -1
        r_mx2[1][1] = math.cos( theta2 )
        
        #print "r_mx1", r_mx1
        #print "theta1", theta1
        #print "r_mx2", r_mx2
        #print "theta2", theta2
        
        rotation_matrix = numpy.dot( r_mx1, r_mx2 )
        return rotation_matrix
    

    def get_median_index(self, arr ):
        arr.sort()
        len_arr = len( arr )
        if( len_arr == 0 ):
            return -1 
        half_len = int( math.floor( len_arr / 2.0 ) )
        return half_len
#    if( half_len == len_arr ):
#      return  int( ( arr[half_len] + arr[half_len + 1] ) / 2 )
#    else:
#      return arr[half_len]
