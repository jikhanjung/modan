#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import time

import wx

from libpy.conf import ModanConf
from libpy.modan_dbclass import *
from libpy.dataimporter import ModanDataImporter
from gui.dialog_dataset import ModanDatasetDialog
from gui.opengltest import MdCanvas, OpenGLTestWin
from PIL import Image, ImageEnhance
import wx.lib.buttons as buttons

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

CONST = {}
CONST['ID_LANDMARK_MODE'] = 4003
CONST['ID_CALIBRATION_MODE'] = 4004
CONST['ID_LANDMARK_EDIT_MODE'] = 4005
CONST['ID_WIREFRAME_MODE'] = 4006
CONST['ID_WIREFRAME_EDIT_MODE'] = 4007
CONST['ID_BASELINE_MODE'] = 4008
CONST['ID_BASELINE_EDIT_MODE'] = 4009

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


class TestDlg(wx.Dialog):
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, 'test', size=DIALOG_SIZE)
        self.panel = panel = wx.Panel(self, -1)
        btn1 = wx.Button(panel, -1, '1')
        btn2 = wx.Button(panel, -1, '2')
        btn3 = wx.Button(panel, -1, '3')
        btn4 = wx.Button(panel, -1, '4')
        self.imgctl = ModanImageControl(panel, -1)
        sizer3 = wx.GridBagSizer()
        #sizer3.Add( btn3, pos=(0,0),flag=wx.EXPAND)
        sizer = wx.GridBagSizer()
        sizer.Add(btn1, pos=(0, 0), flag=wx.EXPAND)
        sizer.Add(btn2, pos=(1, 0), flag=wx.EXPAND)
        sizer.Add(btn3, pos=(0, 1), span=(2, 1), flag=wx.EXPAND)
        sizer.Add(btn4, pos=(2, 0), span=(1, 2), flag=wx.EXPAND)
        sizer.Add(self.imgctl, pos=(3, 0), flag=wx.EXPAND)
        self.imgctl.SetMinSize((640, 480))
        btn1.SetMinSize((300, 100))
        btn2.SetMinSize((300, 100))
        #btn3.SetMinSize((640,480))
        #sizer3.SetMinSize((640,480))
        btn4.SetMinSize((640, 22))
        panel.SetSizer(sizer)
        panel.Fit()


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


class ModanImageControl(wx.Window):
    def __init__(self, parent, id):
        wx.Window.__init__(self, parent, id)
        self.parent_dlg = parent.GetParent()
        #self.Bind( wx.EVT_MOUSEWHEEL, self.OnWheel )
        #self.LoadBitmap( wx.BitmapFromImage(self.img) )
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        # should be left click
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        #self.Bind( wx.EVT_LEAVE_WINDOW, self.OnMouseLeave )
        self.SetBackgroundColour('#aaaaaa')
        #self.SetCursor( wx.StockCursor(wx.CURSOR_CROSS ) )
        self.SetSize((640, 480))
        self.in_motion = False
        self.is_dragging_image = False
        self.is_dragging_landmark = False
        self.is_dragging_wire = False
        self.is_dragging_baseline = False
        self.is_calibrating = False
        self.show_index = True
        self.show_wireframe = True
        self.show_baseline = False
        self.pixels_per_millimeter = -1
        self.SetMode(CONST['ID_LANDMARK_MODE'])
        self.ClearImage()
        #self.currimg = self.img = self.origimg = wx.EmptyImage(640,480)
        #self.buffer = wx.BitmapFromImage( self.img )
        #self.RefreshImage()
        self.has_image = False
        #self.LoadImageFile( "trilobite1.jpg" )
        self.cmd_down = False
        self.alt_down = False
        self.temp_landmark_list = []
        self.deleted_landmark_list = []
        self.begin_wire_idx = -1
        self.end_wire_idx = -1
        self.begin_baseline_idx = -1
        self.end_baseline_idx = -1
        self.cursor_on_idx = -1
        self.hovering_edge = []

    def EndAutoRotate(self):
        return

    def BeginAutoRotate(self):
        return

    def SetMode(self, mode):
        #print "set mode:", mode
        self.mode = mode
        if mode == CONST['ID_LANDMARK_MODE']:
            self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
            self.curr_landmark_idx = -1
        elif mode == CONST['ID_CALIBRATION_MODE']:
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
        elif mode == CONST['ID_LANDMARK_EDIT_MODE']:
            self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        elif mode == CONST['ID_WIREFRAME_MODE']:
            #print "wireframe"
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
        elif mode == CONST['ID_WIREFRAME_EDIT_MODE']:
            self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        elif mode == CONST['ID_BASELINE_MODE']:
            #print "baseline"
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
        elif mode == CONST['ID_BASELINE_EDIT_MODE']:
            self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        return

    def ClearImage(self):
        self.has_image = False
        img = wx.EmptyImage(640, 480)
        img.SetRGBRect(wx.Rect(0, 0, 640, 480), 128, 128, 128)
        self.SetImage(img, True)
        self.buffer = wx.BitmapFromImage(self.img)
        return

    def SetImage(self, img, empty_image=False):
        if not empty_image:
            self.has_image = True
        self.currimg = self.img = self.origimg = img
        #print "set image", img

        self.ResetImage()

    def LoadImageFile(self, filename):
        img = wx.Image(filename)
        self.SetImage(img)
        #print filename
        #self.currimg = self.img = self.origimg = wx.Image( filename )
        #print self.img.ClassName
        #self.RefreshImage()
        return

    def OnRightDown(self, event):
        # should be a callback function
        if self.mode == CONST['ID_LANDMARK_EDIT_MODE']:
            confirmDlg = wx.MessageDialog(self, "Delete landmark?", "Modan", wx.YES_NO | wx.YES_DEFAULT)
            ret = confirmDlg.ShowModal()
            if ret != wx.ID_YES:
                return
            #print self.temp_landmark_list
            deleted_landmark = self.temp_landmark_list.pop(self.curr_landmark_idx - 1)
            #print self.temp_landmark_list
            self.deleted_landmark_list.append(( self.curr_landmark_idx, deleted_landmark ))
            parent = self.parent_dlg
            parent.ClearLandmarkList()
            for i in range(len(self.temp_landmark_list)):
                lm = self.temp_landmark_list[i]
                parent.AppendLandmark(MdLandmark(lm.coords))
            self.DrawToBuffer()
        elif self.mode == CONST['ID_WIREFRAME_EDIT_MODE'] and self.hovering_edge != []:
            confirmDlg = wx.MessageDialog(self, "Delete this edge?", "Modan", wx.YES_NO | wx.YES_DEFAULT)
            ret = confirmDlg.ShowModal()
            if ret != wx.ID_YES:
                return
            self.parent_dlg.DeleteWire(self.hovering_edge[0], self.hovering_edge[1])
            self.DrawToBuffer()
            self.SetMode(CONST['ID_WIREFRAME_MODE'])
        else:
            self.is_dragging_image = True
            self.CaptureMouse()
            self.x, self.y = self.lastx, self.lasty = event.GetPosition()

    def OnRightUp(self, event):
        if self.is_dragging_image:
            self.EndDragging(event)

    def OnKeyDown(self, event):
        self.cmd_down = event.CmdDown()
        self.alt_down = event.AltDown()

    #    if self.alt_down and self.mode == ID_2D_LANDMARK_EDIT_MODE:
    #      self.SetCursor()

    def OnKeyUp(self, event):
        self.cmd_down = event.CmdDown()
        self.alt_down = event.AltDown()

    def OnLeftDown(self, event):
        #print "down"
        if not self.has_image:
            return
        if self.mode == CONST['ID_LANDMARK_MODE']:
            if self.img_x < 0 or self.img_y < 0:
                return
            self.parent_dlg.AppendLandmark(MdLandmark([self.img_x, self.img_y]))
            self.DrawToBuffer()
        elif self.mode == CONST['ID_CALIBRATION_MODE']:
            self.x, self.y = self.lastx, self.lasty = event.GetPosition()
            self.calib_x1, self.calib_y1 = self.x, self.y
            self.calib_x2, self.calib_y2 = self.x, self.y
            #self.calib_y1 = self.y
            self.DrawToBuffer()
            self.is_calibrating = True
            self.CaptureMouse()
        elif self.mode == CONST['ID_LANDMARK_EDIT_MODE']:
            self.x, self.y = self.lastx, self.lasty = event.GetPosition()
            self.is_dragging_landmark = True
            self.CaptureMouse()
        elif self.mode == CONST['ID_WIREFRAME_EDIT_MODE']:
            self.x, self.y = self.lastx, self.lasty = event.GetPosition()
            self.is_dragging_wire = True
            self.CaptureMouse()
        elif self.mode == CONST['ID_BASELINE_EDIT_MODE']:
            self.x, self.y = self.lastx, self.lasty = event.GetPosition()
            hit, lm_idx = self.IsCursorOnLandmark()
            if hit:
                self.begin_baseline_idx = lm_idx
                self.is_dragging_baseline = True
                self.CaptureMouse()


    def IsImageInside(self):
        x1 = y1 = 0
        x2 = self.origimg.GetWidth()
        y2 = self.origimg.GetHeight()
        scr_x, scr_y = self.ImageXYtoScreenXY(x1, y1)
        #print scr_x, scr_y
        if scr_x > self.GetSize().width or scr_y > self.GetSize().height:
            #print "not inside 1"
            return False
        scr_x, scr_y = self.ImageXYtoScreenXY(x2, y2)
        #print scr_x, scr_y
        if scr_x < 0 or scr_y < 0:
            #print "not inside 2"
            return False
        return True


    def OnLeftUp(self, event):
        #print "up"
        if self.is_dragging_image:
            self.EndDragging(event)
        elif self.is_calibrating:
            self.EndCalibration(event)
        elif self.is_dragging_landmark:
            self.is_dragging_landmark = False
            self.ReleaseMouse()
        elif self.is_dragging_wire:
            self.x, self.y = event.GetPosition()
            hit, lm_idx = self.IsCursorOnLandmark()
            if hit:
                self.parent_dlg.AppendWire(self.begin_wire_idx, self.end_wire_idx)
            self.is_dragging_wire = False
            self.begin_wire_idx = self.end_wire_idx
            self.end_wire_idx = -1
            self.ReleaseMouse()
        elif self.is_dragging_baseline:
            self.x, self.y = event.GetPosition()
            hit, lm_idx = self.IsCursorOnLandmark()
            if hit:
                parent = self.parent_dlg
                if lm_idx == self.begin_baseline_idx:
                    if len(parent.baseline_point_list) == 2:
                        parent.ClearBaseline()
                    parent.AppendBaselinePoint(lm_idx)
                else:
                    parent.ClearBaseline()
                    parent.AppendBaselinePoint(self.begin_baseline_idx)
                    parent.AppendBaselinePoint(lm_idx)

            self.is_dragging_baseline = False
            self.begin_baseline_idx = self.end_baseline_idx
            self.end_baseline_idx = -1
            self.ReleaseMouse()

            #self.SetMode( ID_2D_LANDMARK_MODE )
            #self.SetCursor( wx.StockCursor( wx.CURSOR_CROSS ) )

    def EndCalibration(self, event):
        if self.is_calibrating:
            self.is_calibrating = False
            self.in_motion = False
            self.x, self.y = event.GetPosition()
            self.calib_x2, self.calib_y2 = self.x, self.y
            #self.calib_y2 = self.y
            self.ReleaseMouse()
            #print self.calib_x1, self.calib_y1, self.calib_x2, self.calib_y2
            #x2 = float( self.calib_x2 - self.calib_x1 ) ** 2.0
            #y2 = float( self.calib_y2 - self.calib_y1 ) ** 2.0
            dist = self.get_distance(self.calib_x1, self.calib_y1, self.calib_x2, self.calib_y2)
            #dist = ( ( self.calib_x2 - self.calib_x1 ) ** 2 + ( self.calib_y2 - self.calib_y1 ) ** 2 ) ** 1/2
            actual_dist = dist / self.zoom
            #print x2, y2, dist, actual_dist
            #print

            calibDlg = UnitCalibrationDlg(self, -1)
            res = calibDlg.ShowModal()
            if res == wx.ID_OK:
                length = calibDlg.GetValue()
                self.pixels_per_millimeter = float(actual_dist) / float(length)
                #print self.pixels_per_millimeter, "pixels in 1 mm"
            calibDlg.Destroy()
            self.DrawToBuffer()
            self.parent_dlg.ApplyCalibrationResult()
            self.SetMode(CONST['ID_LANDMARK_MODE'])
            #self.mode = ID_2D_LANDMARK_MODE
            #self.Refresh(False)

    def EndDragging(self, event):
        if self.is_dragging_image:
            self.in_motion = False
            self.is_dragging_image = False
            self.x, self.y = event.GetPosition()
            self.img_left = self.img_left + (self.x - self.lastx)
            self.img_top = self.img_top + self.y - self.lasty
            self.lastx = self.x
            self.lasty = self.y
            self.ReleaseMouse()
            #self.AdjustObjectRotation()
            self.Refresh(False)

    def OnMotion(self, event):
        t0 = time.time()
        #print self.mode
        #print "motion"
        self.x, self.y = event.GetPosition()
        #self.x = max( 0, self.x )
        #self.x = min( self.GetSize().width, self.x )
        #self.y = max( 0, self.y )
        #self.y = min( self.GetSize().height, self.y )

        if self.is_dragging_image:  #event.Dragging() and event.LeftIsDown():
            #print "img_left", self.img_left
            #print "img_top", self.img_top
            #print "self.x", self.x
            #print "self.y", self.y
            #print "self.lastx", self.lastx
            #print "self.lasty", self.lasty
            if not self.in_motion:
                self.in_motion = True
                #self.SetCursor( wx.StockCursor( wx.CURSOR_HAND ) )
            old_left = self.img_left
            old_top = self.img_top
            self.img_left = self.img_left + self.x - self.lastx
            self.img_top = self.img_top + self.y - self.lasty
            if not self.IsImageInside():
                self.img_left = old_left
                self.img_top = old_top
                return
            self.crop_x1, self.crop_y1 = self.ScreenXYtoImageXY(0, 0)
            self.crop_x2, self.crop_y2 = self.ScreenXYtoImageXY(self.GetSize().width, self.GetSize().height)
            #if crop_x1 <
            self.lastx = self.x
            self.lasty = self.y
            self.RefreshImage()
        elif self.is_calibrating:
            self.calib_x2, self.calib_y2 = self.x, self.y
            #self.calib_x2 = self.x
            #self.calib_y2 = self.y
            #self.DrawToBuffer()
        elif self.mode == CONST['ID_LANDMARK_MODE']:
            hit, lm_idx = self.IsCursorOnLandmark()
            if hit:
                self.SetMode(CONST['ID_LANDMARK_EDIT_MODE'])
                #self.cursor_on_idx = lm_idx
                self.curr_landmark_idx = lm_idx
                self.temp_landmark_list = []
                self.temp_landmark_list[::] = self.parent_dlg.landmark_list[::]
        elif self.mode == CONST['ID_LANDMARK_EDIT_MODE']:

            if self.is_dragging_landmark:
                parent = self.parent_dlg
                parent.ClearLandmarkList()
                for i in range(len(self.temp_landmark_list)):
                    lm = self.temp_landmark_list[i]
                    if i != self.curr_landmark_idx - 1:
                        parent.AppendLandmark(MdLandmark(lm.coords))
                    else:
                        parent.AppendLandmark( MdLandmark( [ lm.coords[0] + math.floor(( self.x - self.lastx) / self.zoom + 0.5),
                                              lm.coords[1] + math.floor(( self.y - self.lasty ) / self.zoom + 0.5) ]))
            hit, lm_idx = self.IsCursorOnLandmark()
            if not hit:
                self.SetMode(CONST['ID_LANDMARK_MODE'])
                self.curr_landmark_idx = -1
        elif self.mode == CONST['ID_WIREFRAME_MODE']:
            #print "wireframe_mode"
            hit, lm_idx = self.IsCursorOnLandmark()
            if hit:
                self.SetMode(CONST['ID_WIREFRAME_EDIT_MODE'])
                self.begin_wire_idx = lm_idx
                self.hovering_edge = []
            else:
                #print "0"
                hit, edge = self.IsCursorOnWireframe()
                #print "result:", hit, edge
                if hit:
                    self.SetMode(CONST['ID_WIREFRAME_EDIT_MODE'])
                    self.hovering_edge = edge
                    #print "edge:",edge
                else:
                    self.hovering_edge = []
                    #self.DrawToBuffer()
        elif self.mode == CONST['ID_WIREFRAME_EDIT_MODE']:
            #print "wireframe_edit_mode"
            hit, lm_idx = self.IsCursorOnLandmark()
            #print hit, lm_idx, self.begin_wire_idx, self.end_wire_idx
            if not hit:
                #print "not hit"
                self.end_wire_idx = -1
                if self.is_dragging_wire:
                    self.wire_to_x = self.x
                    self.wire_to_y = self.y
                else:
                    hit, edge = self.IsCursorOnWireframe()
                    if hit:
                        self.hovering_edge = edge
                    else:
                        self.SetMode(CONST['ID_WIREFRAME_MODE'])
                        self.begin_wire_idx = -1
                        # draw dangling wire
            else:
                #print "begin_wire", self.begin_wire_idx, "curr_idx", lm_idx
                if self.begin_wire_idx == -1:
                    self.begin_wire_idx = lm_idx
                self.hovering_edge = []
                if self.begin_wire_idx != lm_idx:
                    #to_lm = self.parent_dlg.landmark_list[lm_idx]
                    #self.wire_to_x, self.wire_to_y = self.ImageXYtoScreenXY(to_lm[1],to_lm[2])
                    self.end_wire_idx = lm_idx
        elif self.mode == CONST['ID_BASELINE_MODE']:
            hit, lm_idx = self.IsCursorOnLandmark()
            if hit:
                self.SetMode(CONST['ID_BASELINE_EDIT_MODE'])
                self.begin_baseline_idx = lm_idx
            else:
                self.begin_baseline_idx = -1
        elif self.mode == CONST['ID_BASELINE_EDIT_MODE']:
            hit, lm_idx = self.IsCursorOnLandmark()
            #print hit, lm_idx, self.begin_wire_idx, self.end_wire_idx
            if not hit:
                self.end_baseline_idx = -1
                if self.is_dragging_baseline:
                    self.baseline_to_x = self.x
                    self.baseline_to_y = self.y
                else:
                    self.SetMode(CONST['ID_BASELINE_MODE'])
                    self.baseline_wire_idx = -1
                    # draw dangling wire
            else:
                if self.begin_baseline_idx != lm_idx:
                    #to_lm = self.parent_dlg.landmark_list[lm_idx]
                    #self.baseline_to_x, self.baseline_to_y = self.ImageXYtoScreenXY(to_lm[1],to_lm[2])
                    self.end_baseline_idx = lm_idx
        self.img_x, self.img_y = self.ScreenXYtoImageXY(self.x, self.y)
        #print "on motion 1", time.time() - t0
        self.DrawToBuffer()
        #print "on motion 2", time.time() - t0

    def get_dist_criterion(self):
        dist_criterion = 5.0
        if self.zoom > 2:
            dist_criterion *= ( 1 + self.zoom ** 2 / 10 )
        return dist_criterion


    def IsCursorOnLandmark(self):
        t0 = time.time()
        i = 1
        found = False
        for lm in self.parent_dlg.landmark_list:
            x, y = self.ImageXYtoScreenXY(lm.coords[0], lm.coords[1])
            dist = self.get_distance(x, y, self.x, self.y)
            #print i, "dist", dist
            if dist < self.get_dist_criterion():
                found = True
                #print "landmark", i
                break
            i += 1
        #print "iscursoronlandmark", time.time() - t0
        return found, i

    def IsCursorOnWireframe(self):
        #print "1"
        i = 1
        found = False

        edge_list = self.parent_dlg.edge_list
        landmark_list = self.parent_dlg.landmark_list

        #print "2"
        dist_criterion = self.get_dist_criterion()

        found_edge = []
        #print "3", dist_criterion
        i = 1
        for edge in edge_list:
            #print "edge", i, edge
            #print vertex
            vfrom = int(edge[0]) - 1
            vto = int(edge[1]) - 1
            ( x1, y1 ) = self.ImageXYtoScreenXY(landmark_list[vfrom].coords[0], landmark_list[vfrom].coords[1])
            ( x2, y2 ) = self.ImageXYtoScreenXY(landmark_list[vto].coords[0], landmark_list[vto].coords[1])
            max_x = max(x1, x2)
            min_x = min(x1, x2)
            max_y = max(y1, y2)
            min_y = min(y1, y2)
            #print "5", x1, y1, x2, y2
            #print "6", self.x, self.y, max_x, min_x, max_y, min_y

            if ( self.x > ( max_x + dist_criterion ) ) or ( self.x < min_x - dist_criterion ) or (
                self.y > max_y + dist_criterion ) or ( self.y < min_y - dist_criterion ):
                i += 1
                continue
            #print "7"
            #print vfrom, vto, len( landmark_list )\
            vec = [x2 - x1, y2 - y1]
            curr_pos = [self.x - x1, self.y - y1]
            ab = curr_pos[0] * vec[0] + curr_pos[1] * vec[1]
            abs_b2 = vec[0] ** 2.0 + vec[1] ** 2.0
            c = [( ab / abs_b2 ) * vec[0], ( ab / abs_b2 ) * vec[1]]
            dist = self.get_distance(c[0], c[1], curr_pos[0], curr_pos[1])
            #print "projection:", c[0], c[1], "from", vec[0], vec[1]
            #print "curr", curr_pos[0], curr_pos[1]
            #print "dist:", dist, dist_criterion


            if dist < dist_criterion:
                found = True
                found_edge = edge
                break
            i += 1
        return found, found_edge

    def get_distance_from_line(self, x1, y1, from_x, from_y, to_x, to_y):
        pass
        #self.img_x = math.floor( ( self.x - self.img_left ) / self.zoom + 0.5 )
        #self.img_y = math.floor( ( self.y - self.img_top) / self.zoom + 0.5 )
        #print self.x, self.y, self.img_x, self.img_y

    def get_distance(self, x1, y1, x2, y2):
        x2 = float(x2 - x1) ** 2.0
        y2 = float(y2 - y1) ** 2.0
        dist = ( x2 + y2 ) ** 0.5
        return dist


    def DrawToBuffer(self):
        #print "draw to buffer"
        t0 = time.time()
        zoomed_image = self.currimg
        #print "prepare image", time.time() - t0

        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        dc.SetBackground(wx.GREY_BRUSH)
        dc.Clear()
        left = self.img_left
        top = self.img_top
        if left < 0:
            left = 0
        if top < 0:
            top = 0
        #print "image wxh", zoomed_image.GetWidth(), zoomed_image.GetHeight()
        #print top, left
        dc.DrawBitmap(wx.BitmapFromImage(zoomed_image), left, top)
        dc.SetPen(wx.Pen("red", 1))
        #dc.SetBrush(wx.RED_BRUSH)
        dc.SetTextForeground(wx.RED)
        idxFont = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
        if self.is_calibrating:
            dc_x1, dc_y1 = self.calib_x1, self.calib_y1
            dc_x2, dc_y2 = self.calib_x2, self.calib_y2
            #print dc_x1, dc_y1, dc_x2, dc_y2
            #print self.calib_x1, self.calib_y1, self.calib_x2, self.calib_y2
            dc.SetPen(wx.Pen("red", 1))
            dc.DrawCircle(dc_x1, dc_y1, 3)
            dc.DrawCircle(dc_x2, dc_y2, 3)
            dc.DrawLine(dc_x1, dc_y1, dc_x2, dc_y2)

        landmark_list = self.parent_dlg.landmark_list

        dc.SetTextForeground(wx.BLUE)
        dc.SetPen(wx.Pen("blue", 3))
        if self.is_dragging_baseline:
            if self.mode == CONST['ID_BASELINE_EDIT_MODE'] and self.begin_baseline_idx >= 0:
                from_lm = landmark_list[self.begin_baseline_idx - 1]
                baseline_from_x, baseline_from_y = self.ImageXYtoScreenXY(from_lm.coords[0], from_lm.coords[1])
                if self.end_baseline_idx >= 0:
                    to_lm = landmark_list[self.end_baseline_idx - 1]
                    baseline_to_x, baseline_to_y = self.ImageXYtoScreenXY(to_lm.coords[0], to_lm.coords[1])
                else:
                    baseline_to_x = self.x
                    baseline_to_y = self.y
                dc.DrawLine(baseline_from_x, baseline_from_y, baseline_to_x, baseline_to_y)
                dc.DrawText("(0,0)", baseline_from_x - 5, baseline_from_y + 8)
                if self.end_baseline_idx >= 0:
                    dc.DrawText("(0,1)", baseline_to_x - 5, baseline_to_y + 8)
        elif self.show_baseline:
            parent = self.parent_dlg
            basestr = ["(0,0)", "(0,1)"]
            i = 0
            line_coords = []
            #print parent.baseline_point_list
            for idx in parent.baseline_point_list:
                if idx > len(landmark_list):
                    pass
                else:
                    lm = landmark_list[idx - 1]
                    dc_x1, dc_y1 = self.ImageXYtoScreenXY(lm.coords[0], lm.coords[1])
                    dc.DrawText(basestr[i], dc_x1 - 5, dc_y1 + 8)
                    line_coords.append(dc_x1)
                    line_coords.append(dc_y1)
                i += 1
            if len(line_coords) == 4:
                dc.DrawLine(line_coords[0], line_coords[1], line_coords[2], line_coords[3])

        dc.SetPen(wx.Pen("red", 1))
        dc.SetTextForeground(wx.RED)

        if self.show_wireframe:
            edge_list = self.parent_dlg.edge_list
            for vertex in edge_list:
                #print vertex
                if vertex == self.hovering_edge:
                    dc.SetPen(wx.Pen("red", 3))
                else:
                    dc.SetPen(wx.Pen("red", 1))
                vfrom = int(vertex[0]) - 1
                vto = int(vertex[1]) - 1
                #print vfrom, vto, len( landmark_list )
                if vfrom > len(landmark_list) - 1 or vto > len(landmark_list) - 1:
                    #print "out of bound"
                    continue
                else:
                    #print "draw wire"
                    lm_from = landmark_list[vfrom].coords
                    lm_to = landmark_list[vto].coords
                    dc_x1, dc_y1 = self.ImageXYtoScreenXY(lm_from[0], lm_from[1])
                    dc_x2, dc_y2 = self.ImageXYtoScreenXY(lm_to[0], lm_to[1])
                    dc.DrawLine(dc_x1, dc_y1, dc_x2, dc_y2)

        if self.mode == CONST['ID_WIREFRAME_EDIT_MODE'] and self.begin_wire_idx >= 0:
            #print self.begin_wire_idx, self.end_wire_idx
            if self.is_dragging_wire:
                from_lm = self.parent_dlg.landmark_list[self.begin_wire_idx - 1]
                wire_from_x, wire_from_y = self.ImageXYtoScreenXY(from_lm.coords[0], from_lm.coords[1])
                if self.end_wire_idx >= 0:
                    to_lm = self.parent_dlg.landmark_list[self.end_wire_idx - 1]
                    wire_to_x, wire_to_y = self.ImageXYtoScreenXY(to_lm.coords[0], to_lm.coords[1])
                else:
                    wire_to_x = self.x
                    wire_to_y = self.y
                dc.DrawLine(wire_from_x, wire_from_y, wire_to_x, wire_to_y)
        #self.Refresh(False)

        i = 1
        #print "curr:", self.curr_landmark_idx
        for lm in landmark_list:
            #print "i", i
            if lm.coords[0] == LM_MISSING_VALUE and lm.coords[1] == LM_MISSING_VALUE:
                continue
            radius = 4
            dc.SetPen(wx.Pen("red", 1))
            if self.begin_wire_idx == i or self.end_wire_idx == i or self.curr_landmark_idx == i:
                radius = 6
            if self.begin_baseline_idx == i or self.end_baseline_idx == i:
                #print i, self.begin_baseline_idx
                dc.SetPen(wx.Pen("blue", 1))
                radius = 6
            dc_x, dc_y = self.ImageXYtoScreenXY(lm.coords[0], lm.coords[1])  #
            #dc_x = math.floor( lm[1] * self.zoom + 0.5 ) + self.img_left
            #dc_y = math.floor( lm[2] * self.zoom + 0.5 ) + self.img_top
            dc.DrawCircle(dc_x, dc_y, int(radius))
            #print dc_x, dc_y
            #dc.DrawPoint( dc_x, dc_y )
            if self.show_index:
                dc.DrawText(str(i), dc_x + 5, dc_y - 8)
            i += 1


        # draw scale bar
        if self.pixels_per_millimeter > 0:
            MAX_SCALEBAR_SIZE = 120
            bar_width = float(self.pixels_per_millimeter) * self.zoom
            actual_length = 1.0
            while bar_width > MAX_SCALEBAR_SIZE:
                bar_width /= 10
                actual_length /= 10
            while bar_width < MAX_SCALEBAR_SIZE:
                if bar_width * 10 < MAX_SCALEBAR_SIZE:
                    bar_width *= 10
                    actual_length *= 10
                else:
                    if bar_width * 5 < MAX_SCALEBAR_SIZE:
                        bar_width *= 5
                        actual_length *= 5
                    elif bar_width * 2 < MAX_SCALEBAR_SIZE:
                        bar_width *= 2
                        actual_length *= 2
                    break
            bar_width = int(math.floor(bar_width + 0.5))
            x = self.GetSize().width - 15 - ( bar_width + 20 )
            y = self.GetSize().height - 15 - 30
            dc.SetPen(wx.Pen('black', 1))
            dc.SetTextForeground(wx.BLACK)
            dc.DrawRectangle(x, y, bar_width + 20, 30)
            x += 10
            y += 20
            dc.DrawLine(x, y, x + bar_width, y)
            dc.DrawLine(x, y - 5, x, y + 5)
            dc.DrawLine(x + bar_width, y - 5, x + bar_width, y + 5)
            length_text = str(actual_length) + " mm"
            #print length_text, len( length_text )
            dc.DrawText(length_text, x + int(math.floor(float(bar_width) / 2.0 + 0.5)) - len(length_text) * 4, y - 15)

    def SetWireframe(self, wireframe):
        self.wireframe = wireframe

    def CropImage(self, image):
        self.crop_x1 = max(self.crop_x1, 0)
        self.crop_x2 = min(self.crop_x2, image.GetWidth())
        self.crop_y1 = max(self.crop_y1, 0)
        self.crop_y2 = min(self.crop_y2, image.GetHeight())
        rect = wx.Rect(self.crop_x1, self.crop_y1, self.crop_x2 - self.crop_x1, self.crop_y2 - self.crop_y1)
        cropped_image = image.GetSubImage(rect)
        #print "crop:", cropped_image.GetWidth(), cropped_image.GetHeight()
        return cropped_image


    def OnPaint(self, event):
        #print "OnPaint"
        dc = wx.BufferedPaintDC(self, self.buffer)
        #dc.DrawBitmap( wx.BitmapFromImage( self.currimg ), img_left, img_top, True )
        #dc.DrawCircle( 200,200,100)
        #dc.WriteBitmap( wx.BitmapFromImage( self.img ), 0, 0 )

    def OnMouseEnter(self, event):
        #wx.StockCursor(wx.CURSOR_CROSS)
        self.SetFocus()

    #def OnMouseLeave(self, event):
    #  wx.StockCursor(wx.CURSOR_ARROW)

    def OnWheel(self, event):
        #print "on wheel"
        if not self.has_image:
            return
        rotation = event.GetWheelRotation()
        #curr_scr_x, curr_scr_y = event.GetPosition()
        self.ModifyZoom(rotation)

    def ModifyZoom(self, rotation):
        curr_scr_x = int(self.GetSize().width / 2)
        curr_scr_y = int(self.GetSize().height / 2)

        #curr_img_x = int( math.floor( ( ( curr_scr_x - self.img_left ) / self.zoom ) + 0.5 ) )
        #curr_img_y = int( math.floor( ( ( curr_scr_y - self.img_top ) / self.zoom ) + 0.5 ) )

        old_zoom = self.zoom
        curr_img_x, curr_img_y = self.ScreenXYtoImageXY(curr_scr_x, curr_scr_y)

        ZOOM_MAX = 10
        ZOOM_MIN = 0.1
        if self.zoom < 1:
            factor = 0.5
        else:
            factor = int(self.zoom)
        self.zoom += 0.1 * factor * rotation / ( ( rotation ** 2 ) ** 0.5 )
        self.zoom = min(self.zoom, ZOOM_MAX)
        self.zoom = max(self.zoom, ZOOM_MIN)
        #print "zoom", self.zoom
        old_left = self.img_left
        old_top = self.img_top
        self.img_left = int(math.floor(curr_scr_x - curr_img_x * self.zoom + 0.5))
        self.img_top = int(math.floor(curr_scr_y - curr_img_y * self.zoom + 0.5))
        #print "img pos", self.img_left, self.img_top
        if not self.IsImageInside():
            self.img_left = old_left
            self.img_top = old_top
            self.zoom = old_zoom
            return

        self.crop_x1, self.crop_y1 = self.ScreenXYtoImageXY(0, 0)
        self.crop_x2, self.crop_y2 = self.ScreenXYtoImageXY(self.GetSize().width, self.GetSize().height)
        #print crop_x1, crop_y1, crop_x2, crop_y2
        self.RefreshImage()

    def RefreshImage(self):
        image = self.origimg
        t0 = time.time()
        cropped_image = self.CropImage(image)
        #print "crop", time.time() - t0
        #adjusted_image = self.AdjustBrightnessAndContrast( cropped_image )
        adjusted_image = cropped_image
        #print "b/c", time.time() - t0
        zoomed_image = self.ApplyZoom(adjusted_image)
        #print "zoom", time.time() - t0
        self.currimg = zoomed_image
        self.DrawToBuffer()

    def ScreenXYtoImageXY(self, x, y):
        new_x = int(math.floor(( ( x - self.img_left ) / self.zoom ) + 0.5))
        new_y = int(math.floor(( ( y - self.img_top  ) / self.zoom ) + 0.5))
        #print "screenxy", x, y, "toimagexy", new_x, new_y, "img left&top", self.img_left, self.img_top
        return new_x, new_y

    def ImageXYtoScreenXY(self, x, y):
        x = float(x)
        y = float(y)
        new_x = int(math.floor(( x * self.zoom + self.img_left ) + 0.5))
        new_y = int(math.floor(( y * self.zoom + self.img_top  ) + 0.5))
        return new_x, new_y

    def ApplyZoom(self, image):
        w = int(image.GetWidth() * self.zoom)
        h = int(image.GetHeight() * self.zoom)
        zoomed_image = image.Scale(w, h)
        return zoomed_image

    def AdjustBrightnessAndContrast(self, image):
        #print "brightness, contrast"
        img = imagetopil(image)
        br_enhancer = ImageEnhance.Brightness(img)
        new_img = br_enhancer.enhance(self.brightness_adjustment)
        cont_enhancer = ImageEnhance.Contrast(new_img)
        new_img = cont_enhancer.enhance(self.contrast_adjustment)
        new_wximg = piltoimage(new_img)
        return new_wximg

    def SetBrightness(self, bright):
        if bright <= 0:
            bright /= 100.0 * 2
        else:
            bright /= 100.0 * 2
        new_brightness = bright + 1.0
        self.brightness_adjustment = new_brightness
        self.RefreshImage()

    def SetContrast(self, contrast):
        if contrast <= 0:
            contrast /= 100.0 * 2
        else:
            contrast /= 100.0 * 2
        new_contrast = contrast + 1.0
        self.contrast_adjustment = new_contrast
        self.RefreshImage()

    def CopyImage(self):
        return self.origimg

    def PasteImage(self, image):
        self.SetImage(image)  #self.origimg = image

    def ShowWireframe(self):
        self.show_wireframe = True
        self.DrawToBuffer()
        #self.OnDraw()

    def HideWireframe(self):
        self.show_wireframe = False
        self.DrawToBuffer()
        #self.OnDraw()

    def ShowBaseline(self):
        self.show_baseline = True
        self.DrawToBuffer()
        #self.OnDraw()

    def HideBaseline(self):
        self.show_baseline = False
        self.DrawToBuffer()
        #self.OnDraw()

    def ShowIndex(self):
        self.show_index = True
        self.DrawToBuffer()
        #self.OnDraw()

    def HideIndex(self):
        self.show_index = False
        self.DrawToBuffer()
        #self.OnDraw()


    def ResetImage(self):
        #print "refresh_img", self.origimg
        img_w = self.origimg.GetWidth()
        img_h = self.origimg.GetHeight()
        self_w = self.GetSize().width
        self_h = self.GetSize().height
        #print img_w, img_h, self_w, self_h
        zoom = 1.0
        if img_w > self_w or img_h > self_h:
            zoom = min(float(self_w) / float(img_w), float(self_h) / float(img_h))
        elif img_w < self_w and img_h < self_h:
            zoom = min(float(self_w) / float(img_w), float(self_h) / float(img_h))
        self.zoom = zoom
        #print zoom
        self.buffer = wx.BitmapFromImage(wx.EmptyImage(640, 480))
        self.has_image = True
        self.x = self.y = self.lastx = self.lasty = 0
        self.brightness_adjustment = self.contrast_adjustment = 1.0
        self.img_left = self.img_top = 0
        self.in_motion = False
        self.is_dragging_image = False
        self.crop_x1 = self.crop_y1 = 0
        self.crop_x2 = img_w
        self.crop_y2 = img_h
        self.calib_x1 = self.calib_y1 = -1
        self.calib_x2 = self.calib_y2 = -1
        #print zoom
        self.zoom = zoom
        self.RefreshImage()
        #self.DrawToBuffer()
        #self.parent_dlg.ClearLandmarkList()
        #self.Refresh(True)

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
        self.mdobject = MdObject()
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
        self.ThreeDViewer = MdCanvas(panel)
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
            self.SetSize(wx.Size(915, 600))
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
        self.TwoDViewer.SetMode(mode)

    def OnWireframeMode(self, event):
        if self.dimension == 3:
            return
        if self.ConfirmWireframeOrBaselineEdit() != wx.ID_YES:
            return

        if self.show_wireframe == False:
            self.show_wireframe = True
            self.chkShowWireframe.SetValue(self.show_wireframe)
            self.ToggleShowWireframe(event)

        self.reset_bitmap_buttons(CONST['ID_WIREFRAME_MODE'])

    def OnBaselineMode(self, event):
        if self.dimension == 3:
            return
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
        print "toggle show wireframe"
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
        self.TwoDViewer.DrawToBuffer()

    def set_mdobject(self, mdobject):
        #print "set mdobject"
        session = self.app.get_session()
        #print "session in setmodanobject:", session
        if mdobject not in session:
            session.add( mdobject )
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
        mo = mdobject.copy()
        mo.move_to_center()

        if mdobject.dataset.dimension == 3:
            self.ThreeDViewer.SetSingleObject(mo)
        #if self.auto_rotate:
            #self.RefreshThreeDViewer()
            #self.ThreeDViewer.BeginAutoRotate(50)
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

    def AppendLandmark(self, landmark):
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
            mo = self.mdobject
        else:
            mo = self.mdobject = MdObject()

        mo.objname = self.forms['objname'].GetValue()
        mo.objdesc = self.forms['objdesc'].GetValue()
        #mo.scale = self.forms['scale'].GetValue()
        mo.dataset_id = self.dataset.id
        mo.landmark_list = self.landmark_list[:]
        mo.pack_landmark()

        if self.TwoDViewer.has_image:
            if len(mo.image_list)==0:
                mo.image_list.append(MdImage())
            mo.image_list[0].set_image_object(self.TwoDViewer.origimg)
            mo.image_list[0].ppmm = self.ppmm
        #for i in range(len(self.dataset.groupname_list)):
        #    mo.group_list[i] = self.groupText[i].GetValue()
        #print "session in dialog_object", session
        if mo not in session:
            session.add(mo)

        self.frame.object_content_pane.SetObjectContent(mo)

        if self.is_baseline_changed or self.is_wireframe_changed:
            #print self.is_baseline_changed
            #print self.baseline_point_list
            self.dataset.pack_wireframe()
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

    def AddCoord(self, event):
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
        dummy_mdobject = MdObject()
        dummy_mdobject.landmark_list = self.landmark_list[:]
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
