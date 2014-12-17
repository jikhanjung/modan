#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
from libpy.modan_dbclass import MdDataset,MdPropertyName
from gui.dialog_propertyname import ModanPropertynameDialog
ID_SAVE_BUTTON = 2000
ID_DELETE_BUTTON = 2001
ID_CLOSE_BUTTON = 2002
ID_PROPERTY_BUTTON = 2004
#ID_TEST2_BUTTON = 2005
ID_TEXT_WIREFRAME = 2010
ID_TEXT_POLYGONS = 2011

DIALOG_SIZE = wx.Size(400, 400)


class ModanDatasetDialog(wx.Dialog):
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, 'Edit Dataset', size=DIALOG_SIZE)
        panel = wx.Panel(self, -1)
        self.dataset = None
        self.app = wx.GetApp()

        self.forms = {}
        self.edge_list = []

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        ## ID
        IDLabel = wx.StaticText(panel, -1, 'ID', style=wx.ALIGN_CENTER)
        self.forms['id'] = wx.StaticText(panel, -1, '', size=(30, -1), style=wx.ALIGN_LEFT)
        self.forms['id'].SetBackgroundColour('#aaaaaa')

        headSizer = wx.BoxSizer(wx.HORIZONTAL)
        headSizer.Add(IDLabel)
        headSizer.Add(self.forms['id'])
        mainSizer.Add(headSizer, 0, wx.EXPAND | wx.ALL, 10)

        # dataset name
        dsnameLabel = wx.StaticText(panel, -1, 'Dataset Name', style=wx.ALIGN_RIGHT)
        self.forms['dsname'] = wx.TextCtrl(panel, -1, '')
        # dataset description
        dsdescLabel = wx.StaticText(panel, -1, 'Description', style=wx.ALIGN_RIGHT)
        self.forms['dsdesc'] = wx.TextCtrl(panel, -1, '', style=wx.TE_MULTILINE)
        self.forms['dsdesc'].SetMinSize((300, 50))
        # dataset groupname
        propertiesLabel = wx.StaticText(panel, -1, 'Properties', style=wx.ALIGN_CENTER)
        self.forms['properties'] = wx.ListBox( panel, -1, choices=(),size=(150,50), style=wx.LB_EXTENDED )
        # wireframe
        wireframeLabel = wx.StaticText(panel, -1, 'Wireframe', style=wx.ALIGN_CENTER)
        self.forms['wireframe'] = wx.TextCtrl(panel, ID_TEXT_WIREFRAME, '')  #wx.TextCtrl(panel, -1, '')
        # polygons
        polygonsLabel = wx.StaticText(panel, -1, 'Polygons', style=wx.ALIGN_CENTER)
        self.forms['polygons'] = wx.TextCtrl(panel, ID_TEXT_POLYGONS, '')  #wx.TextCtrl(panel, -1, '')

        # dataset dimension
        dimensionLabel = wx.StaticText(panel, -1, 'Dimension', style=wx.ALIGN_CENTER)
        self.forms['dimension'] = wx.ComboBox(panel, -1, "2", (15, 30), wx.DefaultSize, ['2', '3'], wx.CB_DROPDOWN)

        # baseline
        baselineLabel = wx.StaticText(panel, -1, 'Baseline', style=wx.ALIGN_CENTER)
        self.forms['baseline'] = wx.TextCtrl(panel, -1, '')

        editpropertyButton = wx.Button(panel, ID_PROPERTY_BUTTON, '+')
        self.Bind(wx.EVT_BUTTON, self.OnProperty, id=ID_PROPERTY_BUTTON)

        inputSizer = wx.FlexGridSizer(cols=2, hgap=10)
        inputSizer.AddGrowableCol(1)
        inputSizer.Add(dsnameLabel, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        inputSizer.Add(self.forms['dsname'], 0, wx.EXPAND)
        inputSizer.Add(dsdescLabel, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        inputSizer.Add(self.forms['dsdesc'], 0, wx.EXPAND)
        inputSizer.Add(dimensionLabel, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        inputSizer.Add(self.forms['dimension'], 0, wx.EXPAND)
        inputSizer.Add(wireframeLabel, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        inputSizer.Add(self.forms['wireframe'], 0, wx.EXPAND)
        inputSizer.Add(polygonsLabel, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        inputSizer.Add(self.forms['polygons'], 0, wx.EXPAND)
        inputSizer.Add(baselineLabel, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        inputSizer.Add(self.forms['baseline'], 0, wx.EXPAND)
        inputSizer.Add(propertiesLabel, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)



        propertySizer = wx.BoxSizer(wx.HORIZONTAL)
        propertySizer.Add(self.forms['properties'], 0, wx.EXPAND)
        propertySizer.Add(editpropertyButton, 0,wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        inputSizer.Add(propertySizer, 0, wx.EXPAND)
        mainSizer.Add(inputSizer, 0, wx.EXPAND | wx.ALL, 10)

        ## Buttons
        saveButton = wx.Button(panel, ID_SAVE_BUTTON, 'Save')
        deleteButton = wx.Button(panel, ID_DELETE_BUTTON, 'Delete')
        closeButton = wx.Button(panel, ID_CLOSE_BUTTON, 'Close')
        #wireframeButton = wx.Button(panel, ID_WIREFRAME_BUTTON, 'Edit Wireframe')
        #testButton = wx.Button(panel, ID_TEST_BUTTON, 'Test')
        #    test2Button = wx.Button(panel, ID_TEST2_BUTTON, 'Test2')
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=ID_SAVE_BUTTON)
        self.Bind(wx.EVT_BUTTON, self.OnDelete, id=ID_DELETE_BUTTON)
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=ID_CLOSE_BUTTON)
        #self.Bind(wx.EVT_BUTTON, self.OnWireframe, id=ID_WIREFRAME_BUTTON)
        #self.Bind(wx.EVT_BUTTON, self.OnTest, id=ID_TEST_BUTTON)
        #    self.Bind(wx.EVT_BUTTON, self.OnTest2, id=ID_TEST2_BUTTON)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add((10, 10), wx.EXPAND)
        buttonSizer.Add(saveButton, wx.EXPAND)
        buttonSizer.Add(deleteButton, wx.EXPAND)
        buttonSizer.Add(closeButton, wx.EXPAND)
        #buttonSizer.Add(wireframeButton, wx.EXPAND)
        #buttonSizer.Add(testButton, wx.EXPAND)
        #    buttonSizer.Add(test2Button, wx.EXPAND)
        buttonSizer.Add((10, 10), wx.EXPAND)
        mainSizer.Add(buttonSizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(mainSizer)
        panel.Fit()


    def SetMdDataset(self, ds):
        self.dataset = ds
        self.forms['id'].SetLabel(str(ds.id))
        self.forms['dsname'].SetValue(ds.dsname)
        self.forms['dsdesc'].SetValue(ds.dsdesc)
        self.forms['dimension'].SetValue(str(ds.dimension))

        #self.dataset.unpack_wireframe()
        #self.dataset.unpack_baseline()
        #self.dataset.unpack_groupname()
        #self.dataset.unpack_polygons()
        self.forms['wireframe'].SetValue(ds.wireframe)
        self.forms['baseline'].SetValue(ds.baseline)
        #self.forms['groupname'].SetValue(ds.groupname)
        self.forms['polygons'].SetValue(ds.polygons)
        self.load_properties()

        #print ds.groupname_list
        #self.forms['groupname'].SetValue( ds.groupname )
        #ds.set_wireframe()

    def OnProperty(self, event):
        property_list = []
        for i in range(self.forms['properties'].GetCount()):
            property_list.append(self.forms['properties'].GetClientData(i))
        dlg = ModanPropertynameDialog(self)
        dlg.load_propertyname(property_list)
        ret = dlg.ShowModal()
        if ret == wx.ID_EDIT:
            self.forms['properties'].Clear()
            #self.load_properties()
            for i in range(dlg.list1.GetCount()):
                pn = dlg.list1.GetClientData(i)
                self.forms['properties'].Append( pn.propertyname, pn )
            #self.refresh_tree()

    def load_properties(self):
        self.forms['properties'].Clear()
        for pn in self.dataset.propertyname_list:
            self.forms['properties'].Append( pn.propertyname, pn )

    def OnSave(self, event):
        if self.dataset is None:
            self.dataset = MdDataset()

        session = self.app.get_session()
        session.add( self.dataset )

        self.dataset.dsname = self.forms['dsname'].GetValue()
        self.dataset.dsdesc = self.forms['dsdesc'].GetValue()
        self.dataset.baseline = self.forms['baseline'].GetValue()
        self.dataset.wireframe = self.forms['wireframe'].GetValue()
        self.dataset.polygons = self.forms['polygons'].GetValue()
        self.dataset.dimension = self.forms['dimension'].GetValue()
        property_list = []
        for i in range(self.forms['properties'].GetCount()):
            property_list.append(self.forms['properties'].GetClientData(i))

        for p in self.dataset.propertyname_list:
            if p not in property_list:
                self.dataset.propertyname_list.remove(p)

        for p in property_list:
            if p not in self.dataset.propertyname_list:
                self.dataset.propertyname_list.append(p)

        session.commit()
        #print self.dataset.dsname

        self.EndModal(wx.ID_EDIT)

    def OnDelete(self, event):
        dsid = int( self.forms['id'].GetLabel() )
        if dsid > 0:
            msg_box = wx.MessageDialog(self, "Do you really want to delete?", "Warning",
                                       wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE | wx.ICON_EXCLAMATION)
            result = msg_box.ShowModal()
            if ( result == wx.ID_YES ):
                session = self.app.get_session()
                session.add( self.dataset )
                session.delete(self.dataset)
                session.commit()
                self.EndModal(wx.ID_EDIT)

    def OnClose(self, event):
        self.EndModal(wx.ID_OK)

    def SetDatasetContent(self, ds):
        if ( ds.id ):
            #self.forms['id'].SetValue( ds.id )
            self.forms['dsname'].SetValue(ds.dsname)
            self.forms['dsdesc'].SetValue(ds.dsdesc)
            self.forms['dimension'].SetValue(str(ds.dimension))
            #self.forms['groupname'].SetValue(ds.groupname)
            self.forms['baseline'].SetValue(ds.baseline)
            self.forms['polygons'].SetValue(ds.polygons)
            self.forms['wireframe'].SetValue(ds.wireframe)

    def SetDimension(self, dim):
        if ( dim ):
            self.forms['dimension'].SetValue(str(dim))

    def OnTest(self, event):
        return
