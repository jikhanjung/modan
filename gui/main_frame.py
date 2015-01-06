#!/usr/bin/env python
# -*- coding: utf-8 -*-
import wx
import shutil
from gui.main_tree import MdDatasetTree
from gui.main_list import MdObjectList
from gui.main_content import MdObjectContent
from gui.dialog_object import ModanObjectDialog
from gui.dialog_import import ModanImportDialog
from gui.dialog_export import ModanExportDialog
from gui.dialog_dataset import ModanDatasetDialog
from gui.dialog_datasetviewer import ModanDatasetViewer
from libpy.modan_version import MODAN_VERSION

CONST = {}
CONST['WINDOW_SIZE'] = wx.Size(800, 600)
CONST['TREE_PANE_WIDTH'] = 200
CONST['MIN_TREE_PANE_WIDTH'] = 100
CONST['ITEM_LIST_HEIGHT'] = 300
CONST['MIN_ITEM_PANE_HEIGHT'] = 200

CONTROL_ID = {}
CONTROL_ID['ID_OBJECT_CONTENT'] = 77
CONTROL_ID['ID_OPEN_DB'] = 1001
CONTROL_ID['ID_NEW_DATASET'] = 1002
CONTROL_ID['ID_SAVEAS'] = 1003
CONTROL_ID['ID_IMPORT'] = 1004
CONTROL_ID['ID_EXPORT'] = 1005
CONTROL_ID['ID_ANALYZE'] = 1006
CONTROL_ID['ID_NEW_OBJECT'] = 1007
CONTROL_ID['ID_PREFERENCES'] = 1009
CONTROL_ID['ID_NEW_DB'] = 1010
CONTROL_ID['ID_ABOUT'] = 1011


class EmptyEvent(wx.Event):
    def __init__(self):
        wx.Event.__init__(self)
        return


class ModanFrame(wx.Frame):
    def __init__(self, parent, wid, title):
        wx.Frame.__init__(self, parent, wid, title, wx.DefaultPosition, CONST['WINDOW_SIZE'])
        self.statusbar = self.CreateStatusBar()
        self.app = wx.GetApp()
        self.object_list_proportion = -1

        # # Toolbar
        toolbar = self.CreateToolBar()
        tool_image_opendb = wx.Bitmap("icon/open.png", wx.BITMAP_TYPE_PNG)
        tool_image_newdb = wx.Bitmap("icon/newdb.png", wx.BITMAP_TYPE_PNG)
        tool_image_saveas = wx.Bitmap("icon/saveas.png", wx.BITMAP_TYPE_PNG)
        tool_image_newobject = wx.Bitmap("icon/newobject.png", wx.BITMAP_TYPE_PNG)
        tool_image_newdataset = wx.Bitmap("icon/newdataset.png", wx.BITMAP_TYPE_PNG)
        tool_image_export = wx.Bitmap("icon/export.png", wx.BITMAP_TYPE_PNG)
        tool_image_import = wx.Bitmap("icon/import.png", wx.BITMAP_TYPE_PNG)
        tool_image_analyze = wx.Bitmap("icon/analyze.png", wx.BITMAP_TYPE_PNG)
        tool_image_preferences = wx.Bitmap("icon/preferences.png", wx.BITMAP_TYPE_PNG)
        tool_image_about = wx.Bitmap("icon/about.png", wx.BITMAP_TYPE_PNG)

        toolbar.AddSimpleTool(CONTROL_ID['ID_OPEN_DB'], tool_image_opendb, "Open DB")
        toolbar.AddSimpleTool(CONTROL_ID['ID_NEW_DB'], tool_image_newdb, "Create New DB")
        toolbar.AddSimpleTool(CONTROL_ID['ID_SAVEAS'], tool_image_saveas, "SaveAs")
        toolbar.AddSimpleTool(CONTROL_ID['ID_NEW_DATASET'], tool_image_newdataset, "New Dataset")
        toolbar.AddSimpleTool(CONTROL_ID['ID_NEW_OBJECT'], tool_image_newobject, "New Object")
        toolbar.AddSimpleTool(CONTROL_ID['ID_EXPORT'], tool_image_export, "Export Data")
        toolbar.AddSimpleTool(CONTROL_ID['ID_IMPORT'], tool_image_import, "Import Data")
        toolbar.AddSimpleTool(CONTROL_ID['ID_ANALYZE'], tool_image_analyze, "Analyze Data")
        toolbar.AddSimpleTool(CONTROL_ID['ID_PREFERENCES'], tool_image_preferences, "Preferences")
        toolbar.AddSimpleTool(CONTROL_ID['ID_ABOUT'], tool_image_about, "About")

        toolbar.SetToolBitmapSize(wx.Size(32, 32))
        toolbar.Realize()
        self.Bind(wx.EVT_TOOL, self.open_db_dialog, id=CONTROL_ID['ID_OPEN_DB'])
        self.Bind(wx.EVT_TOOL, self.new_db_dialog, id=CONTROL_ID['ID_NEW_DB'])
        self.Bind(wx.EVT_TOOL, self.object_dialog, id=CONTROL_ID['ID_NEW_OBJECT'])
        self.Bind(wx.EVT_TOOL, self.dataset_dialog, id=CONTROL_ID['ID_NEW_DATASET'])
        self.Bind(wx.EVT_TOOL, self.save_as, id=CONTROL_ID['ID_SAVEAS'])
        self.Bind(wx.EVT_TOOL, self.import_dialog, id=CONTROL_ID['ID_IMPORT'])
        self.Bind(wx.EVT_TOOL, self.export_dialog, id=CONTROL_ID['ID_EXPORT'])
        self.Bind(wx.EVT_TOOL, self.analyze_dialog, id=CONTROL_ID['ID_ANALYZE'])
        self.Bind(wx.EVT_TOOL, self.preferences_dialog, id=CONTROL_ID['ID_PREFERENCES'])
        self.Bind(wx.EVT_TOOL, self.about_dialog, id=CONTROL_ID['ID_ABOUT'])

        ## Splitter
        self.tree_splitter = wx.SplitterWindow(self, -1, style=wx.SP_BORDER)
        self.tree_splitter.SetMinimumPaneSize(CONST['MIN_TREE_PANE_WIDTH'])
        self.object_splitter = wx.SplitterWindow(self.tree_splitter, -1, style=wx.SP_BORDER)
        self.object_splitter.SetMinimumPaneSize(CONST['MIN_ITEM_PANE_HEIGHT'])

        ## Dataset Tree
        self.object_content_pane = MdObjectContent(self.object_splitter, CONTROL_ID['ID_OBJECT_CONTENT'], frame=self)
        self.object_list_pane = MdObjectList(self.object_splitter, -1, frame=self)
        self.dataset_tree_pane = MdDatasetTree(self.tree_splitter, -1, frame=self)

        ## Object content
        self.object_content_pane.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click, id=CONTROL_ID['ID_OBJECT_CONTENT'])

        ## Wrap up
        self.object_splitter.SplitHorizontally(self.object_list_pane, self.object_content_pane, CONST['ITEM_LIST_HEIGHT'])
        self.tree_splitter.SplitVertically(self.dataset_tree_pane, self.object_splitter, CONST['TREE_PANE_WIDTH'])
        self.Bind(wx.EVT_SIZE, self.on_resize)

        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_sash_move)

        icon_file = "icon/modan.ico"
        icon1 = wx.Icon(icon_file, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon1)
        self.object_list_proportion = self.object_list_pane.GetSize()[1] / float( self.GetClientSize()[1])
        #print self.object_list_proportion
        #print self.GetClientSize(), self.object_splitter.GetSize(), self.object_list_pane.GetSize()
        #print

    def on_sash_move(self,event):
        #print self.object_splitter.GetSashPosition()
        #print self.object_splitter.GetSashSize()
        #print "new proportion:", self.object_splitter.GetSize()[1], "=", self.object_list_pane.GetSize()[1], 'vs', self.object_content_pane.GetSize()[1], '+', self.object_splitter.GetSashSize(), "to", self.object_splitter.GetSashPosition()
        #print self.object_splitter.GetSize(), self.object_list_pane.GetSize(), self.object_content_pane.GetSize()
        self.object_list_proportion = self.object_splitter.GetSashPosition() / float(self.object_list_pane.GetSize()[1] + self.object_content_pane.GetSize()[1])
        #print self.object_list_pane.GetSize()[1], self.object_list_pane.GetSize()[1], self.object_content_pane.GetSize()[1]
        #print "object_list proportion",self.object_list_proportion

    def open_db_dialog(self, event):
        newpath = self.open_file_dialog("Choose a DB file to open")
        if newpath != '':
            self.app.SetDBFilePath(newpath)
            self.app.CheckDB()
            self.refresh_tree()

    def new_db_dialog(self, event):
        newpath = self.open_file_dialog("Create new DB file.")
        if newpath != '':
            self.app.SetDBFilePath(newpath)
            self.app.CheckDB(newpath)
            self.refresh_tree()

    def analyze_dialog(self, event):
        selected_item = self.dataset_tree_pane.GetSelection()
        if not selected_item:
            wx.MessageBox("You should select a dataset to analyze.")
            return
        ds = self.dataset_tree_pane.GetItemPyData(selected_item)
        #ds.reference_shape.dataset_id = ds.id
        og = ModanDatasetViewer(self)
        og.SetDataset(ds)
        og.ShowModal()

    def save_as(self, event):
        newpath = self.open_file_dialog("Save As...", 'save')
        if newpath != '':
            shutil.copyfile(self.app.GetDBFilePath(), newpath)
            self.app.SetDBFilePath(newpath)

    def open_file_dialog(self, message='Choose a file', mode='open'):
        """

        :rtype : string
        """
        wildcard = "Modan DB file (*.moa)|*.moa|" \
                   "All files (*.*)|*.*"
        # fileDialog = wx.FileDialog(None, "Choose a file", os.getcwd(),
        #                 "", wildcard, wx.SAVE | wx.OVERWRITE_PROMPT | wx.CHANGE_DIR )
        if mode == 'save':
            dialog_style = wx.SAVE | wx.OVERWRITE_PROMPT
        else:
            dialog_style = wx.OPEN

        file_dialog = wx.FileDialog(self, message, "", "", wildcard, dialog_style)
        newpath = ''
        if file_dialog.ShowModal() == wx.ID_OK:
            newpath = file_dialog.GetPath()
            #wx.MessageBox( self.filename )
        file_dialog.Destroy()
        return newpath

    def dataset_dialog(self, event):
        self.open_dataset_dialog()

    def open_dataset_dialog(self, dataset=None,dim=-1):
        ds_dialog = ModanDatasetDialog(self.dataset_tree_pane, -1)
        if dataset is not None:
            ds_dialog.SetMdDataset(dataset)
        if dim > 0:
            ds_dialog.SetDimension(dim)
        ret = ds_dialog.ShowModal()
        if ret == wx.ID_EDIT:
            self.refresh_tree()

    def object_dialog(self, event):
        self.open_object_dialog()

    def open_object_dialog(self, mdobject=None):
        if not self.dataset_tree_pane.dataset_selected:
            wx.MessageBox("Select a dataset first.")
            return

        new_dialog = ModanObjectDialog(self, -1)
        new_dialog.SetDataset(self.dataset_tree_pane.dataset)
        if mdobject:
            new_dialog.set_mdobject(mdobject)
        ret = new_dialog.ShowModal()
        if ret == wx.ID_EDIT:
            print "refresh tree"
            self.refresh_tree()

    def preferences_dialog(self, event):
        return

    def about_dialog(self, event):
        wx.MessageBox("Modan version " + MODAN_VERSION + "\nCopyright (c) 2009-2014 Jikhan Jung. All rights reserved.")

    def import_dialog(self, event):
        import_dlg = ModanImportDialog(self, -1)
        import_dlg.ShowModal()
        self.refresh_tree()

    def export_dialog(self, event):
        export_dialog = ModanExportDialog(self, -1)
        selected_item = self.dataset_tree_pane.GetSelection()
        # if( selected_item )
        if not selected_item:
            wx.MessageBox("You should select a dataset to export.")
            return

        ds = self.dataset_tree_pane.GetItemPyData(selected_item)
        export_dialog.SetDataset(ds)
        export_dialog.SetExportList(ds.object_list)
        #print ds[0].objects
        export_dialog.ShowModal()
        export_dialog.Destroy()

    def on_resize(self, event):
        #print self.object_list_pane.GetSize()[1], self.object_list_pane.GetSize()[1], self.object_content_pane.GetSize()[1]
        #print "object_list proportion",self.object_list_proportion

        if self.object_list_proportion > 0:
            object_pane_width, new_total_height = self.object_splitter.GetSize()

            new_list_height = int( ( new_total_height - self.object_splitter.GetSashSize() ) * self.object_list_proportion )
            #print self.object_list_proportion, object_pane_width, new_list_height, new_total_height
            self.object_splitter.SetSashPosition( new_list_height )

        self.object_list_pane.OnResize()
        event.Skip()

    def on_double_click(self, event):
        pass

    def refresh_tree(self):
        self.dataset_tree_pane.refresh_dataset()

    def refresh_list(self):
        self.dataset_tree_pane.refresh_object_list()
