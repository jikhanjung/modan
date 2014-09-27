import wx 
import xlrd
import os
import sqlite3

#import sys
from libpy.dataimporter import ModanDataImporter
from libpy.model_mdobject import MdObject
from libpy.model_mdlandmark import MdLandmark
from libpy.model_mddataset import MdDataset

DIALOG_SIZE = wx.Size(550,500) 
ID_SELECT_BUTTON = 1001
ID_IMPORT_BUTTON = 1002
ID_RADIO_FILETYPE = 1003
 
FILETYPE_TPS  = 0
FILETYPE_X1Y1 = 1
FILETYPE_MORPHOLOGIKA = 2
FILETYPE_EXCEL = 3
FILETYPE_LIST = [ 'TPS', 'X1Y1CS', 'Morphologika', 'EXCEL' ]

class ModanImportDialog( wx.Dialog ): 
  def __init__( self, parent, id ):
    wx.Dialog.__init__( self, parent, id, 'MdImport', size=DIALOG_SIZE)
    panel = wx.Panel(self, -1)
    self.importpath = ''

    self.forms = dict()
    self.dsname = None
    self.objectcount = 0
    self.importpath = ''
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    self.import_object = None

    # dataset name
    filenameLabel = wx.StaticText(panel, -1, 'Filename', style=wx.ALIGN_RIGHT)
    self.forms['filename'] = wx.TextCtrl(panel, -1, '')
    
    dsnameLabel = wx.StaticText(panel, -1, 'Dataset Name', style=wx.ALIGN_RIGHT)
    self.forms['dsname'] = wx.TextCtrl(panel, -1, '')

    # dataset description
    dsdescLabel = wx.StaticText(panel, -1, 'Description', style=wx.ALIGN_RIGHT)
    self.forms['dsdesc'] = wx.TextCtrl(panel, -1, '')

    objectsLabel = wx.StaticText(panel, -1, 'No. of objects', style=wx.ALIGN_RIGHT)
    self.forms['objects'] = wx.TextCtrl(panel, -1, '')
    statusLabel = wx.StaticText(panel, -1, 'Status', style=wx.ALIGN_RIGHT)
    self.forms['status'] = wx.TextCtrl(panel, -1, '')

    filetypeLabel = wx.StaticText(panel, -1, 'Filetype', style=wx.ALIGN_RIGHT)
    self.rdFiletype = wx.RadioBox( panel, ID_RADIO_FILETYPE, "", choices=FILETYPE_LIST, style=wx.RA_HORIZONTAL)
    self.Bind( wx.EVT_RADIOBOX, self.OnFiletype, id=ID_RADIO_FILETYPE)
    self.rdFiletype.SetSelection( FILETYPE_TPS )

    inputSizer = wx.FlexGridSizer( cols=2, hgap=10)
    inputSizer.AddGrowableCol(1)
    inputSizer.Add( filenameLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['filename'], 0, wx.EXPAND )
    inputSizer.Add( filetypeLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.rdFiletype, 0, wx.EXPAND )
    inputSizer.Add( dsnameLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['dsname'], 0, wx.EXPAND )
    inputSizer.Add( dsdescLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['dsdesc'], 0, wx.EXPAND )
    inputSizer.Add( objectsLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['objects'], 0, wx.EXPAND )
    inputSizer.Add( statusLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['status'], 0, wx.EXPAND )

    mainSizer.Add( inputSizer, 0, wx.EXPAND|wx.ALL, 10)
    
    selectFileButton = wx.Button(panel, ID_SELECT_BUTTON, 'Select')
    importButton = wx.Button(panel, ID_IMPORT_BUTTON, 'Execute import')
    self.Bind(wx.EVT_BUTTON, self.SelectFile, id=ID_SELECT_BUTTON)
    self.Bind(wx.EVT_BUTTON, self.ImportFile, id=ID_IMPORT_BUTTON)
    objectSizer_btn = wx.BoxSizer( wx.VERTICAL )
    objectSizer_btn.Add( selectFileButton, wx.EXPAND )
    objectSizer_btn.Add( importButton, wx.EXPAND )

    mainSizer.Add( objectSizer_btn, 0, wx.EXPAND|wx.ALL, 10)
    
    self.SelectFile( None )
    
    panel.SetSizer(mainSizer)
    panel.Fit()

  def OnFiletype(self, event):
    pass
  def SetProgress(self,percentage):
    self.forms['status'].SetValue( str( percentage ) + " % completed" )
    self.Update()
    
  def SelectFile(self,evt):
    wildcard = "All files (*.*)|*.*|" \
               "Excel file (*.xls)|*.xls|" \
               "TPS file (*.tps)|*.tps|" \
               "Morphologika file (*.*)|*.*" 

    dialog_style = wx.OPEN 

    selectfile_dialog = wx.FileDialog(self, "Select File to Import...", "", "", wildcard, dialog_style )
    if selectfile_dialog.ShowModal() == wx.ID_OK:
      self.importpath = selectfile_dialog.GetPath()
      #( unc, pathname ) = splitunc( self.importpath )
      fullpath = self.importpath
#      print pathname
      ( pathname, fname ) = os.path.split( fullpath )
      ( fname, ext ) = os.path.splitext( fname )
    else:
      return
    
    self.importer = ModanDataImporter( self )
    open_success = self.importer.checkFileType( fullpath )
    if not open_success:
      wx.MessageBox( "Cannot open selected file!" )
      return
    
    #print "filetype: ", FILETYPE_LIST[ self.importer.filetype ]
    #if importer.filetype == FILETYPE_MORPHOLOGIKA:
      #print "morphologika"
    #print "object: %d, landmarks: %d" % ( self.importer.object_count, self.importer.landmark_count )
    #print "dataset name: ", fname 
    #print importer.filetype, importer.data

    self.forms['objects'].SetValue( str( self.importer.object_count ) )
    #self.forms['status'].SetValue( str( self.importer.object_count )  + " objects" )
    self.forms['dsname'].SetValue( fname )
    self.forms['status'].SetValue( 'Ready to import' )
    self.forms['filename'].SetValue( fullpath )
    self.rdFiletype.SetSelection( self.importer.filetype )
    self.rdFiletype.Enable( False )
    self.dsname = fname 
    
    return
    
  def readExcelFile(self):
    book = xlrd.open_workbook(self.importpath)
    
    for sheet in book.sheets():
      sheetdata = []
      #print "row_values: "

      if sheet.nrows > 0 :
#      print sheet.row_values(1)
        for r in range(sheet.nrows):
          sheetdata.append( sheet.row_values ( r ) )
        di = ModanDataImporter( list=sheetdata )
        di.checkDataType()
    
  def ImportFile(self,event): 
    
    ''' error check '''
    if( self.importpath == '' ) :
      wx.MessageBox( "No file selected." )
      return
    elif(  self.importer.object_count == 0 ):
      wx.MessageBox( "No object detected." )
      return

    wx.BeginBusyCursor()
    self.importer.ImportDataset()
    wx.EndBusyCursor()
    self.Close()       
    return

  def AddObject(self, dsid, objectname, objectdata ):
    di = ModanDataImporter( list=objectdata )
    #print objectdata
    di.checkDataType()
    mo = MdObject()
    mo.objname = objectname
    mo.objdesc = ''
    mo.scale = ''
    mo.dataset_id = dsid
    seq = 0
    for lm in di.grid:
      seq = seq + 10
      mo.landmarks.append( MdLandmark(lmseq=seq,xcoord=lm[0],ycoord=lm[1],zcoord=lm[2]) )
    mo.insert()
    return 1

  def ImportExcelFile(self, dsid ):
    book = xlrd.open_workbook(self.importpath)
    #print "The number of worksheets is", book.nsheets
    processed_sheets = 0
    for sheet in book.sheets():
      #print "name: ", sheet.name
      #print "rows: ", sheet.nrows
      if sheet.name[0] == '#' : continue
      objectdata = []
      #print "row_values: "
      
      if sheet.nrows > 0 :
#      print sheet.row_values(1)
        for r in range(sheet.nrows):
          objectdata.append( sheet.row_values ( r ) )
        added = self.AddObject( dsid, sheet.name, objectdata )
        processed_sheets = processed_sheets + added
        percentage = ( float( processed_sheets ) / float ( self.objectcount) ) * 100
        self.forms['status'].SetValue( str( int( percentage ) ) + "% completed" )
        self.Update()
