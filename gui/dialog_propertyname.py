#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import os  # sys, os
from libpy.modan_dbclass import MdPropertyName

import wx


# from libpy.conf import ModanConf
#from libpy.model_mdobject import MdObject 
from libpy.model_mddataset import MdDataset
#from libpy.dataimporter import ModanDataImporter

DIALOG_SIZE = wx.Size(640, 500)

ID_SAVE_BUTTON = 1001
ID_CANCEL_BUTTON = 1002
ID_MOVELEFT_BUTTON = 1003
ID_MOVERIGHT_BUTTON = 1004
ID_ADD_BUTTON = 1005
ID_DELETE_BUTTON = 1006


class ModanPropertynameDialog(wx.Dialog):
    dataset = None

    def __init__(self, parent, id=-1,dataset=None):
        wx.Dialog.__init__(self, parent, id, 'Property Name', size=DIALOG_SIZE)
        panel = wx.Panel(self, -1)
        self.forms = dict()
        self.mos = []
        if dataset:
            self.dataset = dataset
        self.app = wx.GetApp()

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        vSizer = wx.BoxSizer(wx.VERTICAL)

        propertyLabel1 = wx.StaticText(panel, -1, 'For this dataset', style=wx.ALIGN_CENTER)
        propertyLabel2 = wx.StaticText(panel, -1, 'Available', style=wx.ALIGN_CENTER)
        propertyList1 = wx.ListBox(panel, -1, choices=(), size=(150, 200), style=wx.LB_EXTENDED)
        propertyList2 = wx.ListBox(panel, -1, choices=(), size=(150, 200), style=wx.LB_EXTENDED)
        addButton = wx.Button(panel, ID_ADD_BUTTON, '+', size=(30, 30))
        deleteButton = wx.Button(panel, ID_DELETE_BUTTON, '-', size=(30, 30))
        moveLeftButton = wx.Button(panel, ID_MOVELEFT_BUTTON, '<', size=(30, 30))
        moveRightButton = wx.Button(panel, ID_MOVERIGHT_BUTTON, '>', size=(30, 30))
        self.Bind(wx.EVT_BUTTON, self.OnMoveLeft, id=ID_MOVELEFT_BUTTON)
        self.Bind(wx.EVT_BUTTON, self.OnMoveRight, id=ID_MOVERIGHT_BUTTON)
        self.Bind(wx.EVT_BUTTON, self.OnAdd, id=ID_ADD_BUTTON)
        self.Bind(wx.EVT_BUTTON, self.OnDelete, id=ID_DELETE_BUTTON)

        self.list1 = propertyList1
        self.list2 = propertyList2

        objectSizer_btn = wx.BoxSizer(wx.VERTICAL)
        objectSizer_btn.Add(moveLeftButton, wx.EXPAND)
        objectSizer_btn.Add(moveRightButton, wx.EXPAND)

        objectSizer = wx.FlexGridSizer(2, 3, 0, 0)
        objectSizer.AddGrowableCol(0)
        objectSizer.AddGrowableCol(2)
        objectSizer.AddGrowableRow(1)

        objectSizer.Add(propertyLabel1, wx.EXPAND)
        objectSizer.Add((10, 10), wx.EXPAND)
        objectSizer.Add(propertyLabel2, wx.EXPAND)
        objectSizer.Add(propertyList1, wx.EXPAND)
        objectSizer.Add(objectSizer_btn, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        objectSizer.Add(propertyList2, wx.EXPAND)

        # testButton = wx.Button( panel, -1, 'Test' )
        objectSizerAll = wx.FlexGridSizer(rows=3, cols=1)
        objectSizerAll.AddGrowableRow(0)
        objectSizerAll.AddGrowableRow(2)
        objectSizerAll.Add(objectSizer, wx.EXPAND)
        objectSizerAll.Add((10, 10), wx.EXPAND)

        saveButton = wx.Button(panel, ID_SAVE_BUTTON, 'Save')
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=ID_SAVE_BUTTON)
        cancelButton = wx.Button(panel, ID_CANCEL_BUTTON, 'Cancel')
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=ID_CANCEL_BUTTON)

        optionSizer = wx.FlexGridSizer(2, 1, 0, 0)
        optionSizer.AddGrowableRow(0)
        optionSizer.AddGrowableRow(1)

        buttonSizer1 = wx.BoxSizer(wx.VERTICAL)
        buttonSizer1.Add(addButton, flag=wx.ALIGN_CENTER)
        buttonSizer1.Add(deleteButton, flag=wx.ALIGN_CENTER)
        optionSizer.Add(buttonSizer1, flag=wx.ALIGN_CENTER)

        buttonSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer2.Add(saveButton, flag=wx.ALIGN_CENTER)
        buttonSizer2.Add(cancelButton, flag=wx.ALIGN_CENTER)

        hSizer.Add((10, 10))
        hSizer.Add(objectSizerAll, flag=wx.EXPAND)
        hSizer.Add((10, 10))
        hSizer.Add(optionSizer, flag=wx.EXPAND)
        hSizer.Add((10, 10))

        vSizer.Add((10, 10))
        vSizer.Add(hSizer, flag=wx.EXPAND)
        vSizer.Add((10, 10))
        vSizer.Add(buttonSizer2, flag=wx.EXPAND)
        vSizer.Add((10, 10))


        panel.SetSizer(vSizer)
        panel.Fit()
        #self.load_propertyname()

    def load_propertyname(self, propertyname_list=[]):
        if len( propertyname_list ) > 0:
            self.list1.Clear()
            for pn in propertyname_list:
                self.list1.Append( pn.propertyname, pn )

        self.list2.Clear()
        session = self.app.get_session()
        for p in session.query(MdPropertyName):
            is_in_use = False
            for i in range(self.list1.GetCount()):
                in_use = self.list1.GetClientData(i)
                if in_use == p:
                    is_in_use = True
            if not is_in_use:
                self.list2.Append( p.propertyname, p )

    def SetDataset(self, ds):
        self.dataset = ds
        #print self.dataset.baseline

        return

    def OnAdd(self, evt):
        dlg = PropertyNameDlg(self)
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            self.load_propertyname()
        return

    def OnDelete(self, evt):
        print "delete"
        session = self.app.get_session()
        print "session:", session
        for i in range( self.list2.GetCount() ):
            if self.list2.IsSelected(i):
                pn = self.list2.GetClientData(i)
                print "deleting", pn.propertyname
                session.add( pn )
                session.delete( pn )
        session.commit()
        self.load_propertyname()

    def OnSave(self, evt):

        #for pn in self.dataset.propertyname_list:
        #    self.dataset.propertyname_list.remove(pn)
        #for i in range( self.list1.GetCount() ):
        #    pn = self.list1.GetClientData(i)
        #    self.dataset.propertyname_list.append(pn)
        #print "save"
        self.EndModal(wx.ID_EDIT)

    def OnCancel(self, evt):
        self.Close()

    def OnMoveRight(self, evt):
        self.MoveItemsBetweenListBox(self.list1, self.list2)

    def OnMoveLeft(self, evt):
        self.MoveItemsBetweenListBox(self.list2, self.list1)

    def MoveItemsBetweenListBox(self, lb_from, lb_to):
        j = 0
        for i in xrange(lb_from.GetCount()):
            i
            if lb_from.IsSelected(j):
                pn = lb_from.GetClientData(j)
                lb_from.Delete(j)
                lb_to.Append(pn.propertyname, pn)
            else:
                j = j + 1

    def SetInUseList(self, pname_list):
        #for mo in objList:
        self.list1.Clear()
        #self.SetSort(lambda x, y: cmp(x.id, y.id)) # default sorting

        for pn in pname_list:
            #print mo.objname
            self.list1.Append(pn.propertyname, pn)
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



class PropertyNameDlg(wx.Dialog):
    def __init__(self, parent, id=-1, mdpropertyname=None):
        wx.Dialog.__init__(self, parent, id, 'Enter property name', size=(320, 180))
        self.panel = panel = wx.Panel(self, -1)
        self.app = wx.GetApp()
        self.maintext = wx.StaticText(panel, -1, 'Enter property name:', style=wx.ALIGN_LEFT)
        name = ''
        if mdpropertyname:
            name = mdpropertyname.name
        self.propertyname = wx.TextCtrl(panel, -1, name)

        self.okButton = wx.Button(panel, -1, 'OK')
        self.cancelButton = wx.Button(panel, -1, 'Cancel')
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.okButton)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancelButton)

        #x = self.GetSize().width / 2
        #y = self.GetSize().height/ 2
        rowHeight = 22
        controlWidth = ( 100, 150)
        controls = [ self.maintext, self.propertyname ]
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
        self.propertyname.SetFocus()
        #self.forms['objname'] = wx.TextCtrl(panel, -1, '')

    def OnOk(self, event):
        name = self.propertyname.GetValue()
        if name != '':
            session = self.app.get_session()
            pn = MdPropertyName(name)
            session.add(pn)
            session.commit()

        self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def GetValue(self):
        return self.groupinfo.GetValue()

