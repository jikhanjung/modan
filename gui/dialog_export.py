#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO: Use SQLAlchemy - done 12/18/2014
import math
import wx
from libpy.modan_dbclass import MdDataset, MdDatasetView

CONST = {}

CONST['DIALOG_SIZE'] = wx.Size(640, 500)
CONST['landmarkSeqWidth'] = 50
CONST['landmarkCoordWidth'] = 50

CONST['FILETYPE_TPS'] = 0
CONST['FILETYPE_X1Y1'] = 1
CONST['FILETYPE_MORPHOLOGIKA'] = 2

CONTROL_ID = {}
CONTROL_ID['ID_EXPORT_BUTTON'] = 1001
CONTROL_ID['ID_CANCEL_BUTTON'] = 1002
CONTROL_ID['ID_MOVELEFT_BUTTON'] = 1003
CONTROL_ID['ID_MOVERIGHT_BUTTON'] = 1004
CONTROL_ID['ID_FTYPE_COMBO'] = 1005
CONTROL_ID['ID_CSIZE_CHECKBOX'] = 1006
CONTROL_ID['ID_FOPTION_COMBO'] = 1007

EXPORT_OPTION = ( 'Bookstein Registration', 'Sliding Baseline', 'Procrustes (GLS)', 'RFTRA', 'Traditional Length')
CONST['IDX_BOOKSTEIN'] = 0
CONST['IDX_SBR'] = 1
CONST['IDX_GLS'] = 2
CONST['IDX_RFTRA'] = 3
CONST['IDX_TRADLEN'] = 4
CONST['IDX_DEFAULT'] = CONST['IDX_BOOKSTEIN']
FILETYPE_LIST = ['TPS', 'X1Y1CS', 'Morphologika2']


class ModanExportDialog(wx.Dialog):
    dataset = None

    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, 'Export Data', size=CONST['DIALOG_SIZE'])
        panel = wx.Panel(self, -1)
        self.forms = dict()
        self.mos = []

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        objectLabel1 = wx.StaticText(panel, -1, 'Object List', style=wx.ALIGN_CENTER)
        objectLabel2 = wx.StaticText(panel, -1, 'Export List', style=wx.ALIGN_CENTER)
        objectList = wx.ListBox(panel, -1, choices=(), size=(150, 200), style=wx.LB_EXTENDED)
        exportList = wx.ListBox(panel, -1, choices=(), size=(150, 200), style=wx.LB_EXTENDED)
        landmarkList = wx.ListCtrl(panel, -1, style=wx.LC_REPORT)
        landmarkList.InsertColumn(0, 'Seq', width=CONST['landmarkSeqWidth'])
        landmarkList.InsertColumn(1, 'X', width=CONST['landmarkCoordWidth'])
        landmarkList.InsertColumn(2, 'Y', width=CONST['landmarkCoordWidth'])
        landmarkList.InsertColumn(3, 'Z', width=CONST['landmarkCoordWidth'])
        moveLeftButton = wx.Button(panel, CONTROL_ID['ID_MOVELEFT_BUTTON'], '<', size=(30, 30))
        moveRightButton = wx.Button(panel, CONTROL_ID['ID_MOVERIGHT_BUTTON'], '>', size=(30, 30))
        self.Bind(wx.EVT_BUTTON, self.OnMoveLeft, id=CONTROL_ID['ID_MOVELEFT_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnMoveRight, id=CONTROL_ID['ID_MOVERIGHT_BUTTON'])
        landmarkList.SetMinSize((200, 200))

        self.list1 = objectList
        self.list2 = exportList

        objectSizer_btn = wx.BoxSizer(wx.VERTICAL)
        objectSizer_btn.Add(moveLeftButton, wx.EXPAND)
        objectSizer_btn.Add(moveRightButton, wx.EXPAND)

        objectSizer = wx.FlexGridSizer(2, 3, 0, 0)
        objectSizer.AddGrowableCol(0)
        objectSizer.AddGrowableCol(2)
        objectSizer.AddGrowableRow(1)

        objectSizer.Add(objectLabel1, wx.EXPAND)
        objectSizer.Add((10, 10), wx.EXPAND)
        objectSizer.Add(objectLabel2, wx.EXPAND)
        objectSizer.Add(objectList, wx.EXPAND)
        objectSizer.Add(objectSizer_btn, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        objectSizer.Add(exportList, wx.EXPAND)

        # testButton = wx.Button( panel, -1, 'Test' )
        objectSizerAll = wx.FlexGridSizer(rows=3, cols=1)
        objectSizerAll.AddGrowableRow(0)
        objectSizerAll.AddGrowableRow(2)
        objectSizerAll.Add(objectSizer, wx.EXPAND)
        objectSizerAll.Add((10, 10), wx.EXPAND)
        objectSizerAll.Add(landmarkList, flag=wx.EXPAND)

        ftypeLabel = wx.StaticText(panel, -1, 'File Type', style=wx.ALIGN_RIGHT)
        foptionLabel = wx.StaticText(panel, -1, 'Option', style=wx.ALIGN_RIGHT)
        ftypeCombo = wx.ComboBox(panel, CONTROL_ID['ID_FTYPE_COMBO'], "TPS", (15, 30), wx.DefaultSize, FILETYPE_LIST, wx.CB_DROPDOWN)
        foptionCombo = wx.ComboBox(panel, CONTROL_ID['ID_FOPTION_COMBO'], EXPORT_OPTION[CONST['IDX_DEFAULT']], (15, 30), wx.DefaultSize,
                                   EXPORT_OPTION, wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.OnFtypeChange, id=CONTROL_ID['ID_FTYPE_COMBO'])
        self.Bind(wx.EVT_COMBOBOX, self.OnFoptionChange, id=CONTROL_ID['ID_FOPTION_COMBO'])
        exportButton = wx.Button(panel, CONTROL_ID['ID_EXPORT_BUTTON'], 'Export')
        self.Bind(wx.EVT_BUTTON, self.OnExport, id=CONTROL_ID['ID_EXPORT_BUTTON'])
        cancelButton = wx.Button(panel, CONTROL_ID['ID_CANCEL_BUTTON'], 'Cancel')
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=CONTROL_ID['ID_CANCEL_BUTTON'])
        self.ftypeCombo = ftypeCombo
        self.foptionCombo = foptionCombo
        self.ftypeLabel = ftypeLabel
        self.foptionLabel = foptionLabel
        #self.csizeLabel = wx.StaticText( panel, ID_CSIZE_LABEL, 'Include csize', style=wx.ALIGN_RIGHT )
        self.datasetCheckbox = wx.CheckBox(panel, CONTROL_ID['ID_CSIZE_CHECKBOX'], 'Include dataset name', style=wx.ALIGN_RIGHT)
        self.datasetCheckbox.SetValue(True)
        self.objnameCheckbox = wx.CheckBox(panel, CONTROL_ID['ID_CSIZE_CHECKBOX'], 'Include object name', style=wx.ALIGN_RIGHT)
        self.objnameCheckbox.SetValue(True)
        self.groupInfoCheckbox = wx.CheckBox(panel, CONTROL_ID['ID_CSIZE_CHECKBOX'], 'Include group information',
                                             style=wx.ALIGN_RIGHT)
        self.groupInfoCheckbox.SetValue(True)
        self.csizeCheckbox = wx.CheckBox(panel, CONTROL_ID['ID_CSIZE_CHECKBOX'], 'Include centroid size', style=wx.ALIGN_RIGHT)
        self.csizeCheckbox.SetValue(True)
        self.headerCheckbox = wx.CheckBox(panel, CONTROL_ID['ID_CSIZE_CHECKBOX'], 'Include column header', style=wx.ALIGN_RIGHT)
        self.headerCheckbox.SetValue(True)
        # baseline
        self.baselineLabel = wx.StaticText(panel, -1, 'Baseline', style=wx.ALIGN_RIGHT)
        self.forms['baseline'] = wx.TextCtrl(panel, -1, '')
        # wireframe
        self.wireframeLabel = wx.StaticText(panel, -1, 'Wireframe', style=wx.ALIGN_RIGHT)
        self.forms['wireframe'] = wx.TextCtrl(panel, -1, '')

        booksteinSizer = wx.BoxSizer()
        booksteinSizer.Add(self.baselineLabel, wx.EXPAND)
        booksteinSizer.Add(self.forms['baseline'], wx.EXPAND)
        tradlenSizer = wx.BoxSizer()
        tradlenSizer.Add(self.wireframeLabel, wx.EXPAND)
        tradlenSizer.Add(self.forms['wireframe'], wx.EXPAND)

        optionSizer = wx.FlexGridSizer(2, 1, 0, 0)
        optionSizer.AddGrowableRow(0)
        optionSizer.AddGrowableRow(1)
        fileSizer = wx.FlexGridSizer(3, 3, 0, 0)
        fileSizer.Add(ftypeLabel, flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add(ftypeCombo, flag=wx.EXPAND | wx.ALIGN_CENTER)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add(foptionLabel, flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add(foptionCombo, flag=wx.EXPAND | wx.ALIGN_CENTER)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add(self.datasetCheckbox, flag=wx.EXPAND | wx.ALIGN_LEFT)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add(self.objnameCheckbox, flag=wx.EXPAND | wx.ALIGN_LEFT)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add(self.groupInfoCheckbox, flag=wx.EXPAND | wx.ALIGN_LEFT)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add(self.csizeCheckbox, flag=wx.EXPAND | wx.ALIGN_LEFT)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add(self.headerCheckbox, flag=wx.EXPAND | wx.ALIGN_LEFT)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add(booksteinSizer, flag=wx.EXPAND | wx.ALIGN_LEFT)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add((10, 10), flag=wx.EXPAND)
        fileSizer.Add(tradlenSizer, flag=wx.EXPAND | wx.ALIGN_LEFT)
        #optionSizer.Add( ftypeLabel, wx.EXPAND )
        #optionSizer.Add( ftypeCombo, wx.EXPAND )
        #optionSizer.Add( foptionLabel, wx.EXPAND )
        #optionSizer.Add( foptionCombo, wx.EXPAND )
        optButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        optButtonSizer.Add(exportButton, flag=wx.ALIGN_CENTER)
        optButtonSizer.Add(cancelButton, flag=wx.ALIGN_CENTER)
        optionSizer.Add(fileSizer, flag=wx.ALIGN_CENTER)
        optionSizer.Add(optButtonSizer, flag=wx.ALIGN_CENTER)

        mainSizer.Add((10, 10))
        mainSizer.Add(objectSizerAll, flag=wx.EXPAND)
        mainSizer.Add((10, 10))
        mainSizer.Add(optionSizer, flag=wx.EXPAND)
        mainSizer.Add((10, 10))

        panel.SetSizer(mainSizer)
        panel.Fit()

        evt = wx.PyEvent(-1)
        self.OnFtypeChange(evt)
        #print self.dataset
        if self.dataset != None:
            self.forms['baseline'].SetValue(self.dataset.baseline)
            self.forms['wireframe'].SetValue(self.dataset.wireframe)

    def SetDataset(self, ds):
        self.dataset = ds
        #print self.dataset.baseline
        self.forms['baseline'].SetValue(ds.baseline)
        self.forms['wireframe'].SetValue(self.dataset.wireframe)
        return

    def OnExport(self, evt):
        wildcard = ''
        if ( self.filetype == CONST['FILETYPE_TPS']):
            wildcard = "TPS file (*.tps)|*.tps|" \
                       "TPS file (*.txt)|*.txt|" \
                       "All files (*.*)|*.*"
        elif ( self.filetype == CONST['FILETYPE_X1Y1']):
            wildcard = "X1Y1 file (*.x1y1)|*.x1y1|" \
                       "X1Y1 file (*.txt)|*.txt|" \
                       "All files (*.*)|*.*"
        elif ( self.filetype == CONST['FILETYPE_MORPHOLOGIKA']):
            wildcard = "Morphologika2 file (*.txt)|*.txt|" \
                       "All files (*.*)|*.*"

        fileDialog = wx.FileDialog(self, "Choose a file", "",
                                   "", wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)
        if fileDialog.ShowModal() == wx.ID_OK:
            filename = fileDialog.GetPath()
            fileDialog.Destroy()
        else:
            fileDialog.Destroy()
            return

        wx.BeginBusyCursor()
        baseline = []
        for c in self.forms['baseline'].GetValue().split(','):
            if c != '':
                baseline.append(int(c))

        dimension = self.dataset.dimension

        # collect objects
        ds = MdDatasetView(self.dataset)
        ds.object_list = []
        for i in xrange(self.list2.GetCount()):
            mo = self.list2.GetClientData(i)
            ds.object_list.append(mo)

        # align objects
        foption = self.foptionCombo.GetValue()
        #print "foption:", foption
        #print EXPORT_OPTION
        if ( self.filetype == CONST['FILETYPE_X1Y1']):
            if ( foption == EXPORT_OPTION[CONST['IDX_GLS']] ):
                ds.procrustes_superimposition()
            elif ( foption == EXPORT_OPTION[CONST['IDX_BOOKSTEIN']] ):
                #print "bookstein"
                for mo in ds.object_list:
                    #mo.print_landmarks()
                    mo.bookstein_registration(baseline)
            elif ( foption == EXPORT_OPTION[CONST['IDX_SBR']]):
                for mo in ds.object_list:
                    mo.sliding_baseline_registration(baseline)
            elif ( foption == EXPORT_OPTION[CONST['IDX_RFTRA']] ):
                wx.BeginBusyCursor()
                ds.resistant_fit_superimposition()
                wx.EndBusyCursor()

        result_str = ''
        separator = "\t"
        ''' different newline for different OS '''
        newline = "\n"

        ''' print data into file '''

        ''' header row '''
        if self.filetype == CONST['FILETYPE_X1Y1']:
            if self.headerCheckbox.GetValue():
                if self.datasetCheckbox.GetValue():
                    result_str += "datasetName" + separator
                if self.objnameCheckbox.GetValue():
                    result_str += "objectName" + separator
                if self.groupInfoCheckbox.GetValue():
                    for pn in self.dataset.propertyname_list:
                        result_str += pn.propertyname + separator
                if foption == EXPORT_OPTION[CONST['IDX_TRADLEN']]:
                    self.dataset.unpack_wireframe()
                    for edge in self.dataset.edge_list:
                        result_str += "d" + str(edge[0]) + "_" + str(edge[1])
                        result_str += separator
                else:
                    mo = ds.object_list[0]
                    l_idx = 0
                    for lm in mo.landmark_list:
                        l_idx += 1
                        result_str += "x" + str(l_idx) + separator + "y" + str(l_idx)
                        if dimension == 3:
                            result_str += separator + "z" + str(l_idx)
                        result_str += separator
                if ( self.csizeCheckbox.GetValue() ):
                    result_str += "csize"
                result_str += newline
        elif self.filetype == CONST['FILETYPE_MORPHOLOGIKA']:
            result_str += "[individuals]" + newline + str(len(ds.object_list)) + newline
            result_str += "[landmarks]" + newline + str(len(ds.object_list[0].landmark_list)) + newline
            result_str += "[Dimensions]" + newline + str(dimension) + newline
            label_values = "[labels]" + newline + separator.join( [ pn.propertyname for pn in self.dataset.propertyname_list ]) + newline
            label_values += "[labelvalues]" + newline

        ''' actual data '''
        #rawpoint_values = ''
        rawpoint_values = "[rawpoints]" + newline
        name_values = "[names]" + newline
        for mo in ds.object_list:
            if ( self.filetype == CONST['FILETYPE_TPS'] ):
                result_str += "lm=" + str(len(mo.landmark_list)) + separator + str(mo.objname) + newline
                mo.trim_decimal()
                for lm in mo.landmark_list:
                    result_str += separator.join([str(c) for c in lm.coords])
                    result_str += newline
            elif self.filetype == CONST['FILETYPE_X1Y1']:
                #print "x1y1"
                mo.trim_decimal()
                if ( self.datasetCheckbox.GetValue() ):
                    result_str += str(mo.dataset.dsname) + separator
                if ( self.objnameCheckbox.GetValue() ):
                    result_str += str(mo.objname) + separator
                if ( self.groupInfoCheckbox.GetValue() ):
                    for i in range(len(self.dataset.propertyname_list)):
                        result_str += str(mo.property_list[i].property) + separator

                if ( foption == EXPORT_OPTION[CONST['IDX_TRADLEN']] ):
                    for edge in self.dataset.edge_list:
                        from_edge, to_edge = edge
                        #print from_edge, to_edge
                        dist = self.get_distance(mo.landmark_list[from_edge - 1].coords, mo.landmark_list[to_edge - 1].coords)
                        result_str += str(dist) + separator
                else:
                    for lm in mo.landmark_list:
                        result_str += separator.join(lm.coords)
                        result_str += separator

                if ( self.csizeCheckbox.GetValue() ):
                    result_str += str(mo.get_centroid_size())
                result_str += newline
            elif self.filetype == CONST['FILETYPE_MORPHOLOGIKA']:
                label_values += separator.join([p.property for p in mo.property_list ]).strip() + newline
                name_values += mo.objname + newline
                #print mo.objname
                rawpoint_values += "'#" + mo.objname + newline
                for lm in mo.landmark_list:
                    rawpoint_values += separator.join([str(c) for c in lm.coords])
                    rawpoint_values += newline

        if self.filetype == CONST['FILETYPE_MORPHOLOGIKA']:
            #print name_values
            result_str += name_values + label_values + rawpoint_values
            result_str += "[wireframe]" + newline
            self.dataset.unpack_wireframe()
            for edge in self.dataset.edge_list:
                #print edge
                result_str += separator.join([str(v) for v in edge]) + newline
            result_str += "[polygons]" + newline
            self.dataset.unpack_polygons()
            for polygon in self.dataset.polygon_list:
                #print edge
                result_str += separator.join([str(v) for v in polygon]) + newline

        fh = file(filename, 'w')
        fh.write(result_str)
        fh.close()

        wx.EndBusyCursor()
        self.Close()

    #    return 1
    def get_distance(self, coords1, coords2):
        if len(coords1) != len(coords2):
            return -1
        sqsum = 0
        for i in range( len(coords1)):
            sqsum += ( coords1[i] - coords2[i] ) ** 2
        dist = math.sqrt(sqsum)
        return dist

    def OnClose(self, evt):
        self.Close()

    def OnMoveRight(self, evt):
        self.MoveItemsBetweenListBox(self.list1, self.list2)

    def OnMoveLeft(self, evt):
        self.MoveItemsBetweenListBox(self.list2, self.list1)

    def OnFoptionChange(self, evt):
        foption = self.foptionCombo.GetValue()
        self.baselineLabel.Hide()
        self.forms['baseline'].Hide()
        self.wireframeLabel.Hide()
        self.forms['wireframe'].Hide()
        if self.filetype == CONST['FILETYPE_X1Y1']:
            if ( foption == EXPORT_OPTION[CONST['IDX_SBR']] or foption == EXPORT_OPTION[CONST['IDX_BOOKSTEIN']] ):
                self.baselineLabel.Show()
                self.forms['baseline'].Show()
            elif ( foption == EXPORT_OPTION[CONST['IDX_TRADLEN']] ):
                self.wireframeLabel.Show()
                self.forms['wireframe'].Show()

    def OnFtypeChange(self, evt):
        ftype = self.ftypeCombo.GetValue()
        if ( ftype == FILETYPE_LIST[CONST['FILETYPE_TPS']] ):
            self.filetype = CONST['FILETYPE_TPS']
            #print 'yes tps'
            self.foptionCombo.Hide()
            self.foptionLabel.Hide()
            self.csizeCheckbox.Hide()
            self.objnameCheckbox.Hide()
            self.groupInfoCheckbox.Hide()
            self.datasetCheckbox.Hide()
            self.headerCheckbox.Hide()
            self.baselineLabel.Hide()
            self.forms['baseline'].Hide()
        elif ( ftype == FILETYPE_LIST[CONST['FILETYPE_MORPHOLOGIKA']]):
            self.filetype = CONST['FILETYPE_MORPHOLOGIKA']
            #print 'yes tps'
            self.foptionCombo.Hide()
            self.foptionLabel.Hide()
            self.csizeCheckbox.Hide()
            self.objnameCheckbox.Hide()
            self.groupInfoCheckbox.Hide()
            self.datasetCheckbox.Hide()
            self.headerCheckbox.Hide()
            self.baselineLabel.Hide()
            self.forms['baseline'].Hide()
        else:
            self.filetype = CONST['FILETYPE_X1Y1']
            #print 'not tps'
            self.foptionCombo.Show()
            self.foptionLabel.Show()
            self.csizeCheckbox.Show()
            self.objnameCheckbox.Show()
            self.groupInfoCheckbox.Show()
            self.headerCheckbox.Show()
            self.datasetCheckbox.Show()
            self.baselineLabel.Hide()
            self.forms['baseline'].Hide()
        self.OnFoptionChange(None)

    def MoveItemsBetweenListBox(self, lb_from, lb_to):
        j = 0
        for i in xrange(lb_from.GetCount()):
            if lb_from.IsSelected(j):
                mo = lb_from.GetClientData(j)
                lb_from.Delete(j)
                lb_to.Append(mo.objname, mo)
            else:
                j = j + 1

    def SetObjectList(self, objList):
        self.objList = objList
        #for mo in objList:
        self.list1.Clear()
        #self.SetSort(lambda x, y: cmp(x.id, y.id)) # default sorting

        for mo in self.objList:
            #print mo.objname
            self.list1.Append(mo.objname, mo)
            #self.colsort = [0, 0, 0] # 0=ascending ready, 1=descending ready

    def SetExportList(self, objList):
        self.objList = objList
        #for mo in objList:
        self.list2.Clear()
        #self.SetSort(lambda x, y: cmp(x.id, y.id)) # default sorting

        for mo in self.objList:
            #print mo.objname
            self.list2.Append(mo.objname, mo)
            #self.colsort = [0, 0, 0] # 0=ascending ready, 1=descending ready
