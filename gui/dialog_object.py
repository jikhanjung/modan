#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import wx.lib.buttons as buttons
from libpy.conf import ModanConf
from libpy.modan_dbclass import *
from libpy.dataimporter import ModanDataImporter
from gui.md_3d_canvas import Md3DCanvas
from gui.md_image_control import ModanImageControl, CONST
from PIL import Image

from ctypes import util
try:
    from OpenGL.platform import win32
except AttributeError:
    pass


CONTROL_ID = {}
CONTROL_ID['ID_SAVE_BUTTON'] = 2000
CONTROL_ID['ID_DELETE_BUTTON'] = 2001
CONTROL_ID['ID_CLOSE_BUTTON'] = 2002
CONTROL_ID['ID_SHOW_BUTTON'] = 2003
CONTROL_ID['ID_COMBO_DSNAME'] = 2004
CONTROL_ID['ID_LM_GRID_CTRL'] = 2010
CONTROL_ID['ID_LM_PASTE_BUTTON'] = 2011
CONTROL_ID['ID_LM_ADD_BUTTON'] = 2012
CONTROL_ID['ID_LM_DELETE_BUTTON'] = 2013
CONTROL_ID['ID_COORD_ADD_BUTTON'] = 2014
CONTROL_ID['ID_XCOORD'] = 2015
CONTROL_ID['ID_YCOORD'] = 2016
CONTROL_ID['ID_ZCOORD'] = 2017
CONTROL_ID['ID_IMAGE_LOAD_BUTTON'] = 2018
CONTROL_ID['ID_LANDMARK_BUTTON'] = 2021
CONTROL_ID['ID_CALIBRATION_BUTTON'] = 2022
CONTROL_ID['ID_IMAGE_COPY_BUTTON'] = 2023
CONTROL_ID['ID_IMAGE_PASTE_BUTTON'] = 2024
CONTROL_ID['ID_CHK_COORDS_IN_MILLIMETER'] = 2025
CONTROL_ID['ID_WIREFRAME_BUTTON'] = 2026
CONTROL_ID['ID_BASELINE_BUTTON'] = 2027
CONTROL_ID['ID_MISSING_DATA_BUTTON'] = 2028

CONTROL_ID['ID_CHK_AUTO_ROTATE'] = 2031
CONTROL_ID['ID_CHK_SHOW_INDEX'] = 2032
CONTROL_ID['ID_CHK_SHOW_WIREFRAME'] = 2033
CONTROL_ID['ID_CHK_SHOW_BASELINE'] = 2034


LM_MISSING_VALUE = -99999

DIALOG_SIZE = wx.Size(1024, 768)
landmarkSeqWidth = 40
landmarkCoordWidth_2D = 89
landmarkCoordWidth_3D = 59
landmarkCoordHeight = 22

def piltoimage(pil, alpha=True):
    """Convert PIL Image to wx.Image."""
    if alpha:
        #print "alpha 1", clock()
        image = apply(wx.EmptyImage, pil.size)
        #print "alpha 2", clock()
        image.SetData(pil.convert("RGB").tostring())
        #print "alpha 3", clock()
        image.SetAlphaData(pil.convert("RGBA").tostring()[3::4])
        #print "alpha 4", clock()
    else:
        #print "no alpha 1", clock()
        image = wx.EmptyImage(pil.size[0], pil.size[1])
        #print "no alpha 2", clock()
        new_image = pil.convert('RGB')
        #print "no alpha 3", clock()
        data = new_image.tostring()
        #print "no alpha 4", clock()
        image.SetData(data)
        #print "no alpha 5", clock()
    #print "pil2img", image.GetWidth(), image.GetHeight()
    return image


def imagetopil(image):
    """Convert wx.Image to PIL Image."""
    #print "img2pil", image.GetWidth(), image.GetHeight()
    pil = Image.new('RGB', (image.GetWidth(), image.GetHeight()))
    pil.fromstring(image.GetData())
    return pil


CONTROL_ID['ID_CALIBRATION_OKAY_BUTTON'] = 1001
CONTROL_ID['ID_CALIBRATION_CANCEL_BUTTON'] = 1002


class UnitCalibrationDlg(wx.Dialog):
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, 'Calibration Unit', size=(320, 180))
        self.panel = panel = wx.Panel(self, -1)
        self.maintext = wx.StaticText(panel, -1, 'Enter length in millimeter:', style=wx.ALIGN_LEFT)
        self.length = wx.TextCtrl(panel, -1, '1')
        self.unittext = wx.StaticText(panel, -1, 'mm', style=wx.ALIGN_LEFT)

        self.okButton = wx.Button(panel, CONTROL_ID['ID_CALIBRATION_OKAY_BUTTON'], 'OK')
        self.cancelButton = wx.Button(panel, CONTROL_ID['ID_CALIBRATION_CANCEL_BUTTON'], 'Cancel')
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=CONTROL_ID['ID_CALIBRATION_OKAY_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=CONTROL_ID['ID_CALIBRATION_CANCEL_BUTTON'])

        #x = self.GetSize().width / 2
        #y = self.GetSize().height/ 2
        rowHeight = 22
        controlWidth = ( 150, 30, 20 )
        controls = ( self.maintext, self.length, self.unittext )
        x = 60
        y = 50
        for i in range(len(controls)):
            controls[i].SetSize(( controlWidth[i], rowHeight ))
            controls[i].SetPosition(( x, y ))
            x += controlWidth[i]

        x = 110
        y = 100
        buttonWidth = ( 45, 45)
        buttons = ( self.okButton, self.cancelButton )
        for i in range(len(buttons)):
            buttons[i].SetSize(( buttonWidth[i], rowHeight ))
            buttons[i].SetPosition(( x, y ))
            x += buttonWidth[i]

        panel.Fit()
        #self.Show()
        self.length.SetFocus()
        #self.forms['objname'] = wx.TextCtrl(panel, -1, '')

    def OnOk(self, event):
        self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def GetValue(self):
        return self.length.GetValue()

class ModanObjectDialog(wx.Dialog):
    def __init__(self, parent, id):
        #print "object dialog init"
        wx.Dialog.__init__(self, parent, id, 'MdObject', size=DIALOG_SIZE,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        #panel = self
        self.app = wx.GetApp()
        self.frame = parent
        self.panel = panel = wx.Panel(self, -1)
        #print panel
        mdconf = ModanConf()
        self.conf = mdconf.item
        self.forms = {}
        self.modified = False
        self.mdobject = None
        self.dataset = None

        self.landmark_list = []
        #self.mdobject = MdObject()
        self.baseline_point_list = []
        self.edge_list = []
        self.show_index = True
        self.auto_rotate = False
        self.show_wireframe = True
        self.show_baseline = False
        self.coords_in_millimeter = False
        self.dimension = 2
        self.is_wireframe_changed = False
        self.is_baseline_changed = False
        self.is_confirmed_wireframe_or_baseline_edit = False

        ## ID
        self.IDLabel = wx.StaticText(panel, -1, 'ID', style=wx.ALIGN_CENTER)
        self.forms['id'] = wx.StaticText(panel, -1, '', size=(30, -1),
                                         style=wx.ALIGN_LEFT)
        self.forms['id'].SetBackgroundColour('#aaaaaa')

        ## Dataset, object name, description and scale
        # dataset label and form, event setting
        self.dsnameLabel = wx.StaticText(panel, -1, 'Dataset', style=wx.ALIGN_CENTER)
        self.forms['dsname'] = wx.StaticText(panel, -1, '', style=wx.ALIGN_CENTER)
        #self.forms['dsname'] = wx.ComboBox(panel, ID_COMBO_DSNAME, "", (15, 30), wx.DefaultSize, [], wx.CB_DROPDOWN)
        self.objnameLabel = wx.StaticText(panel, -1, 'Name', style=wx.ALIGN_CENTER)
        self.forms['objname'] = wx.TextCtrl(panel, -1, '')
        self.objdescLabel = wx.StaticText(panel, -1, 'Description', style=wx.ALIGN_CENTER)
        self.forms['objdesc'] = wx.TextCtrl(panel, -1, '', style=wx.TE_MULTILINE)
        self.forms['objdesc'].SetMinSize((300, 100))
        self.coordsLabel = wx.StaticText(panel, -1, 'Coords.', style=wx.ALIGN_CENTER)

        '''
        self.groupLabel = []
        self.groupText = []
        for i in range(10):
            self.groupLabel.append(wx.StaticText(panel, -1, '', style=wx.ALIGN_CENTER))
            self.groupText.append(wx.TextCtrl(panel, -1, ''))
        '''

        # 3D viewer
        self.ThreeDViewer = Md3DCanvas(panel)
        self.chkAutoRotate = wx.CheckBox(panel, CONTROL_ID['ID_CHK_AUTO_ROTATE'], "Auto Rotate")
        self.chkShowIndex = wx.CheckBox(panel, CONTROL_ID['ID_CHK_SHOW_INDEX'], "Show Index")
        self.chkShowWireframe = wx.CheckBox(panel, CONTROL_ID['ID_CHK_SHOW_WIREFRAME'], "Show Wireframe")
        self.chkShowBaseline = wx.CheckBox(panel, CONTROL_ID['ID_CHK_SHOW_BASELINE'], "Show Baseline")
        self.Bind(wx.EVT_CHECKBOX, self.ToggleAutoRotate, id=CONTROL_ID['ID_CHK_AUTO_ROTATE'])
        self.Bind(wx.EVT_CHECKBOX, self.ToggleShowIndex, id=CONTROL_ID['ID_CHK_SHOW_INDEX'])
        self.Bind(wx.EVT_CHECKBOX, self.ToggleShowWireframe, id=CONTROL_ID['ID_CHK_SHOW_WIREFRAME'])
        self.Bind(wx.EVT_CHECKBOX, self.ToggleShowBaseline, id=CONTROL_ID['ID_CHK_SHOW_BASELINE'])
        self.chkAutoRotate.SetValue(self.auto_rotate)
        self.chkShowWireframe.SetValue(self.show_wireframe)
        self.chkShowBaseline.SetValue(self.show_baseline)
        self.chkShowIndex.SetValue(self.show_index)
        self.ThreeDViewer.show_index = self.show_index
        self.ThreeDViewer.show_wireframe = self.show_wireframe
        self.ThreeDViewer.show_baseline = self.show_baseline
        #self.threeDWireframeButton = wx.Button( panel, ID_WIREFRAME_BUTTON, 'Wireframe' )

        ''' 2D viewer '''
        self.TwoDViewer = ModanImageControl(panel, -1)
        self.slBright = wx.Slider(panel, -1, 0, -100, 100)
        self.slContrast = wx.Slider(panel, -1, 0, -100, 100)
        self.Bind(wx.EVT_SCROLL, self.OnSlide)
        self.TwoDViewer.show_index = self.show_index
        self.TwoDViewer.show_wireframe = self.show_wireframe
        self.TwoDViewer.show_baseline = self.show_baseline

        ''' Edit buttons '''
        landmark_bmp = wx.Image("icon/landmark_24.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.landmarkButton = buttons.GenBitmapToggleButton(panel, CONTROL_ID['ID_LANDMARK_BUTTON'], landmark_bmp)
        self.landmarkButton.SetToolTipString("Edit landmark")

        missing_bmp = wx.Image("icon/missing_16.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.missingDataButton = buttons.GenBitmapToggleButton(panel, CONTROL_ID['ID_MISSING_DATA_BUTTON'], missing_bmp)
        self.missingDataButton.SetToolTipString("Missing landmark")

        calib_bmp = wx.Image("icon/calib_24.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.calibrationButton = buttons.GenBitmapToggleButton(panel, CONTROL_ID['ID_CALIBRATION_BUTTON'], calib_bmp)
        self.calibrationButton.SetToolTipString("Calibration")

        wireframe_bmp = wx.Image("icon/wireframe_2_16.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.wireframeButton = buttons.GenBitmapToggleButton(panel, CONTROL_ID['ID_WIREFRAME_BUTTON'], wireframe_bmp)
        self.wireframeButton.SetToolTipString("Edit wireframe")

        baseline_bmp = wx.Image("icon/baseline_16.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.baselineButton = buttons.GenBitmapToggleButton(panel, CONTROL_ID['ID_BASELINE_BUTTON'], baseline_bmp)
        self.baselineButton.SetToolTipString("Edit baseline")

        ''' Image buttons '''
        imageload_bmp = wx.Image("icon/load_image_24.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        imagecopy_bmp = wx.Image("icon/copy_24.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        imagepaste_bmp = wx.Image("icon/paste_24.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.imageLoadButton = buttons.GenBitmapButton(panel, CONTROL_ID['ID_IMAGE_LOAD_BUTTON'], imageload_bmp)
        self.imageCopyButton = buttons.GenBitmapButton(panel, CONTROL_ID['ID_IMAGE_COPY_BUTTON'], imagecopy_bmp)
        self.imagePasteButton = buttons.GenBitmapButton(panel, CONTROL_ID['ID_IMAGE_PASTE_BUTTON'], imagepaste_bmp)
        self.imageLoadButton.SetToolTipString("Load image from file")
        self.imageCopyButton.SetToolTipString("Copy image into Clipboard")
        self.imagePasteButton.SetToolTipString("Paste image from Clipboard")

        #self.Bind( wx.EVT_BUTTON, self.On2DZoom, id=ID_2D_ZOOM_BUTTON )
        #self.Bind( wx.EVT_BUTTON, self.On2DPan, id=ID_2D_PAN_BUTTON )
        self.Bind(wx.EVT_BUTTON, self.OnLandmarkMode, id=CONTROL_ID['ID_LANDMARK_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnCalibrationMode, id=CONTROL_ID['ID_CALIBRATION_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnBaselineMode, id=CONTROL_ID['ID_BASELINE_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnMissingData, id=CONTROL_ID['ID_MISSING_DATA_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnWireframeMode, id=CONTROL_ID['ID_WIREFRAME_BUTTON'])

        self.Bind(wx.EVT_BUTTON, self.OnImageLoad, id=CONTROL_ID['ID_IMAGE_LOAD_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnImageCopy, id=CONTROL_ID['ID_IMAGE_COPY_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnImagePaste, id=CONTROL_ID['ID_IMAGE_PASTE_BUTTON'])

        self.chkCoordsInMillimeter = wx.CheckBox(panel, CONTROL_ID['ID_CHK_COORDS_IN_MILLIMETER'], "Coords. in mm")
        self.Bind(wx.EVT_CHECKBOX, self.ToggleCoordsInMillimeter, id=CONTROL_ID['ID_CHK_COORDS_IN_MILLIMETER'])
        self.chkCoordsInMillimeter.SetValue(self.coords_in_millimeter)

        """ Landmarks : replace with Grid control or its subclass later"""
        self.landmarkLabel = wx.StaticText(panel, -1, 'Landmarks', style=wx.ALIGN_CENTER)
        self.forms['landmark_list'] = wx.ListCtrl(panel, CONTROL_ID['ID_LM_GRID_CTRL'], style=wx.LC_REPORT)
        #    self.forms['landmark_list'].InsertColumn(3,'Z', width=landmarkCoordWidth)
        self.forms['xcoord'] = wx.TextCtrl(panel, id=CONTROL_ID['ID_XCOORD'], value='', style=wx.TE_PROCESS_ENTER)
        self.forms['ycoord'] = wx.TextCtrl(panel, id=CONTROL_ID['ID_YCOORD'], value='', style=wx.TE_PROCESS_ENTER)
        self.forms['zcoord'] = wx.TextCtrl(panel, id=CONTROL_ID['ID_ZCOORD'], value='', style=wx.TE_PROCESS_ENTER)
        self.coordAddButton = wx.Button(panel, CONTROL_ID['ID_COORD_ADD_BUTTON'], 'Add')
        self.coordAddButton.SetMinSize(( landmarkSeqWidth, landmarkCoordHeight))
        self.Bind(wx.EVT_BUTTON, self.AddCoord, id=CONTROL_ID['ID_COORD_ADD_BUTTON'])
        self.Bind(wx.EVT_TEXT_ENTER, self.AddCoord, id=CONTROL_ID['ID_XCOORD'])
        self.Bind(wx.EVT_TEXT_ENTER, self.AddCoord, id=CONTROL_ID['ID_YCOORD'])
        self.Bind(wx.EVT_TEXT_ENTER, self.AddCoord, id=CONTROL_ID['ID_ZCOORD'])

        self.forms['landmark_list'].Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick, id=CONTROL_ID['ID_LM_GRID_CTRL'])
        self.forms['landmark_list'].Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLandmarkSelected, id=CONTROL_ID['ID_LM_GRID_CTRL'])
        self.forms['landmark_list'].Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnLandmarkSelected, id=CONTROL_ID['ID_LM_GRID_CTRL'])

        ## Buttons
        self.saveButton = wx.Button(panel, CONTROL_ID['ID_SAVE_BUTTON'], 'Save')
        #self.showButton = wx.Button(panel, ID_SHOW_BUTTON, 'Show')
        self.deleteButton = wx.Button(panel, CONTROL_ID['ID_DELETE_BUTTON'], 'Delete')
        self.closeButton = wx.Button(panel, CONTROL_ID['ID_CLOSE_BUTTON'], 'Close')
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=CONTROL_ID['ID_SAVE_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnDelete, id=CONTROL_ID['ID_DELETE_BUTTON'])
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=CONTROL_ID['ID_CLOSE_BUTTON'])
        #self.Bind(wx.EVT_BUTTON, self.OnShow, id=ID_SHOW_BUTTON)

        self.ppmm = -1
        self.has_dataset = False
        #panel.SetSizer(self.mainSizer)
        self.AlignControls()
        panel.Fit()
        #self.Show()
        self.forms['objname'].SetFocus()
        #print "end init"

    def OnSlide(self, event):
        bright = self.slBright.GetValue()
        contrast = self.slContrast.GetValue()
        self.TwoDViewer.SetBrightness(bright)
        self.TwoDViewer.SetContrast(contrast)
        self.TwoDViewer.DrawToBuffer()
        #print bright, contrast

    def set_dimension(self, dimension):
        #print "set dimension", dimension

        if dimension == 2:
            self.SetSize(wx.Size(1024, 600))
            self.auto_rotate = False
            self.chkAutoRotate.SetValue(self.auto_rotate)
            #self.SetSize( wx.Size( 1280, 600 ) )
            #self.auto_rotate = False
            #self.chkAutoRotate.Enable( False )
            size = self.forms['ycoord'].GetSize()
            pos = self.forms['ycoord'].GetPosition()
            x_diff = int(size.width / 2.0)
            pos.x += x_diff
            size.width += x_diff
            self.forms['landmark_list'].InsertColumn(0, 'X', width=landmarkCoordWidth_2D)
            self.forms['landmark_list'].InsertColumn(1, 'Y', width=landmarkCoordWidth_2D)
            self.forms['xcoord'].SetSize(size)
            self.forms['ycoord'].SetPosition(pos)
            self.forms['ycoord'].SetSize(size)
            self.forms['zcoord'].Hide()
            self.TwoDViewer.Show()
            self.ThreeDViewer.Hide()
            self.chkAutoRotate.Hide()
            self.imageLoadButton.Show()
            self.imageCopyButton.Show()
            self.imagePasteButton.Show()
            self.slBright.Hide()
            self.slContrast.Hide()
            self.chkCoordsInMillimeter.Show()
            self.objectViewer = self.TwoDViewer
        else:
            self.SetSize(wx.Size(1024, 600))
            self.auto_rotate = False
            dimension = 3
            self.forms['zcoord'].Show()
            self.forms['landmark_list'].InsertColumn(0, 'X', width=landmarkCoordWidth_3D)
            self.forms['landmark_list'].InsertColumn(1, 'Y', width=landmarkCoordWidth_3D)
            self.forms['landmark_list'].InsertColumn(2, 'Z', width=landmarkCoordWidth_3D)
            self.TwoDViewer.Hide()
            self.ThreeDViewer.Show()
            self.chkAutoRotate.Show()
            self.imageLoadButton.Hide()
            self.imageCopyButton.Hide()
            self.imagePasteButton.Hide()
            self.slBright.Hide()
            self.slContrast.Hide()
            self.chkCoordsInMillimeter.Hide()
            self.objectViewer = self.ThreeDViewer

        self.dimension = dimension
        self.chkAutoRotate.SetValue(self.auto_rotate)
        self.ToggleAutoRotate(None)

    def AlignControls(self):
        xMargin = 2
        yMargin = 2
        rowHeight = 22
        labelWidth = 60
        fieldWidth = 200
        sliderWidth = 100
        x = xMargin
        y = yMargin

        labels = ( self.IDLabel, self.dsnameLabel, self.objnameLabel, self.objdescLabel, self.landmarkLabel )
        fields = (self.forms['id'], self.forms['dsname'], self.forms['objname'], self.forms['objdesc'],
                  self.forms['landmark_list'])
        heights = ( 1, 1, 1, 3, 10 )
        for i in range(len(labels)):
            x = xMargin
            labels[i].SetPosition(( x, y ))
            #print x, y
            labels[i].SetSize(( labelWidth, heights[i] * rowHeight ))
            x += labelWidth + xMargin
            fields[i].SetPosition(( x, y ))
            #print x, y
            fields[i].SetSize(( fieldWidth, heights[i] * rowHeight ))
            y += heights[i] * rowHeight + yMargin
        self.coordsLabel.SetPosition(( xMargin, y ))
        self.coordsLabel.SetSize(( labelWidth, rowHeight ))

        buttons1 = [ self.forms['xcoord'], self.forms['ycoord'] ]
        if self.dimension == 3:
            buttons1.append(self.forms['zcoord'])
        buttons1.append(self.coordAddButton)

        x = xMargin
        x += labelWidth + xMargin
        buttonWidth = int(fieldWidth / len(buttons1))
        for i in range(len(buttons1)):
            buttons1[i].SetPosition(( x, y ))
            buttons1[i].SetSize(( buttonWidth, rowHeight ))
            x += buttonWidth

        y += rowHeight + yMargin
        x = xMargin
        # 2D/3D viewer
        x = xMargin
        y = yMargin
        x += labelWidth + fieldWidth + xMargin * 2
        viewerWidth = 640
        viewerHeight = 480
        #print viewerWidth, viewerHeight
        self.TwoDViewer.SetPosition(( x, y ))
        self.TwoDViewer.SetSize(( viewerWidth, viewerHeight ))
        self.ThreeDViewer.SetPosition(( x, y ))
        self.ThreeDViewer.SetSize(( viewerWidth, viewerHeight ))

        buttonWidth = 32
        buttonHeight = 32
        editButtons = (
        self.landmarkButton, self.calibrationButton, self.wireframeButton, self.baselineButton, self.missingDataButton )
        imageButtons = ( self.imageCopyButton, self.imagePasteButton, self.imageLoadButton )
        editButtonWidth = int(sliderWidth / 2)
        y = yMargin
        x = xMargin
        x += labelWidth + fieldWidth + xMargin * 2
        x += viewerWidth + xMargin
        for i in range(len(editButtons)):
            #print i, x, y
            editButtons[i].SetPosition(( x, y ))
            editButtons[i].SetSize(( buttonWidth, buttonHeight))
            if int(i / 2.0) == ( i / 2.0 ):
                x += buttonWidth
            else:
                x -= buttonWidth
                y += buttonHeight+ yMargin
        if int(i / 2.0) != ( i / 2.0 ):
            y += buttonHeight + yMargin

        x = xMargin
        x += labelWidth + fieldWidth + xMargin * 2
        x += viewerWidth + xMargin
        y += buttonHeight + yMargin

        for i in range(len(imageButtons)):
            #print i, x, y
            imageButtons[i].SetPosition(( x, y ))
            imageButtons[i].SetSize(( buttonWidth, buttonHeight ))
            if int(i / 2.0) == ( i / 2.0 ):
                x += buttonWidth
            else:
                x -= buttonWidth
                y += buttonHeight + yMargin
        if int(i / 2.0) != ( i / 2.0 ):
            y += buttonHeight + yMargin

        x = xMargin
        x += labelWidth + fieldWidth + xMargin * 2
        x += viewerWidth + xMargin
        y += rowHeight + yMargin
        self.slBright.SetPosition(( x, y ))
        self.slBright.SetSize(( sliderWidth, rowHeight ))
        y += rowHeight + yMargin
        self.slContrast.SetPosition(( x, y ))
        self.slContrast.SetSize(( sliderWidth, rowHeight ))
        y += rowHeight + yMargin
        self.chkCoordsInMillimeter.SetPosition(( x, y ))
        self.chkCoordsInMillimeter.SetSize(( sliderWidth, rowHeight ))
        y += rowHeight + yMargin

        y = yMargin
        x = xMargin
        y += viewerHeight + yMargin
        x += labelWidth + fieldWidth + xMargin * 2
        checkboxes = ( self.chkAutoRotate, self.chkShowWireframe, self.chkShowIndex, self.chkShowBaseline )
        checkboxWidth = viewerWidth / len(checkboxes)
        for i in range(len(checkboxes)):
            checkboxes[i].SetPosition(( x, y ))
            checkboxes[i].SetSize(( checkboxWidth, rowHeight ))
            x += checkboxWidth

        y += rowHeight
        buttonWidth = 100
        x = self.GetSize().width / 2 - 2 * buttonWidth
        buttons2 = ( self.saveButton, self.deleteButton, self.closeButton )
        for i in range(len(buttons2)):
            buttons2[i].SetPosition(( x, y ))
            #print x, y
            buttons2[i].SetSize(( buttonWidth, rowHeight ))
            x += buttonWidth

    def reset_bitmap_buttons(self,mode=CONST['ID_LANDMARK_MODE']):
        unset = False
        self.landmarkButton.SetValue(unset)
        self.calibrationButton.SetValue(unset)
        self.wireframeButton.SetValue(unset)
        self.baselineButton.SetValue(unset)
        if mode==CONST['ID_LANDMARK_MODE']:
            self.landmarkButton.SetValue(not self.landmarkButton.GetValue())
        elif mode==CONST['ID_CALIBRATION_MODE']:
            self.calibrationButton.SetValue(not self.calibrationButton.GetValue())
        elif mode==CONST['ID_WIREFRAME_MODE']:
            self.wireframeButton.SetValue(not self.wireframeButton.GetValue())
        elif mode==CONST['ID_BASELINE_MODE']:
            self.baselineButton.SetValue(not self.baselineButton.GetValue())
        if self.dimension == 2:
            self.TwoDViewer.SetMode(mode)
        elif self.dimension == 3:
            self.ThreeDViewer.SetMode(mode)

    def OnWireframeMode(self, event):
        if self.dimension == 3:
            pass #return
        if self.ConfirmWireframeOrBaselineEdit() != wx.ID_YES:
            return

        if self.show_wireframe == False:
            self.show_wireframe = True
            self.chkShowWireframe.SetValue(self.show_wireframe)
            self.ToggleShowWireframe(event)

        self.reset_bitmap_buttons(CONST['ID_WIREFRAME_MODE'])

    def OnBaselineMode(self, event):
        if self.dimension == 3:
            pass #return
        if self.ConfirmWireframeOrBaselineEdit() != wx.ID_YES:
            return

        if self.show_baseline == False:
            self.show_baseline = True
            self.chkShowBaseline.SetValue(self.show_baseline)
            self.ToggleShowBaseline(event)

        self.reset_bitmap_buttons(CONST['ID_BASELINE_MODE'])

    def OnLandmarkMode(self, event):
        self.reset_bitmap_buttons(CONST['ID_LANDMARK_MODE'])

    def OnCalibrationMode(self, event):
        self.reset_bitmap_buttons(CONST['ID_CALIBRATION_MODE'])

    def OnImageCopy(self, event):
        img = self.objectViewer.CopyImage()
        wx.TheClipboard.Open()
        success = wx.TheClipboard.SetData(wx.BitmapDataObject(wx.BitmapFromImage(img)))
        wx.TheClipboard.Close()

    def OnImagePaste(self, event):
        img = wx.BitmapDataObject()
        wx.TheClipboard.Open()
        success = wx.TheClipboard.GetData(img)
        wx.TheClipboard.Close()
        #print img
        self.ConfirmClearLandmark()
        self.objectViewer.PasteImage(wx.ImageFromBitmap(img.GetBitmap()))
        #self.TwoDVie
        self.reset_bitmap_buttons()
        self.landmarkButton.SetValue(not self.landmarkButton.GetValue())
        self.reset_bitmap_buttons(CONST['ID_LANDMARK_MODE'])

    def OnImageLoad(self, event):
        wildcard = "JPEG file (*.jpg)|*.jpg|" \
                   "BMP file (*.bmp)|*.bmp|" \
                   "TIF file (*.tif)|*.tif|" \
                   "All files (*.*)|*.*"

        dialog_style = wx.OPEN

        selectfile_dialog = wx.FileDialog(self, "Select File to Load...", "", "", wildcard, dialog_style)
        if selectfile_dialog.ShowModal() != wx.ID_OK:
            return

        self.ConfirmClearLandmark()
        self.importpath = selectfile_dialog.GetPath()
        #( unc, pathname ) = splitunc( self.importpath )
        pathname = self.importpath
        #print pathname
        ( pathname, fname ) = os.path.split(pathname)

        #print pathname
        #print fname
        self.filename = fname
        ( fname, ext ) = os.path.splitext(fname)
        self.fileext = ext
        if ( self.forms['objname'].GetValue() == '' ):
            self.forms['objname'].SetValue(fname)
        self.TwoDViewer.LoadImageFile(self.importpath)
        self.reset_bitmap_buttons(CONST['ID_LANDMARK_MODE'])

    def set_object_image(self,wximg):
        if len(self.mdobject.image_list) > 0:
            self.mdobject.image_list[0].set_image_object(wximg)

    def OnMissingData(self, event):
        missing_lm = [LM_MISSING_VALUE, LM_MISSING_VALUE, LM_MISSING_VALUE]
        self.AppendLandmark(MdLandmark(missing_lm[:self.dimension]))
        return

    def ApplyCalibrationResult(self):
        #print "apply calib"
        self.reset_bitmap_buttons(CONST['ID_LANDMARK_MODE'])
        self.ppmm = self.objectViewer.pixels_per_millimeter
        #print "ppmm", ppmm
        # self.twoDppmm.SetValue( ppmm )
        temp_list = []
        temp_list[:] = self.landmark_list[:]
        self.ClearLandmarkList()
        for lm in temp_list:
            self.AppendLandmark( MdLandmark(lm.coords) )
            #chkShowCoordsInMillimeter()

    def ConfirmClearLandmark(self):
        if len(self.landmark_list) > 0:
            dlg = wx.MessageDialog(self, "Clear landmark data?", "Modan", wx.YES_NO | wx.YES_DEFAULT)
            res = dlg.ShowModal()
            if res == wx.ID_YES:
                self.ClearLandmarkList()

    def ToggleCoordsInMillimeter(self, event):
        #print "toggle coords"
        if ( self.chkCoordsInMillimeter.GetValue() ):
            if self.ppmm < 0:
                self.chkCoordsInMillimeter.SetValue(False)
                return
            self.coords_in_millimeter = True
            #print "true"
        else:
            self.coords_in_millimeter = False
            #print "false"
        self.ApplyCalibrationResult()

    def ToggleShowBaseline(self, event):
        #print "toggle show wireframe"
        self.show_baseline = self.chkShowBaseline.GetValue()
        #print self.show_wireframe
        if ( self.show_baseline ):
            #self.ThreeDViewer.ShowBaseline()
            self.objectViewer.ShowBaseline()
        else:
            #self.ThreeDViewer.HideWireframe()
            self.objectViewer.HideBaseline()
            #print "toggle wireframe"

    def ToggleShowWireframe(self, event):
        #print "toggle show wireframe"
        self.show_wireframe = self.chkShowWireframe.GetValue()
        #print self.show_wireframe
        if ( self.show_wireframe ):
            self.objectViewer.ShowWireframe()
            #self.TwoDViewer.ShowWireframe()
        else:
            self.objectViewer.HideWireframe()
            #self.TwoDViewer.HideWireframe()
            #print "toggle wireframe"

    def ToggleShowIndex(self, event):
        #print "toggle show index"
        self.show_index = self.chkShowIndex.GetValue()
        if ( self.show_index ):
            self.objectViewer.ShowIndex()
            #self.TwoDViewer.ShowIndex()
        else:
            self.objectViewer.HideIndex()
            #self.TwoDViewer.HideIndex()
            #print "toggle show index"

    def ToggleAutoRotate(self, event):
        self.auto_rotate = self.chkAutoRotate.GetValue()
        if ( self.auto_rotate ):
            self.objectViewer.BeginAutoRotate()
        else:
            self.objectViewer.EndAutoRotate()
            #print "toggle auto rotate"

    def SetDataset(self, dataset ):
        #print "set dataset"
        self.dataset = dataset
        self.has_dataset = True
        self.forms['dsname'].SetLabel(dataset.dsname)
        self.set_dimension(dataset.dimension)
        self.dataset.unpack_wireframe()
        self.edge_list = self.dataset.edge_list
        self.dataset.unpack_baseline()
        self.baseline_point_list = self.dataset.baseline_point_list
        self.AlignControls()
        #self.TwoDViewer.DrawToBuffer()

    def set_mdobject(self, mdobject):
        #print "set mdobject", mdobject
        #session = self.app.get_session()
        #print "session in setmodanobject:", session
        self.mdobject = mdobject

        self.forms['id'].SetLabel("%d" % mdobject.id)
        self.forms['objname'].SetLabel(mdobject.objname)
        self.forms['objdesc'].SetValue(mdobject.objdesc)


        #print str(mdobject.dataset_id)+":"+ds.dsname
        #print mdobject
        #self.forms['landmark_list'].Append( ( lm.lmseq, lm.xcoord, lm.ycoord, lm.zcoord ) )
        if len(self.mdobject.image_list) > 0:
            img = mdobject.image_list[0]
            self.TwoDViewer.SetImage(img.get_image_object())
            if img.ppmm > 0:
                self.TwoDViewer.pixels_per_millimeter = self.ppmm = img.ppmm
                self.coords_in_millimeter = True
                self.chkCoordsInMillimeter.SetValue(self.coords_in_millimeter)
                self.reset_bitmap_buttons(CONST['ID_LANDMARK_MODE'])

        #self.dataset = ds
        #self.edge_list.append( "aaa" )
        #print self.edge_list, self.dataset.edge_list

        #if len( self.wireframe.edge_list ) > 0:

        if len( self.mdobject.landmark_list ) == 0 and self.mdobject.landmark_str != '':
            self.mdobject.unpack_landmark()

        for lm in self.mdobject.landmark_list:
            #print lm.coords
            self.AppendLandmark(lm)
            #print lm, lm.lmseq
        #self.TwoDViewer.DrawToBuffer()

        #self.RefreshLinkList()
        #print "a"
        mo = MdObjectView(mdobject)
        #print "b"
        mo.move_to_center()

        if mdobject.dataset.dimension == 3:
            self.ThreeDViewer.SetSingleObject(mo)
            self.ThreeDViewer.baseline_point_list = self.dataset.baseline_point_list
            self.ThreeDViewer.edge_list = self.dataset.edge_list
        else:
            self.TwoDViewer.DrawToBuffer()

    def AppendWire(self, from_idx, to_idx):
        #print "append wire", from_idx, to_idx
        if from_idx < 0 or to_idx < 0:
            return
        self.is_wireframe_changed = True
        edge = [int(from_idx), int(to_idx)]
        edge.sort()
        self.edge_list.append(edge)
        self.dataset.edge_list = self.edge_list
        #print self.edge_list
        #print self.dataset.edge_list
        return

    def DeleteWire(self, from_idx, to_idx):
        self.is_wireframe_changed = True
        new_list = []
        delete_edge = [int(from_idx), int(to_idx)]
        delete_edge.sort(key=int)
        #print delete_edge
        for edge in self.edge_list:
            #print edge
            if delete_edge == edge:
                pass
            else:
                new_list.append(edge)
        self.dataset.edge_list = self.edge_list = new_list

    def ConfirmWireframeOrBaselineEdit(self):
        if self.is_confirmed_wireframe_or_baseline_edit:
            return wx.ID_YES
        msg_box = wx.MessageDialog(self,
                                   "Editing wireframe or baseline will affects all the objects in this dataset. Continue?",
                                   "Warning", \
                                   wx.YES_NO | wx.YES_DEFAULT | wx.CENTRE | wx.ICON_EXCLAMATION)
        ret = msg_box.ShowModal()
        if ret == wx.ID_YES:
            self.is_confirmed_wireframe_or_baseline_edit = True
        return ret

    def ClearWireframe(self):
        self.is_wireframe_changed = True
        self.dataset.edge_list = self.edge_list = []

    def SetBaseline(self, baseidx1, baseidx2, baseidx3=-1):
        #print "set baseline", baseidx1, baseidx2, baseidx3
        self.is_baseline_changed = True
        self.baseline_point_list = []
        self.baseline_point_list.append(baseidx1)
        self.baseline_point_list.append(baseidx2)
        if baseidx3 >= 0:
            self.baseline_point_list.append(baseidx3)
        self.dataset.baseline_point_list = self.baseline_point_list

    def ClearBaseline(self):
        self.is_baseline_changed = True
        self.dataset.baseline_point_list = self.baseline_point_list = []

    def AppendBaselinePoint(self, idx):
        #print "baseline point", idx
        self.is_baseline_changed = True
        #hit = False
        if not idx in self.baseline_point_list:
            self.baseline_point_list.append(idx)
        self.dataset.baseline_point_list = self.baseline_point_list

    def DeleteBaselinePoint(self, idx):
        self.is_baseline_changed = True
        new_list = []
        idx = int(idx)
        #print delete_edge
        for point in self.baseline_point_list:
            #print edge
            if int(point) == idx:
                pass
            else:
                new_list.append(point)
        self.baseline_point_list = new_list
        self.dataset.baseline_point_list = self.baseline_point_list

    def OnClose(self, event):
        if (self.modified):
            msg_box = wx.MessageDialog(self, "You may have modified something. Really close?", "Warning",
                                       wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE | wx.ICON_EXCLAMATION)
            result = msg_box.ShowModal()
            if ( result == wx.ID_YES ): self.Close()
        else:  # Didn't modified anything
            self.Close()

    def OnDelete(self, event):
        moid = int( self.forms['id'].GetLabel() )
        if moid > 0:
            msg_box = wx.MessageDialog(self, "Do you really want to delete?", "Warning",
                                       wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE | wx.ICON_EXCLAMATION)
            result = msg_box.ShowModal()
            if ( result == wx.ID_YES ):
                session = self.app.get_session()
                #for image in self.mdobject.image_list:
                #    session.delete(image)
                #for p in self.mdobject.property_list:
                #    session.delete( p )
                session.delete(self.mdobject)
                session.commit()
                #self.GetParent().Refresh()
                #print "object delete done"
                self.EndModal(wx.ID_EDIT)

    def OnSave(self, event):
        #self.object
        #print self.edge_list
        #print self.dataset.edge_list
        #return
        session = self.app.get_session()
        wx.BeginBusyCursor()
        ret = wx.ID_EDIT
        if self.mdobject:
            print "already have mdobject"
            mo = self.mdobject
            print self.mdobject, mo
        else:
            print "new mdobject"
            mo = self.mdobject = MdObject()
            mo.dataset_id = self.dataset.id
            session.add(mo)

        mo.objname = self.forms['objname'].GetValue()
        mo.objdesc = self.forms['objdesc'].GetValue()
        #mo.scale = self.forms['scale'].GetValue()
        mo.landmark_list = self.landmark_list[:]
        mo.pack_landmark()
        print self.mdobject, mo

        if self.TwoDViewer.has_image:
            if len(mo.image_list)==0:
                mo.image_list.append(MdImage())
            mo.image_list[0].set_image_object(self.TwoDViewer.origimg)
            mo.image_list[0].ppmm = self.ppmm
        #for i in range(len(self.dataset.groupname_list)):
        #    mo.group_list[i] = self.groupText[i].GetValue()
        #print "session in dialog_object", session

        #if mo not in session:

        self.frame.object_content_pane.SetObjectContent(mo)

        if self.is_wireframe_changed:
            self.dataset.pack_wireframe()
            ret = wx.ID_EDIT

        if self.is_baseline_changed:
            self.dataset.pack_baseline()
            ret = wx.ID_EDIT

        #    self.GetParent().objectContent.SetObjectContent(mo)
        session.commit()
        #session.close()
        wx.EndBusyCursor()
        self.EndModal(ret)
        #self.Close()

    def PasteFromClipboard(self, event):
        # if there're some landmarks already, confirm overwrite

        do = wx.TextDataObject()
        wx.TheClipboard.Open()
        success = wx.TheClipboard.GetData(do)
        wx.TheClipboard.Close()
        cbtext = ''
        if success:
            cbtext = do.GetText()
            #print cbtext
            if cbtext == '':
                return
            di = ModanDataImporter(text=cbtext)
            di.checkDataType()
            i = 1
            if ( self.forms['objname'].GetValue() == '' ):
                self.forms['objname'].SetValue(di.title)
            for d in ( di.grid ):
                xcoord = d[0]
                ycoord = d[1]
                zcoord = 0
                if ( len(d) > 2 ):
                    zcoord = d[2]
                self.AppendLandmark(i * 10, xcoord, ycoord, zcoord)
                #self.forms['landmark_list'].Append( [i*10] + d )
                i += 1
        self.RefreshThreeDViewer()
        #self.SetSize(self.GetClientSize())

        #self.forms['landmark_list'].Append( ['a', 'b', 'c', 'd', 'e'] )

    def AppendLandmark(self, landmark):
        #print "append landmark"
        coords = landmark.coords[:]
        is_missing_data = False
        if coords[0] == LM_MISSING_VALUE and coords[1] == LM_MISSING_VALUE:
            is_missing_data = True
        self.landmark_list.append(landmark)

        if self.coords_in_millimeter and self.ppmm > 0:
            coords = [ x / self.ppmm for x in coords ]

        nums = []
        for num in coords:
            if float(num) != int(num):
                num = math.floor( ( num * 1000 ) + 0.5 ) / 1000.0
            else:
                num = int(num)
            nums.append(num)
        if is_missing_data:
            self.forms['landmark_list'].Append([LM_MISSING_VALUE for n in nums])
        else:
            self.forms['landmark_list'].Append(nums)

    def AddCoord(self, event):
        #print "add coord"
        lm = [self.forms['xcoord'].GetValue(),self.forms['ycoord'].GetValue()]
        if self.dimension == 3:
            lm.append(self.forms['zcoord'].GetValue())
        #print lm
        self.AppendLandmark(MdLandmark(lm))
        #self.forms['landmark_list'].Append( [idx, x, y, z] )
        self.forms['xcoord'].SetValue('')
        self.forms['ycoord'].SetValue('')
        self.forms['zcoord'].SetValue('')
        self.forms['xcoord'].SetFocus()
        if self.dimension == 3:
            self.RefreshThreeDViewer()

    def OnLandmarkSelected(self, event):
        listctrl = self.forms['landmark_list']
        selected_idx_list = self.GetSelectedItemIndex(listctrl)
        if self.dimension == 3:
            self.ThreeDViewer.SelectLandmark(selected_idx_list)
            self.ThreeDViewer.Refresh(False)
        #event.Skip()

    def OnDoubleClick(self, event):
        listctrl = self.forms['landmark_list']
        selected_idx = listctrl.GetFocusedItem()
        self.forms['xcoord'].SetValue(listctrl.GetItem(selected_idx, 1).GetText())
        self.forms['ycoord'].SetValue(listctrl.GetItem(selected_idx, 2).GetText())
        self.forms['zcoord'].SetValue(listctrl.GetItem(selected_idx, 3).GetText())

    def DeleteLandmark(self, event):
        #for selected_landmark in self.SelectedItemText(self.forms['landmark_list']):
        #  del self.landmark_list[selected_landmark]
        #self.ClearLandmarkList()
        #self.modified = True
        pass

    def ClearLandmarkList(self):
        if len(self.landmark_list) > 0:
            self.forms['landmark_list'].DeleteAllItems()
            self.landmark_list = []
            #for title, uri in self.landmark_list.iteritems():
            #  self.forms['landmark_list'].Append( [title, uri] )

    def RefreshThreeDViewer(self):
        #print "refresh 3d view 1"
        #for lm in self.landmark_list:
        #    print lm.coords
        dummy_mdobject = MdObject()
        print "dummy object", dummy_mdobject
        dummy_mdobject.landmark_list = [ MdLandmark(x.coords) for x in self.landmark_list]
        #mo = mdobject.copy()
        dummy_mdobject.move_to_center()
        #print "refresh 3d view 2"
        #for lm in self.landmark_list:
        #    print lm.coords

        #print "refresh threed viewer", len( self.landmark_list), "landmarks"
        #print "refresh threed viewer", len( dummy_mdobject.landmark_list), "object landmarks"
        self.ThreeDViewer.SetSingleObject(dummy_mdobject)
        self.ThreeDViewer.OnDraw()
        self.ThreeDViewer.Refresh()
        if self.auto_rotate:
            self.ThreeDViewer.BeginAutoRotate()

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
        return rv
