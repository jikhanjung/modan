#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math

from wx.lib.plot import *
import numpy

from gui.md_3d_canvas import Md3DCanvas
from libpy.modan_dbclass import MdDatasetView
from libpy.mdstatistics import MdPrincipalComponent2
from libpy.mdstatistics import MdCanonicalVariate
from libpy.mdstatistics import MdManova
from libpy.modan_exception import MdException
use_mplot = False

CONST = {}
CONST['DIALOG_SIZE'] = wx.Size(1024, 768)
CONST['IDX_BOOKSTEIN'] = 0
CONST['IDX_SBR'] = 1
CONST['IDX_GLS'] = 2
CONST['IDX_RFTRA'] = 3

CONTROL_ID = {}
CONTROL_ID['ID_CHK_AUTO_ROTATE'] = 2021
CONTROL_ID['ID_CHK_SHOW_INDEX'] = 2022
CONTROL_ID['ID_CHK_SHOW_WIREFRAME'] = 2023
CONTROL_ID['ID_CHK_SHOW_MEANSHAPE'] = 2024
CONTROL_ID['ID_EIGENVALUE_LISTCTRL'] = 2025
CONTROL_ID['ID_LOADING_LISTCTRL'] = 2026
CONTROL_ID['ID_RAWDATA_LISTCTRL'] = 2027
CONTROL_ID['ID_SUPERIMPOSED_LISTCTRL'] = 2028
CONTROL_ID['ID_FINALCOORDINATES_LISTCTRL'] = 2029

CONTROL_ID['ID_RADIO_SUPERIMPOSITION'] = 2031
CONTROL_ID['ID_OBJECT_LISTCTRL'] = 2032
CONTROL_ID['ID_ANALYZE_BUTTON'] = 2033

CONTROL_ID['ID_XAXIS_COMBO'] = 2041
CONTROL_ID['ID_YAXIS_COMBO'] = 2042
CONTROL_ID['ID_ZAXIS_COMBO'] = 2043



#    if( half_len == len_arr ):

class MdPlotter(wx.Window):
    def __init__(self, parent, id):
        wx.Window.__init__(self, parent, id)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetBackgroundColour('#aaaaaa')
        self.SetSize((400, 400))
        self.buffer = wx.BitmapFromImage(wx.EmptyImage(400, 400))
        self.x_margin = 20
        self.y_margin = 20
        self.scale = -1
        self.axis_1 = 0
        self.axis_2 = 1

    def AdjustScale(self):
        self.width = self.GetSize().width
        self.height = self.GetSize().height
        max_x = -99999
        max_y = -99999

        for mdobject in self.dataset.object_list:
            x, y = mdobject.coords[self.axis_1], mdobject.coords[self.axis_2]
            #print x,y
            max_x = max(math.fabs(x), max_x)
            max_y = max(math.fabs(y), max_y)

        #print "max", max_x, max_y
        self.max_x = max_x
        self.max_y = max_y

        available_x = self.width - self.x_margin * 2
        available_y = self.height - self.y_margin * 2
        #print "avail wxh", w, h
        scale_x = ( available_x ) / ( max_x * 2 )
        scale_y = ( available_y ) / ( max_y * 2 )

        #print "scale", scale_x, scale_y
        self.scale = min(scale_x, scale_y)
        #print "final scale", self.scale

        x_scale = self.max_x
        x_order = 0
        while x_scale < 1:
            x_scale *= 10
            x_order -= 1
        while x_scale > 10:
            x_scale /= 10
            x_order += 1

        #print x_scale, x_order

        upper_x = math.ceil(x_scale)
        if x_scale < 3:
            step = 0.5
            temp_x = 0
        else:
            step = 1
            temp_x = 0
        scales = []
        while temp_x <= upper_x:
            scales.append(temp_x * ( 10 ** (x_order) ))
            scales.append(temp_x * -1 * ( 10 ** (x_order) ))
            temp_x += step

        self.x_scales = scales

        #print "x scales", self.x_scales

        y_scale = self.max_y
        y_order = 0
        while y_scale < 1:
            y_scale *= 10
            y_order -= 1
        while y_scale > 10:
            y_scale /= 10
            y_order += 1

        #print y_scale, y_order

        upper_y = math.ceil(y_scale)
        if y_scale < 3:
            step = 0.5
            temp_y = 0
        else:
            step = 1
            temp_y = 0
        scales = []
        while temp_y <= upper_y:
            scales.append(temp_y * ( 10 ** (y_order) ))
            scales.append(temp_y * -1 * ( 10 ** (y_order) ))
            temp_y += step

        self.y_scales = scales

        #print "y scales", self.y_scales


    def GraphXYtoScreenXY(self, x, y):
        new_x = int(math.floor(float(x) * self.scale + 0.5)) + math.floor(self.width / 2 + 0.5)
        new_y = int(math.floor(float(-1.0 * y) * self.scale + 0.5)) + math.floor(self.height / 2 + 0.5)
        return new_x, new_y

    def ScreenXYtoGraphXY(self, x, y):
        new_x = float(x) / self.scale
        new_y = float(y) / self.scale
        return new_x, new_y

    def DrawToBuffer(self):
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        dc.SetBackground(wx.GREY_BRUSH)
        dc.Clear()

        ''' Draw Axes '''
        dc.SetPen(wx.Pen("black", 1))
        y = int(self.height - self.y_margin)

        dc.DrawLine(self.x_margin, y, self.width, y)
        for x in self.x_scales:
            scr_x, temp_y = self.GraphXYtoScreenXY(x, 0)
            if scr_x > 0 and scr_x < self.width:
                dc.DrawLine(scr_x, y, scr_x, y - int(self.y_margin / 2))
                dc.DrawText(str(x), scr_x - 5, y)

        x = self.x_margin
        dc.DrawLine(x, 0, x, self.height - self.y_margin)
        for y in self.y_scales:
            temp_x, scr_y = self.GraphXYtoScreenXY(0, y)
            if scr_y > 0 and scr_y < self.height:
                dc.DrawLine(x, scr_y, x + int(self.x_margin / 2), scr_y)
                dc.DrawText(str(y), 0, scr_y - 3)

        ''' plot data '''
        dc.SetPen(wx.Pen("red", 1))
        i = 1
        for object in self.dataset.object_list:
            x, y = self.GraphXYtoScreenXY(object.coords[self.axis_1], object.coords[self.axis_2])
            #print x,y
            dc.DrawCircle(x, y, 3)
            dc.DrawText(object.objname, x, y)
            i += 1
        return

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self, self.buffer)

    def SetDataset(self, dataset):
        self.dataset = dataset
        self.AdjustScale()
        self.DrawToBuffer()
        self.Refresh()

    def SetAxes(self, axis1, axis2):
        self.axis_1 = axis1
        self.axis_2 = axis2


class ModanDatasetViewer(wx.Dialog):
    def __init__(self, parent, id=-1):
        wx.Dialog.__init__(self, parent, id, "Analysis", size=CONST['DIALOG_SIZE'])

        panel = wx.Panel(self, -1)

        self.dataset = None
        self.show_index = False
        self.auto_rotate = False
        self.show_wireframe = True
        self.show_meanshape = True
        self.superimposition_method = CONST['IDX_GLS']
        self.xaxis_pc_idx = 1
        self.yaxis_pc_idx = 2
        #self.superimposition = ID_RD_PROCRUSTES
        self.selected_object_list = []

        self.ThreeDViewer = Md3DCanvas(panel)
        self.ThreeDViewer.SetMinSize((400, 400))
        self.ResultViewer = wx.Notebook(panel)
        self.eigenvalue_listctrl = wx.ListCtrl(self.ResultViewer, CONTROL_ID['ID_EIGENVALUE_LISTCTRL'], style=wx.LC_REPORT)
        self.eigenvalue_listctrl.InsertColumn(0, 'PC', width=40)
        self.eigenvalue_listctrl.InsertColumn(1, 'Eigen Val.', width=100)
        self.eigenvalue_listctrl.InsertColumn(2, 'Perct.', width=100)
        self.loading_listctrl = wx.ListCtrl(self.ResultViewer, CONTROL_ID['ID_LOADING_LISTCTRL'], style=wx.LC_REPORT)
        self.loading_listctrl_initialized = False
        self.coordinates_listctrl = wx.ListCtrl(self.ResultViewer, CONTROL_ID['ID_FINALCOORDINATES_LISTCTRL'], style=wx.LC_REPORT)
        self.coordinates_listctrl_initialized = False
        #self.rawdata_listctrl = wx.ListCtrl( self.ResultViewer, ID_RAWDATA_LISTCTRL, style=wx.LC_REPORT)
        #self.rawdata_listctrl_initialized = False
        self.superimposed_listctrl = wx.ListCtrl(self.ResultViewer, CONTROL_ID['ID_SUPERIMPOSED_LISTCTRL'], style=wx.LC_REPORT)
        self.superimposed_listctrl_initialized = False

        self.PCAViewer = PlotCanvas(self.ResultViewer)
        self.PCAViewer.SetPointLabelFunc(self.DrawPointLabel)
        #self.PCAViewer = MdPlotter(panel,-1)
        self.PCAViewer.SetMinSize((400, 400))
        self.PCAViewer.SetEnablePointLabel(True)
        # Create mouse event for showing cursor coords in status bar
        self.PCAViewer.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        # Show closest point when enabled
        self.PCAViewer.canvas.Bind(wx.EVT_MOTION, self.OnMotion)

        self.ResultViewer.AddPage(self.PCAViewer, "Plot")
        self.ResultViewer.AddPage(self.eigenvalue_listctrl, "Eigen value")
        self.ResultViewer.AddPage(self.loading_listctrl, "Loading")
        #self.ResultViewer.AddPage( self.rawdata_listctrl, "Raw data" )
        self.ResultViewer.AddPage(self.superimposed_listctrl, "Superimposed")
        self.ResultViewer.AddPage(self.coordinates_listctrl, "Coordinates")

        if use_mplot:
            pass
            #self.MplotViewer = wxmpl.PlotPanel( self.ResultViewer, -1 )
            #self.MplotViewer.SetMinSize((400, 400))
            #self.Bind( wxmpl.EVT_POINT, self.OnPoint , self.MplotViewer )
            #wxmpl.EVT_POINT(self, self.MplotViewer.GetId(), self.OnPoint)
            #self.ResultViewer.AddPage(self.MplotViewer, "Mplot")
            #self.MplotViewer.mpl_connect('pick_event', self.OnPick)
        self.ResultViewer.SetMinSize((400, 400))

        self.baseline_point_list = []
        self.edge_list = []
        self.landmark_list = []

        self.pc_list = []
        for i in range(15):
            self.pc_list.append('PC' + str(i + 1))

        self.xAxisLabel = wx.StaticText(panel, -1, 'X Axis', style=wx.ALIGN_RIGHT)
        self.xAxisCombo = wx.ComboBox(panel, CONTROL_ID['ID_XAXIS_COMBO'], "PC1", (15, 30), wx.DefaultSize, self.pc_list,
                                      wx.CB_DROPDOWN)
        self.yAxisLabel = wx.StaticText(panel, -1, 'Y Axis', style=wx.ALIGN_RIGHT)
        self.yAxisCombo = wx.ComboBox(panel, CONTROL_ID['ID_YAXIS_COMBO'], "PC2", (15, 30), wx.DefaultSize, self.pc_list,
                                      wx.CB_DROPDOWN)

        self.Bind(wx.EVT_COMBOBOX, self.OnXAxis, id=CONTROL_ID['ID_XAXIS_COMBO'])
        self.Bind(wx.EVT_COMBOBOX, self.OnYAxis, id=CONTROL_ID['ID_YAXIS_COMBO'])
        #self.zAxisLabel = wx.StaticText( panel, -1, 'Z Axis', style=wx.ALIGN_RIGHT )
        #self.zAxisCombo = wx.ComboBox( panel, ID_ZAXIS_COMBO, "PC3", (15,30),wx.DefaultSize, self.pc_list, wx.CB_DROPDOWN )
        axesSizer = wx.BoxSizer()
        axesSizer.Add(self.xAxisLabel, wx.EXPAND)
        axesSizer.Add(self.xAxisCombo, wx.EXPAND)
        axesSizer.Add(self.yAxisLabel, wx.EXPAND)
        axesSizer.Add(self.yAxisCombo, wx.EXPAND)
        #axesSizer.Add( self.zAxisLabel, wx.EXPAND )
        #axesSizer.Add( self.zAxisCombo, wx.EXPAND )

        self.chkAutoRotate = wx.CheckBox(panel, CONTROL_ID['ID_CHK_AUTO_ROTATE'], "Auto Rotate")
        self.chkShowIndex = wx.CheckBox(panel, CONTROL_ID['ID_CHK_SHOW_INDEX'], "Show Index")
        self.chkShowWireframe = wx.CheckBox(panel, CONTROL_ID['ID_CHK_SHOW_WIREFRAME'], "Show Wireframe")
        self.chkShowMeanshape = wx.CheckBox(panel, CONTROL_ID['ID_CHK_SHOW_MEANSHAPE'], "Show Mean Shape")
        self.Bind(wx.EVT_CHECKBOX, self.ToggleAutoRotate, id=CONTROL_ID['ID_CHK_AUTO_ROTATE'])
        self.Bind(wx.EVT_CHECKBOX, self.ToggleShowIndex, id=CONTROL_ID['ID_CHK_SHOW_INDEX'])
        self.Bind(wx.EVT_CHECKBOX, self.ToggleShowWireframe, id=CONTROL_ID['ID_CHK_SHOW_WIREFRAME'])
        self.Bind(wx.EVT_CHECKBOX, self.ToggleShowMeanshape, id=CONTROL_ID['ID_CHK_SHOW_MEANSHAPE'])
        self.chkAutoRotate.SetValue(self.auto_rotate)
        self.chkShowWireframe.SetValue(self.show_wireframe)
        self.chkShowIndex.SetValue(self.show_index)
        self.chkShowMeanshape.SetValue(self.show_meanshape)

        self.checkboxSizer = wx.BoxSizer(wx.VERTICAL)
        self.checkboxSizer.Add(self.chkAutoRotate, wx.EXPAND)
        self.checkboxSizer.Add(self.chkShowIndex, wx.EXPAND)
        self.checkboxSizer.Add(self.chkShowWireframe, wx.EXPAND)
        self.checkboxSizer.Add(self.chkShowMeanshape, wx.EXPAND)

        self.testButton = wx.Button(panel, CONTROL_ID['ID_ANALYZE_BUTTON'], 'Analyze')
        self.cvaButton= wx.Button(panel, -1, 'CVA')
        self.copyButton = wx.Button(panel, -1, 'Copy')
        self.Bind(wx.EVT_BUTTON, self.OnAnalyze, id=CONTROL_ID['ID_ANALYZE_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnCVA, self.cvaButton)
        self.Bind(wx.EVT_BUTTON, self.OnCopy, self.copyButton)

        radioList = ["Bookstein", "SBR", "Procrustes (GLS)", "Resistant fit"]
        self.rdSuperimposition = wx.RadioBox(panel, CONTROL_ID['ID_RADIO_SUPERIMPOSITION'], "Superimposition Method",
                                             choices=radioList, style=wx.RA_VERTICAL)
        self.Bind(wx.EVT_RADIOBOX, self.OnSuperimposition, id=CONTROL_ID['ID_RADIO_SUPERIMPOSITION'])
        self.rdSuperimposition.SetSelection(2)




        #self.rdGroupInfo = wx.RadioBox( panel, wx.NewId(), "Group information", choices=["No group information" for i in range( 10 )], style=wx.RA_VERTICAL )


        self.groupLabel = []
        self.groupLabelSizer = wx.BoxSizer(wx.VERTICAL)
        for i in range(10):
            self.groupLabel.append(wx.StaticText(panel, -1, ''))
            self.groupLabelSizer.Add(self.groupLabel[i], wx.EXPAND)

        il = wx.ImageList(16, 16, True)
        il_max = il.Add(wx.Bitmap("icon/visible_16.png", wx.BITMAP_TYPE_PNG))
        il_max = il.Add(wx.Bitmap("icon/invisible_16.png", wx.BITMAP_TYPE_PNG))
        self.object_listctrl = wx.ListCtrl(panel, CONTROL_ID['ID_OBJECT_LISTCTRL'], style=wx.LC_REPORT)
        self.object_listctrl.InsertColumn(0, '', width=20)
        self.object_listctrl.InsertColumn(1, 'Name', width=80)
        self.object_listctrl.AssignImageList(il, wx.IMAGE_LIST_SMALL)
        #self.object_listctrl.InsertColumn(1,'X', width=landmarkCoordWidth)
        #self.object_listctrl.InsertColumn(2,'Y', width=landmarkCoordWidth)
        #self.object_listctrl.InsertColumn(3,'Z', width=landmarkCoordWidth)
        self.object_listctrl.SetMinSize((100, 400))
        self.object_listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnObjectSelected, id=CONTROL_ID['ID_OBJECT_LISTCTRL'])
        self.object_listctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnObjectSelected, id=CONTROL_ID['ID_OBJECT_LISTCTRL'])
        self.object_listctrl.Bind(wx.EVT_LEFT_DCLICK, self.OnObjectDoubleClick, id=CONTROL_ID['ID_OBJECT_LISTCTRL'])
        #self.object_listctrl.Bind(wx.EVT_LEFT_DOWN, self.OnObjectClick, id=CONTROL_ID['ID_OBJECT_LISTCTRL'])
        #self.object_listctrl.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown, id=CONTROL_ID['ID_OBJECT_LISTCTRL'])
        #self.object_listctrl.Bind(wx.EVT_RIGHT_UP, self.OnRightUp, id=CONTROL_ID['ID_OBJECT_LISTCTRL'])
        self.object_listctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick, id=CONTROL_ID['ID_OBJECT_LISTCTRL'])


        self.canvasOptionSizer = wx.GridBagSizer(hgap=5, vgap=5)
        self.canvasOptionSizer.Add(self.ThreeDViewer, pos=(0, 0), span=(1, 2), flag=wx.EXPAND)
        self.canvasOptionSizer.Add(self.ResultViewer, pos=(0, 3), span=(1, 2), flag=wx.EXPAND)
        self.canvasOptionSizer.Add(self.checkboxSizer, pos=(1, 0), flag=wx.EXPAND)
        #self.canvasOptionSizer.Add( self.chkAutoRotate, pos=(1,0), flag=wx.EXPAND )
        #self.canvasOptionSizer.Add( self.chkShowIndex, pos=(2,0), flag=wx.EXPAND )
        #self.canvasOptionSizer.Add( self.chkShowWireframe, pos=(3,0), flag=wx.EXPAND )
        #self.canvasOptionSizer.Add( self.chkShowMeanshape, pos=(4,0), flag=wx.EXPAND )
        self.canvasOptionSizer.Add(self.rdSuperimposition, pos=(1, 1), flag=wx.EXPAND)
        self.canvasOptionSizer.Add(self.object_listctrl, pos=(0, 2), flag=wx.EXPAND)
        self.canvasOptionSizer.Add(self.testButton, pos=(2, 0), flag=wx.EXPAND)
        self.canvasOptionSizer.Add(self.cvaButton, pos=(2, 1), flag=wx.EXPAND)
        self.canvasOptionSizer.Add(self.copyButton, pos=(2, 2), flag=wx.EXPAND)
        #self.canvasOptionSizer.Add( self.rdGroupInfo, pos=(1,2), span=(4,1),flag=wx.EXPAND)
        self.canvasOptionSizer.Add(self.groupLabelSizer, pos=(1, 3), flag=wx.EXPAND)
        self.canvasOptionSizer.Add(axesSizer, pos=(1, 4), flag=wx.EXPAND)

        self.pca_done = False
        self.show_legend = False
        panel.SetSizer(self.canvasOptionSizer)
        panel.Fit()
        self.panel = panel

    def DrawPointLabel(self, dc, mDataDict):
        """This is the fuction that defines how the pointLabels are plotted
            dc - DC that will be passed
            mDataDict - Dictionary of data that you want to use for the pointLabel

            As an example I have decided I want a box at the curve point
            with some text information about the curve plotted below.
            Any wxDC method can be used.
        """
        # ----------
        dc.SetPen(wx.Pen(wx.BLACK))
        dc.SetBrush(wx.Brush(wx.BLACK, wx.SOLID))

        sx, sy = mDataDict["scaledXY"]  #scaled x,y of closest point
        dc.DrawRectangle(sx - 5, sy - 5, 10, 10)  #10by10 square centered on point
        px, py = mDataDict["pointXY"]
        cNum = mDataDict["curveNum"]
        pntIn = mDataDict["pIndex"]
        legend = mDataDict["legend"]
        #make a string to display
        #s = "Crv# %i, '%s', Pt. (%.2f,%.2f), PtInd %i" %(cNum, legend, px, py, pntIn)
        s = legend
        dc.DrawText(s, sx, sy + 1)
        # -----------

    def OnMouseLeftDown(self, event):
        s = "Left Mouse Down at Point: (%.4f, %.4f)" % self.PCAViewer._getXY(event)
        #print s
        #self.SetStatusText(s)
        event.Skip()  #allows plotCanvas OnMouseLeftDown to be called

    def OnMotion(self, event):
        #show closest point (when enbled)
        if self.PCAViewer.GetEnablePointLabel() == True:
            #make up dict with info for the pointLabel
            #I've decided to mark the closest point on the closest curve
            dlst = self.PCAViewer.GetClosestPoint(self.PCAViewer._getXY(event), pointScaled=True)
            if dlst != []:  #returns [] if none
                curveNum, legend, pIndex, pointXY, scaledXY, distance = dlst
                #make up dictionary to pass to my user function (see DrawPointLabel)
                mDataDict = {"curveNum": curveNum, "legend": legend, "pIndex": pIndex,
                             "pointXY": pointXY, "scaledXY": scaledXY}
                #pass dict to update the pointLabel
                self.PCAViewer.UpdatePointLabel(mDataDict)
        event.Skip()  #go to next handler


    def OnSuperimposition(self, event):
        radioSelected = event.GetEventObject()
        method = radioSelected.GetSelection()
        if method == self.superimposition_method:
            return

        wx.BeginBusyCursor()
        baseline = self.ThreeDViewer.dataset.baseline_point_list

        self.superimposition_method = method
        if method == CONST['IDX_BOOKSTEIN']:
            #print "bookstein"
            if len(baseline) == 0:
                wx.MessageBox("Baseline not defined!")
                wx.EndBusyCursor()
                return
            for mo in self.ThreeDViewer.dataset.object_list:
                mo.bookstein_registration(baseline)
                #mo.move_to_center()
            self.ThreeDViewer.dataset.reference_shape = self.ThreeDViewer.dataset.get_average_shape()
        elif method == CONST['IDX_SBR']:
            #print "sbr"
            if len(baseline) == 0:
                wx.MessageBox("Baseline not defined!")
                wx.EndBusyCursor()
                return
            for mo in self.ThreeDViewer.dataset.object_list:
                mo.sliding_baseline_registration(baseline)
                #mo.move_to_center()
            self.ThreeDViewer.dataset.reference_shape = self.ThreeDViewer.dataset.get_average_shape()
        elif method == CONST['IDX_GLS']:
            #print "procrustes"
            self.ThreeDViewer.dataset.procrustes_superimposition()
            self.ThreeDViewer.dataset.reference_shape = self.ThreeDViewer.dataset.get_average_shape()
        elif method == CONST['IDX_RFTRA']:
            #print "resistant fit"
            self.ThreeDViewer.dataset.resistant_fit_superimposition()
            self.ThreeDViewer.dataset.reference_shape = self.ThreeDViewer.dataset.get_average_shape()
        self.ThreeDViewer.SetSuperimpositionMethod(method)
        #self.SetDataset( self.ThreeDViewer.dataset )
        self.SetObject(self.ThreeDViewer.dataset.reference_shape)
        self.ThreeDViewer.ResetParameters()
        self.ThreeDViewer.Refresh(False)

        if True:
            self.PerformPCA()
            self.VisualizePCAResult()
        wx.EndBusyCursor()

        #self.superimposition =
        #print radioSelected.GetSelection()

    def PerformCVA(self):

        self.cva = MdCanonicalVariate()
        datamatrix = []
        category_list = []
        for obj in self.dataset.object_list:
            datum = []
            for lm in obj.landmark_list:
                datum.extend(lm.coords)
            datamatrix.append(datum)
            for p in obj.property_list:
                if p.propertyname_id == self.selected_propertyname_id:
                    category_list.append(p.property)
        self.cva.SetData(datamatrix)
        self.cva.SetCategory(category_list)
        self.cva.Analyze()
        self.loading_listctrl_initialized = False
        self.coordinates_listctrl_initialized = False

        number_of_axes = min(self.cva.nObservation, self.cva.nVariable)
        self.xAxisCombo.Clear()
        self.yAxisCombo.Clear()
        for i in range(number_of_axes):
            self.xAxisCombo.Append("CV" + str(i + 1))
            self.yAxisCombo.Append("CV" + str(i + 1))
        self.xAxisCombo.SetSelection(0)
        self.yAxisCombo.SetSelection(1)

        self.cva_done = True


    def PerformPCA(self):

        self.pca = MdPrincipalComponent2()
        datamatrix = []
        for obj in self.dataset.object_list:
            datum = []
            for lm in obj.landmark_list:
                datum.extend( lm.coords )
            datamatrix.append(datum)

        self.pca.SetData(datamatrix)
        self.pca.Analyze()
        self.loading_listctrl_initialized = False
        self.coordinates_listctrl_initialized = False

        number_of_axes = min(self.pca.nObservation, self.pca.nVariable)
        self.xAxisCombo.Clear()
        self.yAxisCombo.Clear()
        for i in range(number_of_axes):
            self.xAxisCombo.Append("PC" + str(i + 1))
            self.yAxisCombo.Append("PC" + str(i + 1))

        self.xAxisCombo.SetSelection(0)
        self.yAxisCombo.SetSelection(1)

        self.pca_done = True

    def VisualizePCAResult(self):
        #print self.pca.raw_eigen_values
        if not self.pca_done:
            return

        self.eigenvalue_listctrl.DeleteAllItems()
        for i in range(len(self.pca.raw_eigen_values)):
            #print mo.objname
            self.eigenvalue_listctrl.Append((
            'PC' + str(i + 1), math.floor(self.pca.raw_eigen_values[i] * 100000 + 0.5) / 100000,
            math.floor(self.pca.eigen_value_percentages[i] * 10000 + 0.5) / 100 ))

        ''' loading '''
        if not self.loading_listctrl_initialized:
            self.loading_listctrl.DeleteAllItems()
            self.loading_listctrl.DeleteAllColumns()
            for i in range(len(self.pca.raw_eigen_values)):
                self.loading_listctrl.InsertColumn(i, 'Var' + str(i + 1), width=60)
            self.loading_listctrl.InsertColumn(0, 'PC', width=50)
            self.loading_listctrl_initialized = True
            #print self.pca.loading
            for i in range(self.pca.nVariable):
                list = []
                #list[:] = self.pca.loading[i]
                for j in range(self.pca.nVariable):
                    val = self.pca.loading[i, j]
                    #print val,
                    val = math.floor(val * 1000 + 0.5) / 1000
                    #print val
                    list.append(val)
                list.insert(0, "PC" + str(i + 1))
                self.loading_listctrl.Append(list)

        ''' superimposed coordinates '''
        if not self.superimposed_listctrl_initialized:
            self.superimposed_listctrl.DeleteAllItems()
            self.superimposed_listctrl.DeleteAllColumns()
            for i in range(self.pca.nVariable):
                self.superimposed_listctrl.InsertColumn(i, 'Var' + str(i + 1), width=60)
            self.superimposed_listctrl.InsertColumn(0, 'ObjName', width=80)
            self.superimposed_listctrl_initialized = True

            i = 0
            for obj in self.dataset.object_list:
                list = []
                for j in range(self.pca.nVariable):
                    val = self.pca.data[i][j]
                    val = math.floor(val * 1000 + 0.5) / 1000
                    list.append(val)
                list.insert(0, obj.objname)
                self.superimposed_listctrl.Append(list)
                i += 1

        ''' final coordinates '''
        if not self.coordinates_listctrl_initialized:
            self.coordinates_listctrl.DeleteAllItems()
            self.coordinates_listctrl.DeleteAllColumns()
            for i in range(len(self.pca.raw_eigen_values)):
                self.coordinates_listctrl.InsertColumn(i, 'PC' + str(i + 1), width=60)
            self.coordinates_listctrl.InsertColumn(0, 'ObjName', width=80)
            self.coordinates_listctrl_initialized = True

            ''' coordinates '''
            i = 0
            for obj in self.dataset.object_list:
                list = []
                for j in range(self.pca.nVariable):
                    val = self.pca.rotated_matrix[i, j]
                    val = math.floor(val * 1000 + 0.5) / 1000
                    list.append(val)
                list.insert(0, obj.objname)
                self.coordinates_listctrl.Append(list)
                i += 1

        m = []
        i = 0
        for obj in self.dataset.object_list:
            key = ""
            for p in obj.property_list:
                if p.propertyname_id == self.selected_propertyname_id:
                    key = p.property
            x = self.pca.rotated_matrix[i, self.xaxis_pc_idx - 1]
            y = self.pca.rotated_matrix[i, self.yaxis_pc_idx - 1]
            str_x = str(math.floor(x * 1000 + 0.5) / 1000)
            str_y = str(math.floor(y * 1000 + 0.5) / 1000)
            #print x, y
            i += 1
            m.append(PolyMarker([( x, y )], legend=obj.objname + " (" + key + ") (" + str_x + "," + str_y + ")",
                                colour=self.group_colors[key], marker=self.group_symbols[key]))
        #print m
        #self.PCAViewer.SetEnableLegend(True)
        self.PCAViewer.Draw(PlotGraphics(m, "", "PC" + str(self.xaxis_pc_idx), "PC" + str(self.yaxis_pc_idx)))
        self.PCAViewer.Refresh()

    def VisualizeCVAResult(self):
        #print self.pca.raw_eigen_values
        if not self.cva_done:
            return

        self.eigenvalue_listctrl.DeleteAllItems()
        for i in range(len(self.cva.raw_eigen_values)):
            #print mo.objname
            self.eigenvalue_listctrl.Append((
            'CV' + str(i + 1), math.floor(self.cva.raw_eigen_values[i] * 100000 + 0.5) / 100000,
            math.floor(self.cva.eigen_value_percentages[i] * 10000 + 0.5) / 100 ))

        if not self.loading_listctrl_initialized:
            self.loading_listctrl.DeleteAllItems()
            self.loading_listctrl.DeleteAllColumns()
            for i in range(len(self.pca.raw_eigen_values)):
                self.loading_listctrl.InsertColumn(i, 'Var' + str(i + 1), width=60)
            self.loading_listctrl.InsertColumn(0, 'CV', width=50)
            self.loading_listctrl_initialized = True

            #print self.pca.loading
            for i in range(self.cva.nVariable):
                list = []
                #list[:] = self.pca.loading[i]
                for j in range(self.cva.nVariable):
                    val = self.cva.loading[i, j]
                    #print val,
                    val = math.floor(val * 1000 + 0.5) / 1000
                    #print val
                    list.append(val)
                list.insert(0, "CV" + str(i + 1))
                self.loading_listctrl.Append(list)
        #print self.cva.loading
        #print self.cva.rotated_matrix

        if not self.coordinates_listctrl_initialized:
            self.coordinates_listctrl.DeleteAllItems()
            self.coordinates_listctrl.DeleteAllColumns()
            for i in range(len(self.cva.raw_eigen_values)):
                self.coordinates_listctrl.InsertColumn(i, 'CV' + str(i + 1), width=60)
            self.coordinates_listctrl.InsertColumn(0, 'ObjName', width=80)
            self.coordinates_listctrl_initialized = True

            ''' coordinates '''
            i = 0
            for obj in self.dataset.object_list:
                list = []
                for j in range(self.cva.nVariable):
                    val = self.cva.rotated_matrix[i, j]
                    val = math.floor(val * 1000 + 0.5) / 1000
                    list.append(val)
                list.insert(0, obj.objname)
                self.coordinates_listctrl.Append(list)
                i += 1

        m = []
        i = 0
        for obj in self.dataset.object_list:
            for p in obj.property_list:
                if p.propertyname_id == self.selected_propertyname_id:
                    key = p.property
                    x = self.cva.rotated_matrix[i, self.xaxis_pc_idx - 1]
                    y = self.cva.rotated_matrix[i, self.yaxis_pc_idx - 1]
                    str_x = str(math.floor(x * 1000 + 0.5) / 1000)
                    str_y = str(math.floor(y * 1000 + 0.5) / 1000)
                    #print x, y
                    i += 1
                    m.append(PolyMarker([( x, y )], legend=obj.objname + " (" + key + ") (" + str(x) + "," + str(y) + ")",
                                        colour=self.group_colors[key], marker=self.group_symbols[key]))
        #print m
        #self.PCAViewer.SetEnableLegend(True)
        self.PCAViewer.Draw(PlotGraphics(m, "", "CV" + str(self.xaxis_pc_idx), "CV" + str(self.yaxis_pc_idx)))
        self.PCAViewer.Refresh()


    def OnCopy(self, event):

        #print "copy"
        selected_tab = self.ResultViewer.GetSelection()
        ret_str = ""
        if selected_tab == 0:
            context = wx.ClientDC(self.PCAViewer)
            memory = wx.MemoryDC()
            x, y = self.PCAViewer.GetClientSizeTuple()
            bitmap = wx.EmptyBitmap(x, y, -1)
            memory.SelectObject(bitmap)
            memory.Blit(0, 0, x, y, context, 0, 0)
            memory.SelectObject(wx.NullBitmap)
            #bitmap.SaveFile( "test.bmp", wxBITMAP_TYPE_BMP )
            #img = self.PCAViewer.CopyImage()
            wx.TheClipboard.Open()
            success = wx.TheClipboard.SetData(wx.BitmapDataObject(bitmap))
            wx.TheClipboard.Close()
            #self.PCAViewer.SaveFile()
        elif selected_tab == 1:
            for i in range(len(self.pca.raw_eigen_values)):
                val = math.floor(self.pca.raw_eigen_values[i] * 100000 + 0.5) / 100000
                if val == 0.0: break
                ret_str += 'PC' + str(i + 1) + "\t" + str(val) + "\t" + str(
                    math.floor(self.pca.eigen_value_percentages[i] * 10000 + 0.5) / 100) + "%" + "\n"
            wx.TheClipboard.Open()
            success = wx.TheClipboard.SetData(wx.TextDataObject(ret_str))
            wx.TheClipboard.Close()
            #print ret_str

        elif selected_tab == 2:
            # pca result
            for i in range(len(self.pca.loading[..., 0])):
                list = []
                #list[:] = self.pca.loading[i]
                for val in self.pca.loading[i]:
                    #print val,
                    #val = math.floor( val * 1000 + 0.5 ) / 1000
                    #print val
                    list.append(val)
                list.insert(0, "PC" + str(i + 1))
                ret_str += "\t".join([str(x) for x in list]) + "\n"
            wx.TheClipboard.Open()
            success = wx.TheClipboard.SetData(wx.TextDataObject(ret_str))
            wx.TheClipboard.Close()
            #print ret_str
        elif selected_tab == 3:
            ''' coordinates '''
            i = 0
            for obj in self.dataset.object_list:
                list = []
                for j in range(self.pca.nVariable):
                    val = self.pca.rotated_matrix[i, j]
                    #val = math.floor( val * 1000 + 0.5 ) / 1000
                    list.append(val)
                list.insert(0, obj.objname)
                ret_str += "\t".join([str(x) for x in list]) + "\n"
                #self.coordinates_listctrl.Append( list )
                i += 1
            wx.TheClipboard.Open()
            success = wx.TheClipboard.SetData(wx.TextDataObject(ret_str))
            wx.TheClipboard.Close()


    def OnCVA(self, event):
        self.PerformCVA()
        self.VisualizeCVAResult()

    def OnTest2(self, event):
        print "anova"
        self.manova = MdManova()
        self.manova.AddDataset(self.dataset)
        print "a"
        self.manova.Analyze()

        '''

        if not use_mplot:
            return
        if not self.show_legend:
            fig = self.MplotViewer.get_figure()
            axes = fig.gca()
            keys = []
            for key in self.group_symbols.keys():
                if key != '': keys.append(key)
            axes.legend(keys,
                        'upper center', shadow=True, numpoints=1)
            self.MplotViewer.draw()
            #self.MplotViewer.Show()
            self.show_legend = True
        else:
            fig = self.MplotViewer.get_figure()
            axes = fig.gca()
            axes.legend_ = None
            self.MplotViewer.draw()
            #self.MplotViewer.Show()
            self.show_legend = False
        '''
        return

    def OnPoint(self, event):
        #print "on point"
        #print event
        #print event.axes
        #print event.x, event.y
        #print event.xdata, event.ydata
        if not use_mplot:
            return
        i = 0
        min_dist = 99999
        min_idx = -1
        for object in self.pca.new_dataset.object_list:
            dist = math.sqrt(( object.coords[self.xaxis_pc_idx - 1] - event.xdata ) ** 2 + (
            object.coords[self.yaxis_pc_idx - 1] - event.ydata ) ** 2)
            #print i, object.objname, dist, min_dist, min_idx
            if dist < min_dist:
                min_dist = dist
                min_idx = i
                #print "min:", dist, min_dist, min_idx
            i += 1
        #if min_dist <
        #print self.pca.new_dataset.objects[min_idx].objname
        self.OnAnalyze(None)
        fig = self.MplotViewer.get_figure()
        #fig.clear()
        a = fig.gca()
        x = self.pca.new_dataset.object_list[min_idx].coords[self.xaxis_pc_idx - 1]
        y = self.pca.new_dataset.object_list[min_idx].coords[self.yaxis_pc_idx - 1]
        a.annotate(self.pca.new_dataset.object_list[min_idx].objname, xy=(x, y), xycoords='data',
                   xytext=(-30, -30), textcoords='offset points',
                   arrowprops=dict(arrowstyle="->",
                                   connectionstyle="arc3,rad=.2")
        )
        self.MplotViewer.draw()
        #min_dist = min( min_dist, dist )

        #event.axes.pick(event)
        #print event
        #event.axes.pick(event)

    def OnAnalyze(self, event):
        #self.PerformPCA()
        #self.VisualizePCAResult()

        marker_list_x = {}
        marker_list_y = {}
        marker_list_name = {}
        marker_list_symbol = {}
        symbol_list = ['bo', 'r>', 'ro', 'b>', 'r+', 'rs', 'bs']
        i = 0
        for object in self.pca.new_dataset.object_list:
            key = object.group_list[self.selected_group_idx]
            if not marker_list_x.has_key(key):
                marker_list_x[key] = []
                marker_list_y[key] = []
                marker_list_name[key] = []
                marker_list_symbol[key] = symbol_list[i]
                i += 1
            marker_list_x[key].append(object.coords[self.xaxis_pc_idx - 1])
            marker_list_y[key].append(object.coords[self.yaxis_pc_idx - 1])
            marker_list_name[key].append(object.objname)

        #return

        if not use_mplot:
            return

        fig = self.MplotViewer.get_figure()
        fig.clear()
        a = fig.gca()
        for key in marker_list_x.keys():
            #a.scatter( marker_list_x[key], marker_list_y[key], s=20, c = marker_list_symbol[key][0], marker = marker_list_symbol[key][1]  )#, marker_list_symbol[key] )
            a.plot(marker_list_x[key], marker_list_y[key], marker_list_symbol[key], label=marker_list_name[key],
                   markeredgewidth=0)  #self.OnPick )
        self.MplotViewer.draw()
        #self.MplotViewer.Show()

    def ToggleShowWireframe(self, event):
        self.show_wireframe = self.chkShowWireframe.GetValue()
        if ( self.show_wireframe ):
            self.ThreeDViewer.ShowWireframe()
        else:
            self.ThreeDViewer.HideWireframe()

    def ToggleShowIndex(self, event):
        self.show_index = self.chkShowIndex.GetValue()
        if ( self.show_index ):
            self.ThreeDViewer.ShowIndex()
        else:
            self.ThreeDViewer.HideIndex()

    def ToggleAutoRotate(self, event):
        self.auto_rotate = self.chkAutoRotate.GetValue()
        if ( self.auto_rotate):
            self.ThreeDViewer.BeginAutoRotate()
        else:
            self.ThreeDViewer.EndAutoRotate()

    def ToggleShowMeanshape(self, event):
        self.show_meanshape = self.chkShowMeanshape.GetValue()
        if ( self.show_meanshape):
            self.ThreeDViewer.ShowMeanshape()
        else:
            self.ThreeDViewer.HideMeanshape()

    def SetObject(self, mo):
        #print "opengltestwin setobject"
        self.ThreeDViewer.SetSingleObject(mo)
        if self.auto_rotate:
            self.ThreeDViewer.BeginAutoRotate(50)
            #self.auto_rotate = True

    def SetDataset(self, ds):
        wx.BeginBusyCursor()
        self.dataset = MdDatasetView(ds)
        try:
            self.dataset.procrustes_superimposition()
        except MdException, e:
            wx.MessageBox(str(e))
            wx.EndBusyCursor()
            return
        self.dataset.reference_shape.dataset_id = ds.id
        self.SetObject(self.dataset.reference_shape)
        self.object_listctrl.DeleteAllItems()
        self.edge_list = self.dataset.edge_list
        i = 0

        if len(self.dataset.baseline_point_list) == self.dataset.dimension:
            #print "baseline", ds.baseline
            self.rdSuperimposition.EnableItem(0, True)
            self.rdSuperimposition.EnableItem(1, True)
            self.rdSuperimposition.EnableItem(3, False)
        else:
            self.rdSuperimposition.EnableItem(0, False)
            self.rdSuperimposition.EnableItem(1, False)
            self.rdSuperimposition.EnableItem(3, False)

        for mo in self.dataset.object_list:
            #print mo.objname
            #mo.find()
            mo.visible = True
            mo.selected = False
            self.object_listctrl.Append(( "", mo.objname,  ))
            self.object_listctrl.SetItemImage(i, 0, 0)
            i += 1
        self.ThreeDViewer.SetDataset(self.dataset)
        #print self.dataset.wireframe, self.dataset.edge_list
        self.baseline_point_list = self.dataset.baseline_point_list
        self.edge_list = self.dataset.edge_list

        self.PerformPCA()

        i = 0
        if len(self.dataset.propertyname_list) > 0:
            self.rdGroupInfo = wx.RadioBox(self.panel, wx.NewId(), "Group information",
                                           choices=[p.propertyname for p in self.dataset.propertyname_list], style=wx.RA_VERTICAL)
        else:
            self.rdGroupInfo = wx.RadioBox(self.panel, wx.NewId(), "Group information", choices=["All"],
                                           style=wx.RA_VERTICAL)
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeGroupInfo, self.rdGroupInfo)
        #self.canvasOptionSizer.Add( )
        self.canvasOptionSizer.Add(self.rdGroupInfo, pos=(1, 2), flag=wx.EXPAND)
        self.rdGroupInfo.SetSelection(0)
        self.OnChangeGroupInfo(None)
        #while i < 9:
        #  i+= 1
        #  self.rdGroupInfo.SetItemLabel( i, "" )
        #  self.rdGroupInfo.ShowItem( i, False )
        self.panel.Layout()
        self.panel.Fit()
        wx.EndBusyCursor()
        #self.rdGroupInfo.Set
        #self.rdSuperimposition.SetSelection( 2 )

    def OnChangeGroupInfo(self, event):
        wx.BeginBusyCursor()
        groupname = self.rdGroupInfo.GetStringSelection()
        #"groupname: ", groupname
        found = False
        idx = -1

        for i in range(len(self.dataset.propertyname_list)):
            if groupname == self.dataset.propertyname_list[i].propertyname:
                idx = i
                propertyname_id = self.dataset.propertyname_list[i].id
                found = True
                self.selected_propertyname_id = propertyname_id

        self.group_symbols = {}
        self.group_colors = {}
        if found:
            for object in self.dataset.object_list:
                #"onchange group_list", object.objname, object.group_list
                for p in object.property_list:
                    if p.propertyname_id == propertyname_id:
                        groupinfo = p.property
                        if not self.group_symbols.has_key(groupinfo):
                            self.group_symbols[groupinfo] = 0
                        self.group_symbols[groupinfo] += 1
        symbol_list = ['circle', 'square', 'triangle', 'triangle_down', 'cross', 'plus']
        color_list = ['blue', 'green', 'yellow', 'red', 'grey']  #, 'black' ]

        i = 0
        for key in self.group_symbols.keys():
            self.group_colors[key] = color_list[i % len(color_list)]
            self.group_symbols[key] = symbol_list[i % len(symbol_list)]
            self.groupLabel[i].SetLabel(
                key + ":" + color_list[i % len(color_list)] + " " + symbol_list[i % len(symbol_list)])
            #print i, key
            i += 1
        for i in range(i, 10):
            self.groupLabel[i].SetLabel("")
            #print key, group_symbols[key]
        self.group_colors[''] = 'blue'
        self.group_symbols[''] = 'circle'

        self.VisualizePCAResult()
        wx.EndBusyCursor()
        return

        #self.SetSize((400,400))

    def OnObjectSelected(self, event):
        selected_idx_list = self.GetSelectedItemIndex(self.object_listctrl)
        self.ThreeDViewer.SelectObject(selected_idx_list)
        self.ThreeDViewer.Refresh(False)

    def OnLeftUp(self, event):
        #print "leftup"
        selected_idx_list = self.GetSelectedItemIndex(self.object_listctrl)
        self.ThreeDViewer.SelectObject(selected_idx_list)
        self.ThreeDViewer.Refresh(False)

    def GetSelectedItemIndex(self, listctrl):
        #pass
        rv = []
        selected_idx = listctrl.GetFirstSelected()
        if ( selected_idx < 0 ):
            return rv
        else:
            #rv.append( listctrl.GetItemText(selected_idx) )
            rv.append(selected_idx)

        while (1):
            selected_idx = listctrl.GetNextSelected(selected_idx)
            if ( selected_idx < 0 ):
                break
            rv.append(selected_idx)
            #rv.append( listctrl.GetItemText(selected_idx) )

        return rv

    def OnObjectClick(self, event):
        selected_idx = self.object_listctrl.GetFocusedItem()
        if self.ThreeDViewer.dataset.object_list[selected_idx].visible:
            #print "visible -> invisible"
            self.object_listctrl.SetItemImage(selected_idx, 1, 1)
        else:
            #print "invisible -> visible"
            self.object_listctrl.SetItemImage(selected_idx, 0, 0)
        self.ThreeDViewer.ToggleObjectVisibility(selected_idx)
        self.ThreeDViewer.Refresh(False)

    def OnObjectDoubleClick(self, event):
        selected_idx = self.object_listctrl.GetFocusedItem()
        if self.ThreeDViewer.dataset.object_list[selected_idx].visible:
            #print "visible -> invisible"
            self.object_listctrl.SetItemImage(selected_idx, 1, 1)
        else:
            #print "invisible -> visible"
            self.object_listctrl.SetItemImage(selected_idx, 0, 0)
        self.ThreeDViewer.ToggleObjectVisibility(selected_idx)
        self.ThreeDViewer.Refresh(False)

    def OnRightDown(self,event):
        event_point = event.GetPoint()
        #print event_point

        m = wx.Menu()
        i = m.Append(wx.NewId(), '&Hide this')
        self.Bind(wx.EVT_MENU, self.OnHideThis, i)
        i = m.Append(wx.NewId(), 'Hide &Others')
        self.Bind(wx.EVT_MENU, self.OnHideOthers, i)
        self.PopupMenu(m, event_point)

    def OnRightUp(self,event):
        event_point = event.GetPoint()
        #print event_point

    def OnRightClick(self,event):

        itemid = self.object_listctrl.GetFirstSelected()
        #print "first selected item: ", itemid
        if ( itemid < 0 ):
            return
        object_idx_list = []
        while ( itemid >= 0 ):
            object_idx_list.append(itemid)
            itemid = self.object_listctrl.GetNextSelected(itemid)
        self.selected_object_list = object_idx_list


        selected_idx = self.object_listctrl.GetFocusedItem()
        self.selected_object_list = [selected_idx]

        m = wx.Menu()
        if self.ThreeDViewer.dataset.object_list[selected_idx].visible:
            i = m.Append(wx.NewId(), '&Hide this')
            self.Bind(wx.EVT_MENU, self.OnHideThis, i)
        else:
            i = m.Append(wx.NewId(), '&Show this')
            self.Bind(wx.EVT_MENU, self.OnShowThis, i)
        i = m.Append(wx.NewId(), 'Hide &Others')
        self.Bind(wx.EVT_MENU, self.OnHideOthers, i)
        i = m.Append(wx.NewId(), 'S&how others')
        self.Bind(wx.EVT_MENU, self.OnShowOthers, i)

        event_point = event.GetPoint()
        pos = self.object_listctrl.GetPosition()
        (x1, y1 )= pos
        (x2, y2 ) = event_point
        menu_point = ( x1+x2, y1+y2 )
        #print pos
        #print "right click", menu_point

        self.PopupMenu(m, menu_point)

    def OnShowThis(self,event):
        for i in range(len(self.ThreeDViewer.dataset.object_list)):
            if i in self.selected_object_list and not self.ThreeDViewer.dataset.object_list[i].visible:
                self.object_listctrl.SetItemImage(i, 0, 0)
                self.ThreeDViewer.ToggleObjectVisibility(i)
        self.ThreeDViewer.Refresh(False)

    def OnHideThis(self,event):
        for i in range(len(self.ThreeDViewer.dataset.object_list)):
            if i in self.selected_object_list and self.ThreeDViewer.dataset.object_list[i].visible:
                self.object_listctrl.SetItemImage(i, 1, 1)
                self.ThreeDViewer.ToggleObjectVisibility(i)
        self.ThreeDViewer.Refresh(False)

    def OnHideOthers(self,event):
        for i in range(len(self.ThreeDViewer.dataset.object_list)):
            if i not in self.selected_object_list and self.ThreeDViewer.dataset.object_list[i].visible:
                self.object_listctrl.SetItemImage(i, 1, 1)
                self.ThreeDViewer.ToggleObjectVisibility(i)
        self.ThreeDViewer.Refresh(False)
        #print self.selected_object_list
        #print "hide others"

    def OnShowOthers(self,event):
        for i in range(len(self.ThreeDViewer.dataset.object_list)):
            if i not in self.selected_object_list and not self.ThreeDViewer.dataset.object_list[i].visible:
                self.object_listctrl.SetItemImage(i, 0, 0)
                self.ThreeDViewer.ToggleObjectVisibility(i)
        self.ThreeDViewer.Refresh(False)
        #print self.selected_object_list
        #print "hide others"

    def OnXAxis(self, event):
        x = self.xAxisCombo.GetValue()
        xaxis = x.replace("PC", "")
        self.xaxis_pc_idx = int(xaxis)
        self.VisualizePCAResult()

    def OnYAxis(self, event):
        y = self.yAxisCombo.GetValue()
        yaxis = y.replace("PC", "")
        self.yaxis_pc_idx = int(yaxis)
        self.VisualizePCAResult()
