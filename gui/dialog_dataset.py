import wx
#import sys
#import libpy.conf import ModanConf
#from libpy.conf import ModanConf as ModanConf
  
#from libpy.conf import ModanConf
from libpy.model_mddataset import MdDataset
from libpy.model_mdobject import MdObject
from gui.opengltest import MdCanvas#, OpenGLTestWin
from gui.dialog_datasetviewer import ModanDatasetViewer
from libpy.modan_exception import MdException

ID_SAVE_BUTTON = 2000
ID_DELETE_BUTTON = 2001
ID_CLOSE_BUTTON = 2002
ID_TEST_BUTTON = 2004
#ID_TEST2_BUTTON = 2005
ID_TEXT_WIREFRAME = 2010
ID_TEXT_POLYGONS = 2011

DIALOG_SIZE = wx.Size( 400, 300 )

class ModanDatasetDialog( wx.Dialog ):
  def __init__( self, parent, id ):
    wx.Dialog.__init__( self, parent, id, 'Edit Dataset', size=DIALOG_SIZE)
    panel = wx.Panel(self, -1)
    self.forms = dict()
    self.dsname = None
    self.dsid = None
    self.dataset = MdDataset
    self.edge_list = []
    
    mainSizer = wx.BoxSizer(wx.VERTICAL)

    ## ID
    IDLabel = wx.StaticText(panel, -1, 'ID', style=wx.ALIGN_CENTER)
    self.forms['id'] = wx.StaticText(panel, -1, '', size=(30,-1), style=wx.ALIGN_LEFT)
    self.forms['id'].SetBackgroundColour('#aaaaaa')

    headSizer = wx.BoxSizer(wx.HORIZONTAL)
    headSizer.Add(IDLabel)
    headSizer.Add(self.forms['id'])
    mainSizer.Add( headSizer, 0, wx.EXPAND|wx.ALL, 10)

    # dataset name
    dsnameLabel = wx.StaticText(panel, -1, 'Dataset Name', style=wx.ALIGN_RIGHT)
    self.forms['dsname'] = wx.TextCtrl(panel, -1, '')
    # dataset description
    dsdescLabel = wx.StaticText(panel, -1, 'Description', style=wx.ALIGN_RIGHT)
    self.forms['dsdesc'] = wx.TextCtrl(panel, -1, '', style=wx.TE_MULTILINE)
    self.forms['dsdesc'].SetMinSize((300,50))
    # dataset groupname 
    groupnameLabel = wx.StaticText(panel, -1, 'Group Name', style=wx.ALIGN_CENTER)
    self.forms['groupname'] = wx.TextCtrl(panel, -1, '')
    # wireframe
    wireframeLabel = wx.StaticText(panel, -1, 'Wireframe', style=wx.ALIGN_CENTER)
    self.forms['wireframe'] = wx.TextCtrl( panel, ID_TEXT_WIREFRAME, '' ) #wx.TextCtrl(panel, -1, '')
    # polygons
    polygonsLabel = wx.StaticText(panel, -1, 'Polygons', style=wx.ALIGN_CENTER)
    self.forms['polygons'] = wx.TextCtrl( panel, ID_TEXT_POLYGONS, '' ) #wx.TextCtrl(panel, -1, '')
#    self.SetWireframeCombobox()
    #self.groupnameLabel = wx.StaticText(panel, -1, 'Groupnames', style=wx.ALIGN_CENTER)
    #self.forms['groupname'] = wx.TextCtrl(panel, -1, '', style=wx.TE_MULTILINE)
    #self.forms['groupname'].SetMinSize((300,100))
    #self.Bind( wx.EVT_COMBOBOX, self.OnWireframeChange, id=ID_COMBO_WIREFRAME)

    # dataset dimension
    dimensionLabel = wx.StaticText(panel, -1, 'Dimension', style=wx.ALIGN_CENTER)
    self.forms['dimension'] = wx.ComboBox(panel, -1, "2", (15, 30), wx.DefaultSize, ['2','3'], wx.CB_DROPDOWN )

    # baseline
    baselineLabel = wx.StaticText(panel, -1, 'Baseline', style=wx.ALIGN_CENTER)
    self.forms['baseline'] = wx.TextCtrl(panel, -1, '')
    
    inputSizer = wx.FlexGridSizer( cols=2, hgap=10)
    inputSizer.AddGrowableCol(1)
    inputSizer.Add( dsnameLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['dsname'], 0, wx.EXPAND )
    inputSizer.Add( dsdescLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['dsdesc'], 0, wx.EXPAND )
    inputSizer.Add( dimensionLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['dimension'], 0, wx.EXPAND )
    inputSizer.Add( wireframeLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['wireframe'], 0, wx.EXPAND )
    inputSizer.Add( polygonsLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['polygons'], 0, wx.EXPAND )
    inputSizer.Add( baselineLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['baseline'], 0, wx.EXPAND )
    inputSizer.Add( groupnameLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['groupname'], 0, wx.EXPAND )
    mainSizer.Add( inputSizer, 0, wx.EXPAND|wx.ALL, 10)
    
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
    buttonSizer.Add((10,10), wx.EXPAND)
    buttonSizer.Add(saveButton, wx.EXPAND)
    buttonSizer.Add(deleteButton, wx.EXPAND)
    buttonSizer.Add(closeButton, wx.EXPAND)
    #buttonSizer.Add(wireframeButton, wx.EXPAND)
    #buttonSizer.Add(testButton, wx.EXPAND)
#    buttonSizer.Add(test2Button, wx.EXPAND)
    buttonSizer.Add((10,10), wx.EXPAND)
    mainSizer.Add(buttonSizer, 0, wx.EXPAND|wx.ALL, 10)

    panel.SetSizer(mainSizer)
    panel.Fit()  


  def SetMdDataset(self, ds ):
    self.dataset = ds
    self.dsid = ds.id
    self.forms['id'].SetLabel( str( ds.id ) )
    self.forms['dsname'].SetValue( ds.dsname )
    self.forms['dsdesc'].SetValue(  ds.dsdesc )
    self.forms['dimension'].SetValue(  str( ds.dimension ) )
    
    self.dataset.unpack_wireframe()
    self.dataset.unpack_baseline()
    self.dataset.unpack_groupname()
    self.dataset.unpack_polygons()
    self.forms['wireframe'].SetValue(  ds.wireframe )
    self.forms['baseline'].SetValue(  ds.baseline )
    self.forms['groupname'].SetValue(  ds.groupname )
    self.forms['polygons'].SetValue(  ds.polygons )
    
    #print ds.groupname_list
    #self.forms['groupname'].SetValue( ds.groupname )
    #ds.set_wireframe()
  
  def OnSave( self, event ):
    ds = MdDataset()
    ds.id = self.forms['id'].GetLabelText()
    ds.dsname = self.forms['dsname'].GetValue()
    ds.dsdesc = self.forms['dsdesc'].GetValue()
    ds.baseline = self.forms['baseline'].GetValue()
    ds.wireframe = self.forms['wireframe'].GetValue()
    ds.polygons = self.forms['polygons'].GetValue()
    ds.dimension = self.forms['dimension'].GetValue()
    ds.groupname = self.forms['groupname'].GetValue()
    #if( len( self.wireframe ) > 0 ):
    #ds.wireframe_id = self.wireframe_id

    if( ds.id != '' ) :
      #print "update"
      try:
        ds.update()
      except:
        print "error update"
    else:
      #print "insert"
      try:
        ds.insert()
      except:
        print "error insert"
    #e = ''
    
    self.dsname = ds.dsname
    self.dsid = ds.id
    #self.GetParent().Refresh( self.dsid )
    self.EndModal( wx.ID_EDIT )

  def OnDelete( self, event ):
    msg_box = wx.MessageDialog(self, "Do you really want to delete?", "Warning", wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE | wx.ICON_EXCLAMATION )
    result = msg_box.ShowModal()
    if( result == wx.ID_YES ):
      ds = MdDataset()
      ds.id = int(self.forms['id'].GetLabel())
      if( ds.id ): 
        ds.delete()
        # print "delete done"
        self.GetParent().Refresh()
        self.EndModal(wx.ID_DELETE)

  def OnClose( self, event ):
    self.EndModal( wx.ID_OK )

  def SetDatasetContent( self, ds ):
    if( ds.id ):
      #self.forms['id'].SetValue( ds.id )
      self.forms['dsname'].SetValue( ds.dsname )
      self.forms['dsdesc'].SetValue( ds.dsdesc )
      self.forms['dimension'].SetValue( str( ds.dimension ) )
      self.forms['groupname'].SetValue( ds.groupname )
      self.forms['baseline'].SetValue( ds.baseline )
      self.forms['polygons'].SetValue( ds.polygons )
      self.forms['wireframe'].SetValue( ds.wireframe )

  def SetDimension(self, dim ):
    if( dim ):
      self.forms['dimension'].SetValue( str( dim ) )

  def OnTest(self, event):
    return
  
    ds = MdDataset()
    ds.id = int( self.forms['id'].GetLabel())
    if( not ds.id ) :
      return
    ds.find()
    ds.load_objects()
    try:
      ds.procrustes_superimposition()
    except MdException, e:
      wx.MessageBox( str( e ) )
      return
    ds.reference_shape.dataset_id = ds.id
    og = ModanDatasetViewer(self)
    og.SetDataset( ds )
    og.SetObject( ds.reference_shape )
    og.ShowModal()
    og.Destroy()
