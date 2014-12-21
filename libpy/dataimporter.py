#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import xlrd

from libpy.modan_dbclass import MdObject, MdDataset, MdLandmark, MdPropertyName, MdProperty

ID_TAB_DELIMITED = 1
ID_ABERLINK = 2

FILETYPE_TPS = 0
FILETYPE_X1Y1 = 1
FILETYPE_MORPHOLOGIKA = 2
FILETYPE_EXCEL = 3
FILETYPE_LIST = ['TPS', 'X1Y1CS', 'Morphologika', 'EXCEL']
NEWLINE = "\n"
DEFAULT_DIMENSION = 2


class ModanDataImporter:
    def __init__(self, parent, type='', text='', list=[]):
        self.type = type
        self.parent = parent
        self.error_message = ''
        self.dimension = -1
        if text <> '':
            self.set_grid_from_text(text)
        elif len(list) > 0:
            self.set_grid_from_list(list)

    def set_grid_from_list(self, list=[]):
        self.grid = list
        self.linenum = len(list)

    def set_grid_from_text(self, text=''):
        self.orig_text = text.rstrip().replace('\r\n', '\n').replace('\r', '\n')
        self.title = ''
        self.lines = self.orig_text.split('\n')
        self.linenum = len(self.lines)
        self.grid = []
        for i in xrange(self.linenum):
            self.grid.append(self.lines[i].split('\t'))

    def openTpsFile(self, filepath):
        f = open(filepath, 'r')
        tpsdata = f.read()
        f.close()

        object_count = 0
        landmark_count = 0
        data = []
        threed = 0
        twod = 0
        objects = {}
        header = ''
        comment = ''
        image_count = 0
        tps_lines = [l.strip() for l in tpsdata.split(NEWLINE)]
        found = False
        for line in tps_lines:
            line = line.strip()
            if line == '':
                continue
            headerline = re.search('^(\w+)(\s*)=(\s*)(\d+)(.*)', line)
            if headerline == None:
                if header == 'lm':
                    point = re.split('\s+', line)
                    if len(point) > 2 and self.isNumber(point[2]):
                        threed += 1
                    else:
                        twod += 1

                    if len(point)>1:
                        data.append(point)
                continue
            elif headerline.group(1).lower() == "lm":
                if len(data) > 0:
                    if comment != '':
                        key = comment
                    else:
                        key = self.dataset_name + "_" + str(object_count + 1)
                    objects[key] = data
                    data = []
                header = 'lm'
                object_count += 1
                landmark_count, comment = int(headerline.group(4)), headerline.group(5).strip()
                # landmark_count_list.append( landmark_count )
                # if not found:
                #found = True
            elif headerline.group(1).lower() == "image":
                image_count += 1

        if len(data) > 0:
            if comment != '':
                key = comment
            else:
                key = self.dataset_name + "_" + str(object_count + 1)
            objects[key] = data
            data = []

        if object_count == 0 and landmark_count == 0:
            return False
        if threed > twod:
            self.dimension = 3
        else:
            self.dimension = 2

        self.object_count = object_count
        self.landmark_count = landmark_count
        self.data = objects

        return True

    def openExcelFile(self, filepath):
        ''' okay.. MS Excel file '''
        book = xlrd.open_workbook(filepath)
        object_count = 0
        sheet_list = book.sheets()
        data_list = []
        if len(sheet_list) == 1 or \
                                        len(sheet_list) == 3 and ( sheet_list[1].nrows == 0 ) and (
                            sheet_list[2].nrows == 0 ):
            ''' all the objects are in a single sheet '''
            object_count = -1
            row_list = []
            sheet = sheet_list[0]
            for r in range(sheet.nrows):
                row = sheet.row_values(r)
                data_list.append(row)
        else:
            for sheet in sheet_list:
                if sheet.nrows > 0 and sheet.name[0] != '#':
                    object_count = object_count + 1
                    data_list.append(sheet)
                    # data_list = sheet_list
        self.object_count = object_count
        self.landmark_count = -1
        self.data = data_list
        return True

    def openTextFile(self, filepath):
        f = open(filepath, 'r')
        data = f.read()
        f.close()

        return False

    def openMorphologikaFile(self, filepath):
        f = open(filepath, 'r')
        morphologika_data = f.read()
        f.close()

        object_count = -1
        landmark_count = -1
        data_lines = [l.strip() for l in morphologika_data.split(NEWLINE)]
        found = False
        dsl = ''
        dimension = DEFAULT_DIMENSION
        data = {}
        for line in data_lines:
            line = line.strip()
            if line == "":
                continue
            if line[0] == "'":
                '''comment'''
                continue
            elif line[0] == '[':
                dsl = re.search('(\w+)', line).group(0).lower()
                data[dsl] = []
                continue
            else:
                data[dsl].append(line)
                if dsl == 'individuals':
                    object_count = int(line)
                if dsl == 'landmarks':
                    landmark_count = int(line)
                if dsl == 'dimensions':
                    dimension = int(line)

        if object_count < 0 or landmark_count < 0:
            return False

        self.object_count = object_count
        self.landmark_count = landmark_count
        self.dimension = dimension
        self.data = data
        return True

    def checkFileType(self, filepath, filetype=FILETYPE_TPS):
        ( pathname, filename ) = os.path.split(filepath)
        ( filename, fileext ) = os.path.splitext(filename)
        fileext = fileext.lower()
        self.dataset_name = filename

        success = False

        ''' file type specified when opening '''
        if filetype == FILETYPE_EXCEL:
            success = self.openExcelFile(filepath)
            self.filetype = filetype
        elif filetype == FILETYPE_TPS:
            success = self.openTpsFile(filepath)
            self.filetype = filetype
        elif filetype == FILETYPE_MORPHOLOGIKA:
            success = self.openMorphologikaFile(filepath)
            self.filetype = filetype

        ''' second chance! file type not specified '''
        if ( not success ):
            print "not success"
            if fileext == '.tps':
                print "try tps"
                success = self.openTpsFile(filepath)
                if success:
                    self.filetype = FILETYPE_TPS
                return success
            elif fileext == '.xls':
                success = self.openExcelFile(filepath)
                if success:
                    self.filetype = FILETYPE_EXCEL
            else:  # if fileext == '.txt':
                print "try morphologika"
                ''' try morphologika first '''
                success = self.openMorphologikaFile(filepath)
                if success:
                    self.filetype = FILETYPE_MORPHOLOGIKA
                else:
                    print "try tps"
                    ''' and then tps'''
                    success = self.openTpsFile(filepath)
                    if success:
                        self.filetype = FILETYPE_TPS
                    else:
                        ''' add text file open later'''
                        pass
        return success

    def ImportDataset(self, session, dimension=3):
        ''' don't forget to implement transaction for this method '''

        ''' first, insert the dataset '''
        if self.dimension < 0:
            self.dimension = dimension

        ds = MdDataset()
        ds.dsname = self.dataset_name
        ds.dimension = self.dimension

        dsname = newname = self.dataset_name
        i = 1
        len( session.query(MdDataset).filter(MdDataset.dsname==newname).all() ) > 0
        while len( session.query(MdDataset).filter(MdDataset.dsname==newname).all() ) > 0:
            newname = dsname + " (" + str(i) + ")"
            i += 1
        ds.dsname = newname
        session.add(ds)

        ''' and then objects and landmarks '''
        if self.filetype == FILETYPE_TPS:
            self.importTpsFile(ds,session)
        elif self.filetype == FILETYPE_MORPHOLOGIKA:
            self.importMorphologikaFile(ds,session)
        elif self.filetype == FILETYPE_EXCEL:
            self.importExcelFile(ds,session)
            # elif self.filetype == FILETYPE_TEXT:
            # pass
        return

    def importMorphologikaFile(self, dataset, session):
        i = 0
        # abc
        for name in self.data['names']:
            obj = MdObject()
            obj.objname = name
            obj.landmark_list = []
            j = 1
            begin = i * self.landmark_count
            count = self.landmark_count
            # print begin, begin + count
            for point in self.data['rawpoints'][begin:begin + count]:
                #print point
                coords = re.split('\s+', point)
                obj.landmark_list.append(MdLandmark(coords))
                obj.pack_landmark()
                j += 1
            dataset.object_list.append(obj)
            i += 1

        group_info = []
        group_number = []
        edge_list = []
        polygon_list = []
        propertyname_list = []
        property_list_list = []

        if 'labels' in self.data.keys():
            for line in self.data['labels']:
                labels = re.split('\s+', line)
                for label in labels:
                    propertyname_list.append( label )
                    dataset.propertyname_list.append(MdPropertyName(label))

        # flush session to get dataset id and mdpropertyname ids
        session.flush()

        if 'labelvalues' in self.data.keys():
            for line in self.data['labelvalues']:
                property_list = re.split('\s+', line)
                property_list_list.append(property_list)

        if 'wireframe' in self.data.keys():
            for line in self.data['wireframe']:
                edge = [int(v) for v in re.split('\s+', line)]
                edge.sort()
                edge_list.append(edge)

        if 'polygons' in self.data.keys():
            for line in self.data['polygons']:
                poly = [int(v) for v in re.split('\s+', line)]
                poly.sort()
                polygon_list.append(poly)

        '''a
        print "n o o", self.object_count
        print "n o lm", self.landmark_count
        print "dim", dataset.dimension
        print "groups", group_info, group_number
        #print "names", object_name
        #print "groupname_list", groupname_list
        #print "groupinfo_list", groupinfo_list
        #print "object_list", raw_object_list
        print "wireframe", edge_list
        print "polygons", polygon_list
        a'''

        ''' Error checking and warning '''
        if len(dataset.object_list) == 0:
            print "no objects!"
        if len(dataset.object_list) != self.object_count:
            print 'number of objects does not match!! %d objects expected, but %d objects found' % (
                self.object_count, len(dataset.object_list) )

        i = 0
        for obj in dataset.object_list:
            for j in range(len(property_list_list[i])):
                mdprop = MdProperty(property_list_list[i][j])
                mdprop.object_id = obj.id
                mdprop.propertyname_id = dataset.propertyname_list[j].id
                obj.property_list.append(mdprop)
            obj.dataset_id = dataset.id
            #print object.id
            i += 1
            #percentage = ( float( processed_object ) / float ( self.objectcount) ) * 100
            percentage = ( float(i) / float(self.object_count) ) * 100
            self.parent.SetProgress(int(percentage))
        #print group_info
        edge_list.sort()
        dataset.edge_list = edge_list
        dataset.pack_wireframe()
        polygon_list.sort()
        dataset.polygon_list = polygon_list
        dataset.pack_polygons()
        return

    def importTpsFile(self, dataset, session):
        for name in self.data.keys():
            obj = MdObject()
            obj.objname = name
            obj.landmark_list = []
            for point in self.data[name]:
                coords = point
                # print point
                if len(coords)>0:
                    lm = MdLandmark(coords)
                    obj.landmark_list.append(lm)
                    obj.pack_landmark()
            dataset.object_list.append( obj )

    def checkExcelSheet(self, sheet):
        new_objects = []
        for row in sheet.rows:
            pass
        return new_objects

    def ExcelSheetToMdObject(self, sheet, dataset):
        sheetdata = []
        for r in range(sheet.nrows):
            sheetdata.append(sheet.row_values(r))
        self.set_grid_from_list(sheetdata)
        self.checkDataType()
        mo = MdObject()
        mo.objname = sheet.name
        mo.objdesc = ''
        mo.landmark_list = []
        for lm in self.grid:
            mo.landmark_list.append(MdLandmark(lm))
        dataset.object_list.append(mo)
        return

    def importExcelFile(self, dataset, session):
        # TODO : test Excel file import
        for sheet in self.data:
            self.ExcelSheetToMdObject(sheet, dataset)
            # for obj in converted_objects:
            # objects.append( obj )

    def checkDataType(self):
        row_to_check = 5
        min_colnum = 2

        if ( self.linenum > row_to_check ):
            row_to_check = row_to_check
        else:
            row_to_check = self.linenum
        print "row to check", row_to_check
        print "linenum", self.linenum
        threshold = row_to_check * 0.8

        if ( row_to_check > 2 ):
            mode_point = 0
            # dim_point = 0
            # prev_colnum = 0
            max_colnum = 10
            colnum = 0
            cols = []
            colIsNumber = []
            #mode = ''
            coord_begin = 0
            coord_end = 0
            aberlink_point = 0

            # Check location of the numbers
            for j in xrange(max_colnum):
                colIsNumber.append(0)
            for i in xrange(row_to_check):
                firstcol = unicode(self.grid[i][0])
                if ( firstcol == u'R' or firstcol == 'F' or firstcol == 'P' ):
                    aberlink_point += 1
                colnum = len(self.grid[i])
                if ( colnum > min_colnum ):
                    mode_point += 1
                if ( colnum > max_colnum ):
                    colnum = max_colnum
                for j in xrange(colnum):
                    #print "i:"+str(i)
                    #print "j:"+str(j)
                    #print self.grid[i][j]
                    if ( self.grid[i][j] != '' and self.isNumber(self.grid[i][j]) ):
                        colIsNumber[j] += 1
            if ( mode_point >= threshold ):
                mode = ID_TAB_DELIMITED
            if ( aberlink_point >= threshold ):
                mode = ID_ABERLINK
            else:
                mode = ID_TAB_DELIMITED
            for i in xrange(colnum - 1):
                if ( colIsNumber[i] < threshold and colIsNumber[i + 1] >= threshold ):
                    coord_begin = i + 1
                if ( colIsNumber[i + 1] >= threshold ):
                    coord_end = i + 1
                    # set 3 as maximum column numbers
            if ( coord_end - coord_begin > 2 ):
                coord_end = coord_begin + 2
            datacol_count = coord_end - coord_begin + 1
            print "begin:[%d]" % coord_begin
            print "end:[%d]" % coord_end
            if (coord_begin > 0 ):
                self.title = self.grid[0][0]

            # check if from Aberlink
            # if from aberlink, strip first and last row
            print self.grid[0][0], self.grid[1][0], self.grid[2][0]
            if ( unicode(self.grid[0][0]) == u'R' and
                     ( unicode(self.grid[1][0]) == u'R' or unicode(self.grid[1][0]) == u'F' ) and
                         unicode(self.grid[2][0]) == u'P' ):
                print "delete first row"
                del self.grid[0]
            last_row = len(self.grid) - 1
            #print self.grid[last_row]
            if ( ( unicode(self.grid[last_row - 2][0]) == u'R' or unicode(self.grid[last_row - 2][0]) == u'F' ) and
                         unicode(self.grid[last_row - 1][0]) == u'P' and
                         unicode(self.grid[last_row][0]) == u'R' ):  #and
                #float( self.grid[last_row][1] ) == 0.0 and
                #float( self.grid[last_row][2] ) == 0.0 and
                #float( self.grid[last_row][3] ) == 0.0 ):
                #print 'last row del'
                del self.grid[len(self.grid) - 1]
                print "delete last row"

                #print len( self.grid )
            max_row = len(self.grid)
            #half_max_row = int( max_row / 2 )
            #print max_row
            #print half_max_row
            if ( mode == ID_ABERLINK ):
                for i in xrange(max_row / 2):
                    #print i
                    j = max_row - 2 * i
                    #print j
                    del self.grid[max_row - 2 * i - 1]

        for cols in ( self.grid ):
            for i in xrange(datacol_count):
                cols[i] = cols[coord_begin + i]
            cols[i + 1:len(cols)] = []
            # pass
            # print self.title
            #print self.grid

    def isNumber(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False


# text = "this is title\t1\t1\t1\n"
# text += "\t1\t1\t2\n"
#text += "\t1\t1\t3\n"
#text += "\t1\t1\t4\n"
#text += "\t2\t3\t4\n"
#text += "\t22\t33\t44"
#di = ModanDataImporter(text=text)
#di.checkDataType()
