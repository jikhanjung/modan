import wx
import os
import shutil
import sqlite3
#from rpy import *
 
#from gui.dialog_dataset import ModanDatasetDialog
from gui.main_tree import MdDatasetTree    
from gui.main_list import MdObjectList 
from gui.main_content import MdObjectContent 
from gui.dialog_object import ModanObjectDialog
from gui.dialog_import import ModanImportDialog
from gui.dialog_export import ModanExportDialog
from gui.dialog_dataset import ModanDatasetDialog
from gui.dialog_datasetviewer import ModanDatasetViewer
from gui.opengltest import OpenGLTestWin
from libpy.model_mdobject import MdObject
from libpy.model_mddataset import MdDataset
from libpy.modan_version import VersionControl, MODAN_VERSION, DB_VERSION

from libpy.dbi import ModanDBI  
from libpy.conf import ModanConf 
from libpy.modan_exception import MdException

windowSize = wx.Size(800,600)
treePaneWidth = 200 
minTreePaneWidth = 100
itemListHeight = 300
minItemPaneHeight = 200

ID_OBJECT_CONTENT = 77

ID_OPEN_DB = 1001
ID_NEW_DATASET = 1002
ID_SAVEAS = 1003
ID_IMPORT = 1004
ID_EXPORT = 1005
ID_ANALYZE = 1006
ID_NEW_OBJECT = 1007
ID_NEW_DATASET = 1008
ID_PREFERENCES = 1009
ID_NEW_DB = 1010
ID_ABOUT = 1011

class EmptyEvent( wx.Event ):
  def __init__ (self):
    return

class ModanFrame( wx.Frame):
  def __init__(self, parent, id, title):
    wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, windowSize )
    self.statusbar = self.CreateStatusBar()
    self.app = wx.GetApp()

    ## Toolbar
    toolbar = self.CreateToolBar()
    tool_image_opendb = wx.Bitmap( "icon/open.png", wx.BITMAP_TYPE_PNG )
    tool_image_newdb = wx.Bitmap( "icon/newdb.png", wx.BITMAP_TYPE_PNG )
    tool_image_saveas = wx.Bitmap( "icon/saveas.png", wx.BITMAP_TYPE_PNG )
    tool_image_newobject= wx.Bitmap( "icon/newobject.png", wx.BITMAP_TYPE_PNG )
    tool_image_newdataset= wx.Bitmap( "icon/newdataset.png", wx.BITMAP_TYPE_PNG )
    tool_image_export = wx.Bitmap( "icon/export.png", wx.BITMAP_TYPE_PNG )
    tool_image_import = wx.Bitmap( "icon/import.png", wx.BITMAP_TYPE_PNG )
    tool_image_analyze = wx.Bitmap( "icon/analyze.png", wx.BITMAP_TYPE_PNG )
    tool_image_preferences = wx.Bitmap( "icon/preferences.png", wx.BITMAP_TYPE_PNG )
    tool_image_about= wx.Bitmap( "icon/about.png", wx.BITMAP_TYPE_PNG )
    #tool_image_test = wx.Bitmap( "icon/test.bmp", wx.BITMAP_TYPE_BMP )
    toolbar.AddSimpleTool( ID_OPEN_DB, tool_image_opendb, "Open DB" )
    toolbar.AddSimpleTool( ID_NEW_DB, tool_image_newdb, "Create New DB" )
    toolbar.AddSimpleTool( ID_SAVEAS, tool_image_saveas, "SaveAs" )
    toolbar.AddSimpleTool( ID_NEW_DATASET, tool_image_newdataset, "New Dataset" )
    toolbar.AddSimpleTool( ID_NEW_OBJECT, tool_image_newobject, "New Object" )
    toolbar.AddSimpleTool( ID_EXPORT, tool_image_export, "Export Data" )
    toolbar.AddSimpleTool( ID_IMPORT, tool_image_import, "Import Data" )
    toolbar.AddSimpleTool( ID_ANALYZE, tool_image_analyze, "Analyze Data" )
    toolbar.AddSimpleTool( ID_PREFERENCES, tool_image_preferences, "Preferences" )
    toolbar.AddSimpleTool( ID_ABOUT, tool_image_about, "About" )
    #toolbar.AddSimpleTool( ID_TEST, tool_image_test, "Test" )
    toolbar.SetToolBitmapSize( wx.Size(32,32))
    toolbar.Realize()
    self.Bind( wx.EVT_TOOL, self.OpenDbDialog, id=ID_OPEN_DB)
    self.Bind( wx.EVT_TOOL, self.NewDbDialog, id=ID_NEW_DB)
    self.Bind( wx.EVT_TOOL, self.ObjectDialog, id=ID_NEW_OBJECT )
    self.Bind( wx.EVT_TOOL, self.DatasetDialog, id=ID_NEW_DATASET )
    self.Bind( wx.EVT_TOOL, self.SaveAs, id=ID_SAVEAS)
    self.Bind( wx.EVT_TOOL, self.ImportDialog, id=ID_IMPORT )
    self.Bind( wx.EVT_TOOL, self.ExportDialog, id=ID_EXPORT )
    self.Bind( wx.EVT_TOOL, self.AnalyzeDialog, id=ID_ANALYZE )
    self.Bind( wx.EVT_TOOL, self.PreferencesDialog, id=ID_PREFERENCES)
    self.Bind( wx.EVT_TOOL, self.AboutDialog, id=ID_ABOUT)

    ## Splitter
    self.treeSplitter = wx.SplitterWindow( self, -1, style= wx.SP_BORDER )
    self.treeSplitter.SetMinimumPaneSize( minTreePaneWidth )
    self.objectSplitter = wx.SplitterWindow( self.treeSplitter, -1, style=wx.SP_BORDER )
    self.objectSplitter.SetMinimumPaneSize( minItemPaneHeight )

    ## Dataset Tree
    self.app.objectContent = self.objectContent = MdObjectContent( self.objectSplitter, id=ID_OBJECT_CONTENT )
    self.app.objectList    = self.objectList = MdObjectList( self.objectSplitter, -1 )
    self.app.datasetTree   = self.datasetTree = MdDatasetTree( self.treeSplitter, -1 )

    ## Object content
    self.objectContent.Bind( wx.EVT_LEFT_DCLICK, self.OnDoubleClick, id=ID_OBJECT_CONTENT )

    ## Wrap up
    self.objectSplitter.SplitHorizontally( self.objectList, self.objectContent, itemListHeight )
    self.treeSplitter.SplitVertically( self.datasetTree, self.objectSplitter, treePaneWidth )
    self.Bind( wx.EVT_SIZE, self.OnResize )
    
    iconFile = "icon/modan.ico"        
    icon1 = wx.Icon(iconFile, wx.BITMAP_TYPE_ICO)        
    self.SetIcon(icon1)

  def OpenDbDialog(self, event ):
    newpath = self.OpenFileDialog( "Choose a DB file to open" )
    if( newpath != '' ):
      app = wx.GetApp()
      app.SetDbpath( newpath)
      app.CheckDB()
      self.RefreshTree()

  def NewDbDialog(self, event ):
    newpath = self.OpenFileDialog( "Create new DB file." )
    if( newpath != '' ):
      app = wx.GetApp()
      app.SetDbpath( newpath )
      app.CheckDB( newpath )
      self.RefreshTree()

  def AnalyzeDialog(self, event):
    selected_item = self.datasetTree.GetSelection()
    if not selected_item:
      wx.MessageBox( "You should select a dataset to export.")
      return
    dsname = self.datasetTree.GetItemText(selected_item)

    wx.BeginBusyCursor()
    ds = MdDataset()
    ds = ds.find_by_name( dsname )[0]
    ds.load_objects()
    try:
      ds.procrustes_superimposition()
    except MdException, e:
      wx.MessageBox( str( e ) )
      wx.EndBusyCursor()
      return
    wx.EndBusyCursor()
    ds.reference_shape.dataset_id = ds.id
    og = ModanDatasetViewer(self)
    og.SetDataset( ds )
    og.SetObject( ds.reference_shape )
    og.ShowModal()
    og.Destroy()
    
    
  def SaveAs(self, event ):
    #openglwin = OpenGLTestWin(self)
    #openglwin.Show()
    newpath = self.OpenFileDialog( "Save As...", 'save' )
    if newpath != '':
      shutil.copyfile( wx.GetApp().GetDbpath(), newpath )
      wx.GetApp().SetDbpath( newpath)
    
  def OpenFileDialog( self, message = 'Choose a file', mode = 'open' ):
    wildcard = "Modan DB file (*.moa)|*.moa|" \
               "All files (*.*)|*.*"
#    fileDialog = wx.FileDialog(None, "Choose a file", os.getcwd(),
#                 "", wildcard, wx.SAVE | wx.OVERWRITE_PROMPT | wx.CHANGE_DIR )
    if( mode == 'save' ):
      dialog_style = wx.SAVE | wx.OVERWRITE_PROMPT
    else: 
      dialog_style = wx.OPEN 

    file_dialog = wx.FileDialog(self, message, "", "", wildcard, dialog_style  )
    newpath = ''
    if file_dialog.ShowModal() == wx.ID_OK:
      newpath = file_dialog.GetPath()
      #wx.MessageBox( self.filename )
    file_dialog.Destroy()
    return newpath

  def DatasetDialog(self,event):
    ds_dialog = ModanDatasetDialog( self.datasetTree, -1 )
    #ds_dialog.SetDimension( str( self.dim ) )
    ret = ds_dialog.ShowModal()
    if ret == wx.ID_EDIT:
      self.datasetTree.Refresh()
    #wx.MessageBox('dataset dialog')

  def PreferencesDialog(self,event):
    return
    wx.MessageBox('preferences dialog will show up.. someday.')

  def AboutDialog(self, event ):
    wx.MessageBox( "Modan version " + MODAN_VERSION + "\nCopyright (c) 2009 Jikhan Jung. All rights reserved."  )
    
  def ObjectDialog( self, event ):
    app = wx.GetApp()
      
    new_dialog = ModanObjectDialog( self, -1 )
    mo = MdObject()
    if app.datasetTree.dataset_selected:
      mo.dataset_id = app.datasetTree.dataset.id
      dsname = app.datasetTree.dataset.dsname
      new_dialog.SetDatasetCombobox( sel=dsname )
      #new_dialog.SetDataset( app.datasetTree.dataset )
      new_dialog.dsid = app.datasetTree.dataset.id
    new_dialog.SetModanObject( mo )
    new_dialog.ShowModal()
    #self.datasetTree.Refresh()
    new_dialog.Destroy()
    
  def ImportDialog( self, event ):
    importDlg = ModanImportDialog( self, -1 )
    importDlg.ShowModal()
    importDlg.Destroy()
    self.datasetTree.Refresh()

  def ExportDialog( self, event ):
    export_dialog = ModanExportDialog( self, -1 )
    selected_item = self.datasetTree.GetSelection()
    #if( selected_item )
    if not selected_item:
      wx.MessageBox( "You should select a dataset to export.")
      return
    
    dsname = self.datasetTree.GetItemText(selected_item)
    #print dsname
    ds = MdDataset()
    ds = ds.find_by_name( dsname )
    ds[0].load_objects()
    #print "ds[0]"
    #mo = MdObject()
    #mos = mo.find_by_dataset_name( dsname )
    export_dialog.SetDataset( ds[0] )
    export_dialog.SetExportList( ds[0].objects )
    #print ds[0].objects
    export_dialog.ShowModal()
    export_dialog.Destroy()

  def OnResize( self, event ):
    self.objectList.OnResize()
    event.Skip()

  def OnDoubleClick( self, event ):
    pass
  
  def RefreshTree(self):
    self.datasetTree.Refresh()
