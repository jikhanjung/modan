#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx

from gui.dialog_dataset import ModanDatasetDialog
from gui.dialog_object import ModanObjectDialog
from libpy.model_mdobject import MdObject


class MainTreeMenu(wx.Menu):
    def __init__(self, parent, mode='dataset', dataset=None, dim=2):
        wx.Menu.__init__(self)
        self.parent = parent
        self.dataset = dataset
        self.frame = parent.frame
        self.dim = dim
        if ( mode == 'dataset' ):
            # addNew = wx.MenuItem(self, -1, 'Add &New')
            editDataset = wx.MenuItem(self, -1, '&Edit')
            addObject = wx.MenuItem(self, -1, 'Add &Object')
            #self.AppendItem( addNew )
            self.AppendItem(editDataset)
            self.AppendItem(addObject)
            #self.Bind(wx.EVT_MENU, self.OnAddDataset, id=addNew.GetId())
            self.Bind(wx.EVT_MENU, self.OnEditDataset, id=editDataset.GetId())
            self.Bind(wx.EVT_MENU, self.OnAddObject, id=addObject.GetId())
        else:
            addNew = wx.MenuItem(self, -1, 'Add &New Dataset')
            self.AppendItem(addNew)
            self.Bind(wx.EVT_MENU, self.OnAddDataset, id=addNew.GetId())

    def OnAddDataset(self, event):
        ds_dialog = ModanDatasetDialog(self.parent, -1)
        ds_dialog.SetDimension(str(self.dim))
        ds_dialog.ShowModal()
        self.parent.refresh_dataset()
        # print "add dataset"
        #self.Close()

    def OnEditDataset(self, event):
        self.frame.open_dataset_dialog()
        # self.parent.Refresh()
        #print "edit dataset"
        #self.Close()

    def OnDelDataset(self, event):
        self.frame.open_dataset_dialog()
        # self.parent.Refresh()
        #print "del dataset"
        #self.Close()

    def OnAddObject(self, event):
        self.frame.open_object_dialog()
        # self.parent.RefreshObjectList()
        # self.parent.
