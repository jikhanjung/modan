#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import math
import time
from libpy.modan_dbclass import *
from PIL import Image, ImageEnhance


CONST = {}
CONST['ID_LANDMARK_MODE'] = 4003
CONST['ID_CALIBRATION_MODE'] = 4004
CONST['ID_LANDMARK_EDIT_MODE'] = 4005
CONST['ID_WIREFRAME_MODE'] = 4006
CONST['ID_WIREFRAME_EDIT_MODE'] = 4007
CONST['ID_BASELINE_MODE'] = 4008
CONST['ID_BASELINE_EDIT_MODE'] = 4009

LM_MISSING_VALUE = -99999

DIALOG_SIZE = wx.Size(1024,768)
landmarkSeqWidth = 40
landmarkCoordWidth = 60
landmarkCoordHeight = 22

ID_CALIBRATION_OKAY_BUTTON = 1001
ID_CALIBRATION_CANCEL_BUTTON = 1002

class UnitCalibrationDlg( wx.Dialog ):
  def __init__(self,parent,id):
    wx.Dialog.__init__(self,parent,id,'Calibration Unit', size = (320,180))
    self.panel = panel = wx.Panel( self, -1 )
    self.maintext = wx.StaticText(panel, -1, 'Enter length in millimeter:', style=wx.ALIGN_LEFT)
    self.length = wx.TextCtrl(panel,-1,'1')
    self.unittext = wx.StaticText( panel, -1, 'mm', style=wx.ALIGN_LEFT )

    self.okButton = wx.Button( panel, ID_CALIBRATION_OKAY_BUTTON, 'OK' )
    self.cancelButton = wx.Button( panel, ID_CALIBRATION_CANCEL_BUTTON , 'Cancel' )
    self.Bind( wx.EVT_BUTTON, self.OnOk, id=ID_CALIBRATION_OKAY_BUTTON )
    self.Bind( wx.EVT_BUTTON, self.OnCancel, id=ID_CALIBRATION_CANCEL_BUTTON )

    #x = self.GetSize().width / 2 
    #y = self.GetSize().height/ 2 
    rowHeight = 22
    controlWidth = ( 150, 30, 20 )
    controls = ( self.maintext, self.length, self.unittext )
    x = 60
    y = 50
    for i in range( len( controls ) ):
      controls[i].SetSize( ( controlWidth[i], rowHeight ) )
      controls[i].SetPosition( ( x, y ) )
      x+= controlWidth[i]

    x = 110
    y = 100
    buttonWidth = ( 45, 45)
    buttons = ( self.okButton, self.cancelButton )
    for i in range( len( buttons ) ):
      buttons[i].SetSize( ( buttonWidth[i], rowHeight ) )
      buttons[i].SetPosition( ( x, y ) )
      x += buttonWidth[i] 

    panel.Fit()
    #self.Show()
    self.length.SetFocus()
    #self.forms['objname'] = wx.TextCtrl(panel, -1, '')
    
  def OnOk(self,event):
    self.EndModal(wx.ID_OK)   

  def OnCancel(self,event):
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

def piltoimage(pil,alpha=True):
    """Convert PIL Image to wx.Image."""
    if alpha:
        #print "alpha 1", clock()
        image = apply( wx.EmptyImage, pil.size )
        #print "alpha 2", clock()
        image.SetData( pil.convert( "RGB").tostring() )
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
    
