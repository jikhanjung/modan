#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import wx
from wx import glcanvas
#from OpenGL.GL import *
#from OpenGL.GLUT import *
#from OpenGL.GLU import *
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut
import sys
#import OpenGL.arrays

#from OpenGL.plugins import PlatformPlugin, FormatHandler
#from OpenGL.plugins import FormatHandler
from ctypes import util
try:
    from OpenGL.platform import win32
except AttributeError:
    pass

#FormatHandler( 'numpy', 'OpenGL.arrays.numpymodule.NumpyHandler', ['numpy.ndarray'] )
#fprint( str( OpenGL.plugins.FormatHandler.all() ) )
#from OpenGL.arrays import formathandler
#fprint( "handler registry" + str( formathandler.FormatHandler.HANDLER_REGISTRY ) )
#formathandler.FormatHandler.chooseOutput( 'ctypesarrays' )
#fprint( "handler registry" + str( formathandler.FormatHandler.HANDLER_REGISTRY ) )

IDX_BOOKSTEIN = 0
IDX_SBR = 1
IDX_GLS = 2
IDX_RFTRA = 3

MODE_3D_WIREFRAME = 1

CONST = {}
CONST['ID_LANDMARK_MODE'] = 4003
CONST['ID_CALIBRATION_MODE'] = 4004
CONST['ID_LANDMARK_EDIT_MODE'] = 4005
CONST['ID_WIREFRAME_MODE'] = 4006
CONST['ID_WIREFRAME_EDIT_MODE'] = 4007
CONST['ID_BASELINE_MODE'] = 4008
CONST['ID_BASELINE_EDIT_MODE'] = 4009


class MdColorScheme:
    def __init__(self):
        self.meanshape = ( 0.2, 0.2, 0.8 )
        self.meanshape_wireframe = ( 0.4, 0.4, 1.0 )
        self.selected_landmark = ( 1.0, 1.0, 0.0 )
        self.object = ( 0.6, 0.6, 0.2 )
        self.selected_object = ( 1.0, 1.0, 0.0 )
        self.object_wireframe = ( 1.0, 1.0, 0.6)
        self.selected_wire = ( 1.0, 0.5, 0.5 )

    def convert_color(self, hexstring):
        l = len(hexstring)
        #print l
        s = hexstring[l - 6:l]
        #print s
        r = s[0:2]
        g = s[2:4]
        b = s[4:6]
        #print r, g, b
        r = int(r, 16)
        g = int(g, 16)
        b = int(b, 16)
        #print r, g, b
        return ( r / 255.0, g / 255.0, b / 255.0 )


class Md3DCanvas(glcanvas.GLCanvas):
    def __init__(self, parent):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.print_log = True
        self.parent_dlg = parent.GetParent()
        self.init = False
        # initial mouse position
        self.hovering_edge = []
        self.hovering_edge_idx = -1
        self.color = MdColorScheme()
        self.r = 1
        self.superimposition_method = IDX_GLS
        self.offset = -3
        self.lm_radius = 0.1
        self.wire_radius = 0.05
        self.auto_rotate = False
        self.show_index = False
        self.show_wireframe = True
        self.show_baseline = False
        self.show_meanshape = True
        self.lastx = self.x = 30
        self.lasty = self.y = 30
        self.lastpanx = self.panx = 30
        self.lastpany = self.pany = 30
        self.last_xangle = 0
        self.last_yangle = 0
        self.is_dragging = False
        self.size = None
        self.mdobject = None
        self.dataset = None
        self.baseline_point_list = []
        self.baseline_candidate_point_list = []
        self.edge_list = []
        #self.color_scheme = None
        self.init_control = False
        self.interval = 50
        self.zoom = 1.0
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
        self.rotation_timer = wx.Timer(self)
        self.render_mode = gl.GL_RENDER

        self.mode = CONST['ID_LANDMARK_MODE']
        self.is_dragging_wire = False
        self.is_panning = False
        self.is_dragging_baseline = False
        self.begin_wire_idx = -1
        self.end_wire_idx = -1
        self.begin_baseline_idx = -1
        self.end_baseline_idx = -1
        self.wireidx_to_delete = -1
        self.wirename = dict()
        self.baseline_point_to_delete = -1
        self.lastpanposx = self.lastpanposy = 0
        #self.cursor_on_idx = -1

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
        #print "canvasbase init"

    def SetSuperimpositionMethod(self, method_idx):
        self.superimposition_method = method_idx

    def OnWheel(self, event):
        rotation = event.GetWheelRotation()

        #print rotation
        self.zoom = self.zoom + self.zoom * 0.1 * rotation / ( ( rotation ** 2 ) ** 0.5 )
        #print self.zoom
        se = wx.SizeEvent()
        self.OnSize(se)
        self.Refresh(False)
        #self.OnDraw()

    def ShowWireframe(self):
        self.show_wireframe = True
        self.Refresh(False)

    def HideWireframe(self):
        self.show_wireframe = False
        self.Refresh(False)

    def ShowIndex(self):
        self.show_index = True
        self.Refresh(False)

    def HideIndex(self):
        self.show_index = False
        self.Refresh(False)

    def ShowMeanshape(self):
        self.show_meanshape = True
        self.Refresh(False)

    def HideMeanshape(self):
        self.show_meanshape = False
        self.Refresh(False)

    def BeginAutoRotate(self, interval=50):
        if self.auto_rotate:
            return
        self.auto_rotate = True
        #return
        #print "begin auto rotate interval = ", interval
        self.interval = interval
        self.Bind(wx.EVT_TIMER, self.AutoRotate, self.rotation_timer)
        self.rotation_timer.Start(self.interval)
        #glRenderMode( GL_RENDER )
        #self.auto_rotate = True
        #self.rotation_timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.AutoRotate, self.rotation_timer)
        #self.rotation_timer.Start(interval)
        #self.auto_rotate = True
        #self.SetSize( (400,400) )
        #self.OnDraw()

    def EndAutoRotate(self):
        #return
        #print "end auto rotate"
        self.Unbind(wx.EVT_TIMER, self.rotation_timer)
        #glRenderMode( GL_SELECT )
        self.auto_rotate = False
        #self.auto_rotate = False

    def IsCursorOnLandmark(self, x, y):
        SIZE = 1024
        gl.glSelectBuffer(SIZE)  # allocate a selection buffer of SIZE elements

        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()

        gl.glRenderMode(gl.GL_SELECT)
        self.render_mode = gl.GL_SELECT
        #print x, y
        #viewport = []

        #viewport = glGetIntegerv( GL_VIEWPORT )
        #print viewport

        gl.glLoadIdentity()
        glu.gluPickMatrix(x, (viewport[3] - y), 10, 10, viewport)
        gl.glFrustum(self.frustum_args['width'] * -1.0, self.frustum_args['width'], self.frustum_args['height'] * -1.0,
                  self.frustum_args['height'], self.frustum_args['znear'], self.frustum_args['zfar'])
        glu.gluLookAt(0.0, 0.0, self.offset * -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

        #print "on leftdown on draw"
        self.OnDraw()
        #print "on leftdown on draw done"
        #self.drawPeers(GL_SELECT,0);
        # draw some stuff


        buffer = gl.glRenderMode(gl.GL_RENDER)
        self.render_mode = gl.GL_RENDER
        #print "now render mode"
        hit = False
        top_lmidx = -1
        #print buffer
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)

        for hit_record in buffer:
            #print hit_record
            min_depth, max_depth, names = hit_record  # do something with the record
            #print min_depth, max_depth, names
            if names[0] > 1000:
                pass  #print "wire " + self.wirename[names[0]]
            else:
                #print "you hit point #" + str( names[0] )
                lmidx = names[0]
                if not hit:
                    hit = True
                    top_lmidx = lmidx
                    return hit, lmidx

        for hit_record in buffer:
            min_depth, max_depth, names = hit_record  # do something with the record
            if names[0] > 1000:
                hit = True
                idx = names[0]
                return hit, idx

                #self.object.landmarks[lmidx].selected = True
                #self.Refresh(False)
                #glMatrixMode( GL_MODELVIEW )

            #    print "a"
        return hit, top_lmidx

    def OnMouseEnter(self, event):
        self.SetFocus()

    def OnMotion(self, event):
        #print self.mode, CONST['ID_WIREFRAME_MODE']
        #if self.auto_rotate:
            #return
        x, y = event.GetPosition()
        if self.is_dragging:  #event.Dragging() and event.LeftIsDown():
            self.x, self.y = x, y
            self.Refresh(False)
            return
        elif self.is_panning:
            self.panx, self.pany = x, y
            self.Refresh(False)
            return
        if self.mode == CONST['ID_WIREFRAME_MODE']:
            hit, lm_idx = self.IsCursorOnLandmark(x, y)
            #print hit, lm_idx
            #print "cursor on landmark", x, y, hit, lm_idx
            if hit:
                if lm_idx < 1000:
                    #print hit, lm_idx
                    #print "cursor on landmark"
                    self.SetMode(CONST['ID_WIREFRAME_EDIT_MODE'])
                    #self.begin_wire_idx = lm_idx
                else:
                    self.hovering_edge_idx = lm_idx
                    #from_idx, to_idx = self.wirename[lm_idx].split("_")
                    #self.hovering_edge = [ from_idx, to_idx ]
                    #self.parent_dlg.DeleteWire(from_idx, to_idx)
            else:
                self.hovering_edge_idx = -1

        elif self.mode == CONST['ID_WIREFRAME_EDIT_MODE']:
            hit, lm_idx = self.IsCursorOnLandmark(x, y)
            #print hit, lm_idx, self.begin_wire_idx, self.end_wire_idx
            if not hit or lm_idx > 1000:
                self.end_wire_idx = -1
                if self.is_dragging_wire:
                    self.wire_to_x = x
                    self.wire_to_y = y
                else:
                    self.SetMode(CONST['ID_WIREFRAME_MODE'])
                    self.begin_wire_idx = -1
                    # draw dangling wire
            else:
                if self.is_dragging_wire:
                    if self.begin_wire_idx != lm_idx:
                        self.end_wire_idx = lm_idx
                else:
                    self.begin_wire_idx = lm_idx
        elif self.mode == CONST['ID_BASELINE_MODE']:
            hit, lm_idx = self.IsCursorOnLandmark(x, y)
            if hit and lm_idx < 1000:
                self.SetMode(CONST['ID_BASELINE_EDIT_MODE'])
                #self.begin_baseline_idx = lm_idx
        elif self.mode == CONST['ID_BASELINE_EDIT_MODE']:
            hit, lm_idx = self.IsCursorOnLandmark(x, y)
            #print hit, lm_idx, self.begin_wire_idx, self.end_wire_idx
            if not hit or lm_idx > 1000:
                self.end_baseline_idx = -1
                if self.is_dragging_baseline:
                    self.baseline_to_x = self.x
                    self.baseline_to_y = self.y
                else:
                    self.SetMode(CONST['ID_BASELINE_MODE'])
                    self.begin_baseline_idx = -1
                    # draw dangling wire
            else:
                if self.begin_baseline_idx != lm_idx:
                    #to_lm = self.GetParent().GetParent().landmark_list[lm_idx]
                    #self.baseline_to_x, self.baseline_to_y = self.ImageXYtoScreenXY(to_lm[1],to_lm[2])
                    self.end_baseline_idx = lm_idx
        self.Refresh(False)

    def OnLeftDown(self, event):
        #print self.mode, CONST['ID_BASELINE_MODE'], CONST['ID_BASELINE_EDIT_MODE']
        if self.mode == CONST['ID_WIREFRAME_EDIT_MODE']:
            self.is_dragging_wire = True
            x, y = event.GetPosition()
            hit, lm_idx = self.IsCursorOnLandmark(x, y)
            #print hit, lm_idx
            #print "cursor on landmark", x, y, hit, lm_idx
            if hit and lm_idx < 1000:
                self.begin_wire_idx = lm_idx
                #print hit, lm_idx
                #print "cursor on landmark"
                #self.SetMode(CONST['ID_WIREFRAME_EDIT_MODE'])
                #print "left down. edit wireframe!", self.begin_wire_idx
            #
        elif self.mode == CONST['ID_BASELINE_EDIT_MODE']:
            self.is_dragging_baseline = True
            x, y = event.GetPosition()
            hit, lm_idx = self.IsCursorOnLandmark(x, y)
            #print hit, lm_idx
            #print "cursor on landmark", x, y, hit, lm_idx
            if hit and lm_idx < 1000:
                self.begin_baseline_idx = lm_idx
                #print hit, lm_idx
                #print "cursor on landmark"
                #self.SetMode(CONST['ID_WIREFRAME_EDIT_MODE'])
                #print "left down. edit baseline!", self.begin_baseline_idx
            #

        else:
            #print "dragging"
            self.is_dragging = True
            self.CaptureMouse()
            self.x, self.y = self.lastx, self.lasty = event.GetPosition()

    def OnLeftUp(self, event):
        #print "up"
        if self.mode == CONST['ID_WIREFRAME_EDIT_MODE']:
            if self.begin_wire_idx != self.end_wire_idx and self.begin_wire_idx > 0 and self.end_wire_idx > 0:
                #print "add wire from", self.begin_wire_idx, "to", self.end_wire_idx
                self.parent_dlg.AppendWire(self.begin_wire_idx, self.end_wire_idx)
                self.mode = CONST['ID_WIREFRAME_MODE']
            self.is_dragging_wire = False
            self.mode = CONST['ID_WIREFRAME_MODE']
            self.begin_wire_idx = -1
        elif self.mode == CONST['ID_BASELINE_EDIT_MODE']:
            if len(self.parent_dlg.baseline_point_list) == 3:
                self.parent_dlg.ClearBaseline()
            if self.begin_baseline_idx > 0:
                self.parent_dlg.AppendBaselinePoint(self.begin_baseline_idx)
            self.mode = CONST['ID_BASELINE_MODE']
            self.is_dragging_baseline = False
            self.begin_baseline_idx = -1
        elif self.is_dragging:
            self.is_dragging = False
            self.x, self.y = event.GetPosition()
            self.last_xangle = self.last_xangle + (self.x - self.lastx)
            self.last_yangle = self.last_yangle + self.y - self.lasty
            self.lastx = self.x
            self.lasty = self.y
            self.ReleaseMouse()
            self.AdjustObjectRotation()
            self.Refresh(False)

    def OnRightDown(self, event):
        #print "right down"
        if self.mode == CONST['ID_WIREFRAME_MODE']:
            #print "wireframe_mode right down"
            x, y = event.GetPosition()
            hit, idx = self.IsCursorOnLandmark(x, y)
            if hit and idx > 1000:
                self.wireidx_to_delete = idx
                self.hovering_edge_idx = -1
                #print self.wirename[lm_idx]
        elif self.mode == CONST['ID_BASELINE_EDIT_MODE']:
            x, y = event.GetPosition()
            hit, idx = self.IsCursorOnLandmark(x, y)
            if hit and idx < 1000:
                self.baseline_point_to_delete = idx
        else:
            self.is_panning = True
            self.CaptureMouse()
            self.panx, self.pany = self.lastpanx, self.lastpany = event.GetPosition()

        self.Refresh(False)
        return

    def OnRightUp(self, event):
        #print "right up"
        if self.is_panning and self.mode != CONST['ID_BASELINE_EDIT_MODE']:
            self.is_panning = False
            x, y = event.GetPosition()
            self.panx, self.pany = x, y
            self.lastpanposx += (self.panx - self.lastpanx)
            self.lastpanposy += (self.lastpany - self.pany)
            self.lastpanx, self.lastpany = self.panx, self.pany = x, y
            self.ReleaseMouse()
            self.Refresh(False)
            return

        if self.mode == CONST['ID_WIREFRAME_MODE']:
            x, y = event.GetPosition()
            hit, lm_idx = self.IsCursorOnLandmark(x, y)
            if hit and lm_idx > 1000:
                if self.wireidx_to_delete == lm_idx:
                    #print self.wirename[lm_idx], "will be deleted."
                    from_idx, to_idx = self.wirename[lm_idx].split("_")
                    self.parent_dlg.DeleteWire(from_idx, to_idx)
        elif self.mode == CONST['ID_BASELINE_EDIT_MODE']:
            x, y = event.GetPosition()
            hit, idx = self.IsCursorOnLandmark(x, y)
            if hit and idx < 1000:
                if self.baseline_point_to_delete == idx:
                    self.parent_dlg.DeleteBaselinePoint(idx)

                    #print parent.wire
                    #print "wireframe_mode right up"
        #if self.mode == WIREFRAME_EDIT_
        self.wireidx_to_delete = -1
        self.Refresh(False)
        return

    def OnMiddleDown(self, event):
        #if self.print_log:
        #print "OnLeftDown", self.mode
        #print self.mode
        if self.mode == CONST['ID_WIREFRAME_EDIT_MODE']:
            self.is_dragging_wire = True
            self.CaptureMouse()
        elif self.mode == CONST['ID_BASELINE_EDIT_MODE']:
            x, y = event.GetPosition()
            hit, idx = self.IsCursorOnLandmark(x, y)
            if hit and idx < 1000:
                self.is_dragging_baseline = True
                self.begin_baseline_idx = idx
                self.CaptureMouse()

    def OnMiddleUp(self, event):

        if self.is_dragging_wire:
            x, y = event.GetPosition()
            hit, lm_idx = self.IsCursorOnLandmark(x, y)
            if hit and lm_idx < 1000 and self.begin_wire_idx >= 0 and self.end_wire_idx >= 0:
                #print "append wire", self.begin_wire_idx, self.end_wire_idx
                self.parent_dlg.AppendWire(self.begin_wire_idx, self.end_wire_idx)
            self.is_dragging_wire = False
            self.begin_wire_idx = self.end_wire_idx
            self.end_wire_idx = -1
            self.ReleaseMouse()
        elif self.is_dragging_baseline:
            parent = self.parent_dlg
            #print parent.baseline_points
            x, y = event.GetPosition()
            hit, lm_idx = self.IsCursorOnLandmark(x, y)
            #print hit, lm_idx
            if hit and lm_idx < 1000:
                if lm_idx == self.begin_baseline_idx:
                    #parent = self.GetParent().GetParent()
                    if len(parent.baseline_point_list) == 3:
                        #print "clear baseline"
                        parent.ClearBaseline()
                    parent.AppendBaselinePoint(lm_idx)
                else:
                    parent.ClearBaseline()
                    parent.AppendBaselinePoint(self.begin_baseline_idx)
                    parent.AppendBaselinePoint(self.end_baseline_idx)

                    #print "append", lm_idx, "to baseline"
                    #parent.baseline_points = []
                    #parent.baseline_points.append( lm_idx )
            self.is_dragging_baseline = False
            #self.begin_baseline_idx = self.end_baseline_idx
            #self.end_baseline_idx = -1
            self.ReleaseMouse()
        self.Refresh(False)

    def DrawToBuffer(self):
        self.Refresh(False)

    def ShowBaseline(self):
        self.show_baseline = True
        self.DrawToBuffer()
        #self.OnDraw()

    def HideBaseline(self):
        self.show_baseline = False
        self.DrawToBuffer()
        #self.OnDraw()

    def OnEraseBackground(self, event):
        #print "EraseBackground"
        pass  # Do nothing, to avoid flashing on MSW.

    def OnSize(self, event):
        #    self.ProcessSize()
        #if self.print_log:
        #print "OnSize"

        if not self.init:
            self.InitGL()
            self.init = True
        s = self.GetClientSize()
        size = self.size = s
        if self.GetContext():
            self.SetCurrent()
            gl.glViewport(0, 0, size.width, size.height)

            # Maintain 1:1 Aspect Ratio
            """
            the screen starts out with a glFrustum left,right,bottom,top of -0.5,0.5,-0.5,0.5
            and an aspect ratio (screen width / screen height) of 1
            """
            w = float(size.width)
            h = float(size.height)
            if self.r == 0:
                self.r = 1
            height = width = self.r
            if size.width > size.height:
                width = width * (w / h)
            elif size.height > size.width:
                height = height * (h / w)
            #print width, "x", height
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            #print "zoom", self.zoom

            znear = 0.1
            zfar = 100
            width = width / self.zoom
            height = height / self.zoom
            bottom_height = -1 * height
            top_height = height

            znear = ( self.offset * - 0.4 )
            zfar = ( self.offset * - 1.6 )
            #      if self.superimposition_method == IDX_SBR or self.superimposition_method == IDX_BOOKSTEIN:
            #        bottom_height += height
            #        top_height += height
            self.frustum_args = dict()
            self.frustum_args['width'] = width
            self.frustum_args['height'] = height
            self.frustum_args['znear'] = znear
            self.frustum_args['zfar'] = zfar

            gl.glFrustum(-width, width, bottom_height, top_height, znear, zfar)
            glu.gluLookAt(0.0, 0.0, self.offset * -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
            #print
            #print "width height near far offset", width, height, znear, zfar, self.offset
            #print self.r
            gl.glMatrixMode(gl.GL_MODELVIEW)  # switch back to model view

        event.Skip()


    def OnPaint(self, event):
        if self.print_log:
            pass  #print "OnPaint"
        dc = wx.PaintDC(self)
        self.SetCurrent()
        #if not self.init:
        #  self.InitGL()
        #  self.init = True
        self.OnDraw()


    def DrawWire(self, yangle, xangle, vfrom, vto, nameidx=-1):
        #if self.print_log:
        #print "DrawWire"
        #return

        lm1 = self.mdobject.landmark_list[vfrom - 1]
        lm2 = self.mdobject.landmark_list[vto - 1]
        axis_start = [0, 0, 1]
        axis_end = [lm1.coords[0] - lm2.coords[0], lm1.coords[1] - lm2.coords[1], lm1.coords[2] - lm2.coords[2]]
        angle = math.acos(axis_start[0] * axis_end[0] + axis_start[1] * axis_end[1] + axis_start[2] * axis_end[2] / (
        (axis_start[0] ** 2 + axis_start[1] ** 2 + axis_start[2] ** 2) ** 0.5 * (
        axis_end[0] ** 2 + axis_end[1] ** 2 + axis_end[2] ** 2) ** 0.5))
        angle = angle * (180 / math.pi)
        axis_rotation = [0, 0, 0]
        axis_rotation[0] = axis_start[1] * axis_end[2] - axis_start[2] * axis_end[1]
        axis_rotation[1] = axis_start[2] * axis_end[0] - axis_start[0] * axis_end[2]
        axis_rotation[2] = axis_start[0] * axis_end[1] - axis_start[1] * axis_end[0]
        if angle == 180:
            axis_rotation = [1, 0, 0]

        length = (axis_end[0] ** 2 + axis_end[1] ** 2 + axis_end[2] ** 2) ** 0.5
        radius = self.wire_radius
        gl.glPushMatrix()
        #glLoadIdentity()
        cyl = glu.gluNewQuadric()
        #glTranslate(0, 0, self.offset)
        #glRotatef(yangle, 1.0, 0.0, 0.0)
        #glRotatef(xangle, 0.0, 1.0, 0.0)
        gl.glTranslate(lm2.coords[0], lm2.coords[1], lm2.coords[2])
        if (angle != 0):
            gl.glRotate(angle, axis_rotation[0], axis_rotation[1], axis_rotation[2])
        if nameidx > 0:
            gl.glLoadName(nameidx)
        glu.gluCylinder(cyl, radius, radius, length, 10, 10)
        gl.glPopMatrix()

    def SelectLandmark(self, idx_list):
        for i in range(len(self.mdobject.landmark_list)):
            if i in idx_list:
                self.mdobject.landmark_list[i].selected = True
            else:
                self.mdobject.landmark_list[i].selected = False
        #print "selected idx :", idx_list
        self.Refresh(False)

    def SelectObject(self, idx_list):
        for i in range(len(self.dataset.object_list)):
            if i in idx_list:
                self.dataset.object_list[i].selected = True
            else:
                self.dataset.object_list[i].selected = False
                #print self.dataset.object_list[i].selected
        self.Refresh(False)

    def ToggleObjectVisibility(self, idx):
        if self.dataset.object_list[idx].visible:
            self.dataset.object_list[idx].visible = False
        else:
            self.dataset.object_list[idx].visible = True

    def DrawObject(self, object, xangle, yangle, size=0.1, color=( 1.0, 1.0, 0.0 ), show_index=False,
                   single_object_mode=True):
        #single_object_mode = False
        #if self.print_log:
        #print "DrawObject"
        #print "object:", object.objname
        original_color = color
        #i = 0
        #glTranslate(0, 0, self.offset)
        gl.glPushMatrix()


        #    single_object_mode = True
        if not single_object_mode:
            #print "point size, glbegin"
            gl.glPointSize(3)
            gl.glDisable(gl.GL_LIGHTING)
            gl.glBegin(gl.GL_POINTS)
        i = 1
        for lm in object.landmark_list:
            if lm.selected:
                gl.glColor3f(self.color.selected_landmark[0], self.color.selected_landmark[1],
                          self.color.selected_landmark[2])
            elif i == self.begin_wire_idx or i == self.end_wire_idx:
                gl.glColor3f(self.color.selected_landmark[0], self.color.selected_landmark[1],
                          self.color.selected_landmark[2])
            elif i == self.begin_baseline_idx or i == self.end_baseline_idx:
                gl.glColor3f(self.color.meanshape_wireframe[0], self.color.meanshape_wireframe[1],
                          self.color.meanshape_wireframe[2])
            elif i in self.parent_dlg.baseline_point_list and self.show_baseline:
                gl.glColor3f(0.0, 0.0, 1.0)
            else:
                gl.glColor3f(original_color[0], color[1], color[2])
            coords = [0,0,0]
            for j in range(len(lm.coords)):
                coords[j] = lm.coords[j]

            if single_object_mode:
                gl.glPushMatrix()
                gl.glTranslate(coords[0], coords[1], coords[2])
                #print "render mode:", self.render_mode, gl.GL_SELECT
                if self.render_mode == gl.GL_SELECT:
                    gl.glLoadName(i)
                i += 1
                glut.glutSolidSphere(size, 20, 20)  #glutSolidCube( size )
                gl.glPopMatrix()
            else:
                gl.glVertex3f(coords[0], coords[1], coords[2])

        if not single_object_mode:
            #print "glend"
            gl.glEnd()
            gl.glEnable(gl.GL_LIGHTING)

        if self.show_baseline:
            gl.glDisable(gl.GL_LIGHTING)
            gl.glColor3f(.2, .2, 1.0)
            basestr = ["(0,0,0)", "(0,1,0)", "(x,y,0)"]
            i = 0
            for i in range(len(self.parent_dlg.baseline_point_list)):
                #print "i=",i
                idx = self.parent_dlg.baseline_point_list[i]
                #print "idx=",idx
                lm = object.landmark_list[idx - 1]
                #print basestr[i]
                gl.glRasterPos3f(lm.coords[0] - size * (len(basestr[i]) / 2), lm.coords[1] - size * 2.4, lm.coords[2])
                for letter in list(basestr[i]):
                    gl.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_12, int(ord(letter)))
            gl.glEnable(gl.GL_LIGHTING)

        if show_index:
            i = 0
            gl.glDisable(gl.GL_LIGHTING)
            gl.glColor3f(.5, .5, 1.0)
            for lm in object.landmark_list:
                i += 1
                gl.glRasterPos3f(lm.coords[0], lm.coords[1] + size * 1.2, lm.coords[2])
                for letter in list(str(i)):
                    #print ord(letter)
                    #print glut.GLUT_BITMAP_HELVETICA_12, type(glut.GLUT_BITMAP_HELVETICA_12).__name__
                    #print int(ord(letter)), type(int(ord(letter))).__name__
                    glut.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_12, ord(letter))
                    #c = 7
                    #glutBitmapCharacter(ctypes.c_int(c), ctypes.c_int(ord(letter)))
            gl.glEnable(gl.GL_LIGHTING)
        gl.glPopMatrix()

    def InitGL(self):
        #if self.print_log:
        #print "InitGL"
        if self.GetContext():
            self.SetCurrent()
            gl.glViewport(0, 0, self.GetSize().width, self.GetSize().height)
        #glMatrixMode(GL_PROJECTION)
        #glFrustum(-1.5, 1.5, -1.5, 1.5, 1, 100.0)
        #print "width height near far offset", width, height, znear, zfar, self.offset
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        #glLightfv( GL_LIGHT0, GL_AMBIENT, ( 0.5, 0.5, 0.5, 1.0 ) )
        #glLightfv( GL_LIGHT0, GL_AMBIENT, ( 1.0, 1.0, 1.0, 1.0 ) )
        #glLightfv( GL_LIGHT0, GL_POSITION, ( 0.0, 0.0, 0.0 ) )
        #glLightfv( GL_LIGHT0, GL_SPOT_DIRECTION, ( 0.0, 0.0, -1.0 ) )
        """
        glEnable(GL_LIGHT1)
        glLightfv( GL_LIGHT1, GL_DIFFUSE, ( 1.0, 1.0, 1.0, 1.0 ) )
        glLightfv( GL_LIGHT1, GL_SPECULAR, ( 1.0, 1.0, 1.0, 1.0 ) )
        glLightfv( GL_LIGHT1, GL_POSITION, ( 0.0, 0.0, -5.0 ) )
        glLightfv( GL_LIGHT1, GL_SPOT_DIRECTION, ( 0.0, 0.0, 0.0 ) )
        glEnable(GL_LIGHT2)
        glLightfv( GL_LIGHT2, GL_DIFFUSE, ( 1.0, 1.0, 1.0, 1.0 ) )
        glLightfv( GL_LIGHT2, GL_SPECULAR, ( 1.0, 1.0, 1.0, 1.0 ) )
        glLightfv( GL_LIGHT2, GL_POSITION, ( 0.0, 5.0, -2.0 ) )
        glLightfv( GL_LIGHT2, GL_SPOT_DIRECTION, ( 0.0, 0.0, -2.0 ) )

        glEnable(GL_LIGHT3)
        glLightfv( GL_LIGHT3, GL_DIFFUSE, ( 1.0, 1.0, 1.0, 1.0 ) )
        glLightfv( GL_LIGHT3, GL_SPECULAR, ( 1.0, 1.0, 1.0, 1.0 ) )
        glLightfv( GL_LIGHT3, GL_POSITION, ( 0.0, -5.0, -2.0 ) )
        glLightfv( GL_LIGHT3, GL_SPOT_DIRECTION, ( 0.0, 0.0, -2.0 ) )
        """

        gl.glEnable(gl.GL_COLOR_MATERIAL)

        """ anti-aliasing """
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glEnable(gl.GL_POINT_SMOOTH)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_DONT_CARE)

        gl.glClearColor(0.2, 0.2, 0.2, 1.0)  # set background color
        gl.glDepthFunc(gl.GL_LESS)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        #glMatrixMode(GL_MODELVIEW)
        #glLoadIdentity()
        #gluLookAt( 0.0, 0.0, 50.0, 0.0, 0.0, -100.0, 0.0, 1.0, 0.0 )
        #gluLookAt( 0.0, 0.0, self.offset * -1.0, 0.0, 0.0, -50.0, 0.0, 1.0, 0.0 )
        #gluLookAt( 0.0, 0.0, self.offset * -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0 )
        #glTranslatef(0.0, 0.0, self.offset)
        #print "offset:", self.offset
        glut.glutInit(sys.argv)

        #self.offset = -3 # z position

    def AdjustObjectRotation(self):
        y_angle = self.last_yangle
        self.last_yangle = 0
        x_angle = self.last_xangle
        self.last_xangle = 0
        x_angle = -1.0 * ( x_angle * math.pi ) / 180
        self.mdobject.rotate_3d(x_angle, 'Y')
        if self.dataset != None:
            for mo in self.dataset.object_list:
                mo.rotate_3d(x_angle, 'Y')
        y_angle = ( y_angle * math.pi ) / 180
        self.mdobject.rotate_3d(y_angle, 'X')
        if self.dataset != None:
            for mo in self.dataset.object_list:
                mo.rotate_3d(y_angle, 'X')

    def OnDraw(self):
        #if self.print_log:
        #print "OnDraw"
        # clear color and depth buffers
        #print "OnDraw"
        #begin_time = clock()
        #print "begin draw", clock()
        #print 1/0
        if self.mdobject == None:
            self.SwapBuffers()
            return
        #print self.mdobject

        single_object_mode = True

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        #glLoadIdentity()
        gl.glPushMatrix()

        if self.render_mode == gl.GL_SELECT:
            gl.glInitNames()
            gl.glPushName(0)

        panning = 4.0
        panning_rate_x = panning * ( self.panx - self.lastpanx + self.lastpanposx ) / ( 1.0 * self.size.width )
        panning_rate_y = panning * ( self.lastpany - self.pany + self.lastpanposy ) / ( 1.0 * self.size.height )
        #print self.panx, self.lastpanx, panning_rate_x, self.size.width
        #print self.pany, self.lastpany, panning_rate_y, self.size.height
        gl.glTranslate(self.frustum_args['width'] * ( panning_rate_x ), self.frustum_args['height'] * panning_rate_y, 0)

        yangle = self.y - self.lasty + self.last_yangle
        xangle = (self.x - self.lastx ) + self.last_xangle
        gl.glRotatef(yangle, 1.0, 0.0, 0.0)
        gl.glRotatef(xangle, 0.0, 1.0, 0.0)
        #print self.Size.width

        #print "1"
        if self.dataset != None and (self.dataset.object_list ) > 0:
            if len(self.dataset.object_list) > 20:
                single_object_mode = False
            for mo in self.dataset.object_list:
                if mo.visible == False:
                    continue
                if mo.selected:
                    l_color = self.color.selected_object  #( 0.2, 1.0, 0.2 )
                else:
                    l_color = self.color.object  #( 1.0, 1.0, 0.0 )
                #print "drawobject"
                self.DrawObject(mo, xangle, yangle, self.lm_radius, color=l_color, show_index=False,
                                single_object_mode=single_object_mode)

        #dataset_end = clock()
        #print "draw single object", dataset_end
        #print "2"
        if len(self.mdobject.landmark_list)>200:
            single_object_mode = False
        """ Draw object: """
        if ( self.dataset != None and self.show_meanshape ):
            self.DrawObject(self.mdobject, xangle, yangle, self.lm_radius * 2, color=self.color.meanshape,
                            show_index=self.show_index, single_object_mode=single_object_mode)
        elif self.dataset == None:
            #print "drawobject", self.mdobject.landmark_list[0].coords
            self.DrawObject(self.mdobject, xangle, yangle, self.lm_radius * 2, color=self.color.object,
                            show_index=self.show_index, single_object_mode=single_object_mode)

        #print self.show_wireframe, self.parent_dlg.edge_list
        #print "draw wireframe if visible", clock()
        if ( self.dataset != None and self.show_meanshape and self.show_wireframe ) or (
                self.dataset == None and self.show_wireframe ):
            edge_list = self.parent_dlg.edge_list  #self.object.get_dataset().get_edge_list()
            #$print "on draw wireframe", wireframe.edge_list
            #print "on draw object", self.object

            nameidx = 1001
            self.wirename = dict()
            for vertices in edge_list:
                if self.dataset == None:
                    gl.glColor3f(self.color.object_wireframe[0], self.color.object_wireframe[1],
                              self.color.object_wireframe[2])
                else:
                    gl.glColor3f(self.color.meanshape_wireframe[0], self.color.meanshape_wireframe[1],
                              self.color.meanshape_wireframe[2])
                if nameidx == self.wireidx_to_delete:
                    gl.glColor3f(self.color.selected_wire[0], self.color.selected_wire[1], self.color.selected_wire[2])
                if nameidx == self.hovering_edge_idx:
                    gl.glColor3f(self.color.selected_wire[0], self.color.selected_wire[1], self.color.selected_wire[2])
                #print vertices
                vfrom = int(vertices[0])
                vto = int(vertices[1])
                if vfrom > len(self.mdobject.landmark_list) or vto > len(self.mdobject.landmark_list):
                    #print "out of bound"
                    continue
                    #if self.print_log:
                    #print "draw wire"
                self.wirename[nameidx] = str(vfrom) + "_" + str(vto)
                self.DrawWire(yangle, xangle, vfrom, vto, nameidx)
                nameidx += 1
        #print "3"
        landmark_list = self.parent_dlg.landmark_list
        if self.show_baseline:
            gl.glColor3f(self.color.meanshape_wireframe[0], self.color.meanshape_wireframe[1],
                      self.color.meanshape_wireframe[2])
            parent = self.parent_dlg
            line = []
            line[:] = parent.baseline_point_list[:]
            if len(line) > 0:
                line.append(line[0])
                for i in range(len(line) - 1):
                    #print "draw wire", line[i], line[i+1]
                    if line[i] > len(landmark_list) or line[i + 1] > len(landmark_list) or line[i] == line[i + 1]:
                        pass
                    else:
                        self.DrawWire(yangle, xangle, line[i], line[i + 1], nameidx)
                        nameidx += 1
        #print "4"
        gl.glPopMatrix()
        self.SwapBuffers()
        #end_time = clock()
        #t = end_time- begin_time
        #d = dataset_end - dataset_begin
        #print "draw:", t, d, int((d/t) *10000 )/100.0

    def AutoRotate(self, event):
        #print "auto rotate", self.is_dragging, self.auto_rotate
        if self.init_control == False:
            e = wx.SizeEvent(self.GetClientSize())
            self.OnSize(e)
            #self.SetSize( self.GetClientSize() )
            #self.GetParent().SetSize( self.GetParent().GetClientSize() )
            self.init_control = True
        if self.auto_rotate == False or self.is_dragging:
            return
            #return
        #print "rotate it!"
        self.last_xangle += 1
        self.OnDraw()

    def SetSingleObject(self, mo):
        #if self.print_log:
        #print "SetSingleObject", "with", len(mo.landmark_list), "landmarks"
        #mo.move_to_center()
        #wx.MessageBox( "before adjust perspective" )
        #sleep_time = 2
        #print "1"
        #sleep( sleep_time )
        self.mdobject = mo
        if len(mo.landmark_list) > 0:
            self.AdjustPerspective(self.mdobject)
            #print "2"
            #sleep( sleep_time )
        #    wx.MessageBox( "after adjust perspective" )
        #self.SetSize( self.GetClientSize() )
        for lm in mo.landmark_list:
            lm.selected = False
        #wx.MessageBox( "before on draw" )
        #print "3"
        #sleep( sleep_time )
        e = wx.SizeEvent(self.GetClientSize())
        self.OnSize(e)
        #self.SetSize( self.GetClientSize() )
        #self.OnDraw()
        #print "4"
        #sleep( sleep_time )
        #wx.MessageBox( "after on draw" )

    def ResetParameters(self):
        #self.zoom = 1.0
        self.OnSize(wx.SizeEvent())
        #self.

    def SetDataset(self, ds):
        self.dataset = ds
        #for mo in self.dataset:
        #  mo.move_to_center()
        self.SetSize(self.GetClientSize())


    def AdjustPerspective(self, mo):
        #if self.print_log:
        #print "adjust perspective"
        if not self.init:
            self.InitGL()
            self.init = True
        #max_x, max_y, max_z, min_x, min_y, min_z = -999,-999,-999,999,999,999
        max_dist = 0
        for i in range(len(mo.landmark_list)):
            for j in range(i + 1, len(mo.landmark_list)):
                dist = math.sqrt(( mo.landmark_list[i].coords[0] - mo.landmark_list[j].coords[0] ) ** 2 +
                                 ( mo.landmark_list[i].coords[1] - mo.landmark_list[j].coords[1] ) ** 2 +
                                 ( mo.landmark_list[i].coords[2] - mo.landmark_list[j].coords[2] ) ** 2)
                max_dist = max(dist, max_dist)
        """      max_x = max( lm.xcoord, max_x )
          max_y = max( lm.ycoord, max_y )
          max_z = max( lm.zcoord, max_z )
          min_x = min( lm.xcoord, min_x )
          min_y = min( lm.ycoord, min_y )
          min_z = min( lm.zcoord, min_z )
        # print max_x, min_x, max_y, min_y, max_z, min_z
        xr = max( max_x**2, min_x ** 2 ) ** 0.5
        yr = max( max_y**2, min_y ** 2 ) ** 0.5
        zr = max( max_z**2, min_z ** 2 ) ** 0.5
        r = max( xr, yr, zr )
        print "r", r
        print "x", max_x, min_x
        print "y", max_y, min_y
        print "z", max_z, min_z
        """
        if max_dist == 0:
            max_dist = 1
        self.r = max_dist * 0.3
        self.offset = max_dist * -2.0
        #max_diff = max( max_x - min_x, max_y - min_y, max_z - min_z )
        #print "max dist", max_dist
        #print "offset", self.offset
        #self.offset = -3 #max_diff * -2
        self.lm_radius = max_dist / ( 4 * min(50, len(mo.landmark_list)) )
        #print "radius:", self.lm_radius, "max_dist:", max_dist
        self.wire_radius = self.lm_radius / 2


class OpenGLTestWin(wx.Dialog):
    def __init__(self, parent, id=-1):
        wx.Dialog.__init__(self, parent, size=(400, 400))
        self.control = Md3DCanvas(self)
        self.control.SetMinSize((200, 200))
        self.v2 = wx.Button(self, wx.ID_ANY, 'Button #2')
        lb1 = wx.StaticText(self, wx.ID_ANY, 'Video #1')
        lb2 = wx.StaticText(self, wx.ID_ANY, 'Video #2')
        fs = wx.FlexGridSizer(2, 2, 10, 5)
        fs.AddGrowableCol(0)
        fs.AddGrowableCol(1)
        fs.AddGrowableRow(0)
        fs.Add(self.control, 0, wx.EXPAND)
        fs.Add(self.v2, 0, wx.EXPAND)
        fs.Add(lb1, 0, wx.ALIGN_CENTER)
        fs.Add(lb2, 0, wx.ALIGN_CENTER)
        self.Bind(wx.EVT_BUTTON, self.OnButton, self.v2)
        self.SetSizer(fs)
        self.init_control = False
        # Timer
        self.Show()
        self.auto_rotate = False

        return

    def ShowModal(self):
        print "show modal"
        self.control.SetSingleObject(self.mo)
        print "now really show modal"
        wx.Dialog.ShowModal(self)

    def OnButton(self, e):
        if self.auto_rotate:
            self.auto_rotate = False
            self.control.EndAutoRotate()
        else:
            self.auto_rotate = True
            self.control.BeginAutoRotate()

    def SetObject(self, mobj):
        #print "opengltestwin setobject"
        mobj.move_to_center()
        #self.control.SetSingleObject( mobj )
        self.mo = mobj
        #wx.MessageBox( "set single object done" )
        #self.control.BeginAutoRotate(10)
        #self.auto_rotate = True

    def SetDataset(self, ds):
        self.control.SetDataset(ds)
        for mo in ds.object_list:
            for lm in mo.landmark_list:
                lm.selected = False

                #self.SetSize((400,400))


""" apply these color schemes later
------
ordinary
------
FF9900
B36B00
FFE6BF
FFCC80
0033CC
00248F
BFCFFF
809FFF
3F0099
2C006B
DABFFF
B480FF
FFE400
B3A000
FFF8BF
FFF280
------
pastel
------
806640
E6DCCF
BF8630
5C73B8
405080
CFD4E6
3054BF
61458A
5A4080
D8CFE6
6B30BF
E6D973
807940
E6E3CF
BFB030
------
"""
