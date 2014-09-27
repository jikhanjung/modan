import wx
#import sys
#import libpy.conf import ModanConf
#from libpy.conf import ModanConf as ModanConf
  
#from libpy.conf import ModanConf
from libpy.model_mddataset import MdDataset
from libpy.model_mdwireframe import MdWireframe
from libpy.model_mdobject import MdObject

ID_ADD_BUTTON = 2000
ID_DELETE_BUTTON = 2001
ID_CLEAR_ALL_BUTTON = 2002
ID_SAVE_BUTTON = 2003
ID_CLOSE_BUTTON = 2004
ID_EDGELIST_CTRL = 2005
ID_vertex_from = 2006
ID_vertex_to = 2007

DIALOG_SIZE = wx.Size( 600, 400 )

class ModanWireframeDialog( wx.Dialog ):
  def __init__( self, parent, id ):
    wx.Dialog.__init__( self, parent, id, 'Edit Wireframe', size=DIALOG_SIZE)
    panel = wx.Panel(self, -1)
    self.forms = dict()
    self.wfname = None
    self.wireframe_id = None
    self.wireframe = []
    
    mainSizer = wx.BoxSizer(wx.VERTICAL)

    # wireframe name
    wfnameLabel = wx.StaticText(panel, -1, 'Wireframe Name', style=wx.ALIGN_RIGHT)
    self.forms['wfname'] = wx.TextCtrl(panel, -1, '')
    # dataset description
    wfdescLabel = wx.StaticText(panel, -1, 'Description', style=wx.ALIGN_RIGHT)
    self.forms['wfdesc'] = wx.TextCtrl(panel, -1, '')

    edgelistLabel = wx.StaticText(panel, -1, 'Edges', style=wx.ALIGN_CENTER)
    self.forms['edgelist'] = wx.TextCtrl(panel, -1, '', style=wx.TE_MULTILINE)
    self.forms['edgelist'].SetMinSize((200,200))

    inputSizer = wx.FlexGridSizer( cols=2, hgap=10)
    inputSizer.AddGrowableCol(1)
    inputSizer.Add( wfnameLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['wfname'], 0, wx.EXPAND )
    inputSizer.Add( wfdescLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['wfdesc'], 0, wx.EXPAND )
    inputSizer.Add( edgelistLabel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL )
    inputSizer.Add( self.forms['edgelist'], 0, wx.EXPAND )
    mainSizer.Add( inputSizer, 0, wx.EXPAND|wx.ALL, 10)
    
    #deleteButton = wx.Button(panel, ID_DELETE_BUTTON, 'Delete')
    clearallButton = wx.Button(panel, ID_CLEAR_ALL_BUTTON, 'ClearAll')
    saveButton = wx.Button(panel, ID_SAVE_BUTTON, 'Save')
    closeButton = wx.Button(panel, ID_CLOSE_BUTTON, 'Close')
    #self.Bind(wx.EVT_BUTTON, self.OnAdd, id=ID_ADD_BUTTON)
    #self.Bind(wx.EVT_BUTTON, self.OnDelete, id=ID_DELETE_BUTTON)
    self.Bind(wx.EVT_BUTTON, self.OnClearAll, id=ID_CLEAR_ALL_BUTTON)
    self.Bind(wx.EVT_BUTTON, self.OnSave, id=ID_SAVE_BUTTON)
    self.Bind(wx.EVT_BUTTON, self.OnClose, id=ID_CLOSE_BUTTON)
    buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
    # buttonSizer.Add(deleteButton, wx.EXPAND)
    buttonSizer.Add(clearallButton, wx.EXPAND)
    buttonSizer.Add(saveButton, wx.EXPAND)
    buttonSizer.Add(closeButton, wx.EXPAND)
    buttonSizer.Add((10,10), wx.EXPAND)
    mainSizer.Add(buttonSizer, 0, wx.EXPAND|wx.ALL, 10)

    panel.SetSizer(mainSizer)
    panel.Fit()
    self.forms['edgelist'].SetFocus()

  def OnClearAll(self, event):
    self.forms['edgelist'].SetValue('')
    return
  
  def OnSave(self, event):
    edges = self.process_wireframe( self.forms['edgelist'].GetValue() )
    wf = MdWireframe()
    wf.edges = edges
    wf.wfname = self.forms['wfname'].GetValue()
    wf.wfdesc = self.forms['wfdesc'].GetValue()
    if self.wireframe_id:
      wf.id = self.wireframe_id
      wf.update()
      self.wfname = wf.wfname
      self.wireframe_id = wf.id
    else:
      wf.insert()
      self.wfname = wf.wfname
      self.wireframe_id = wf.id
    self.EndModal( wx.ID_EDIT )
  
  def OnClose(self, event):
    self.Close()

  def process_wireframe( self, edge_text ):
    #print edge_text
    new_edges = []
    edges = edge_text.split( "\n" )
    for edge in edges:
      edge = edge.strip()
      points = edge.split( " " )
      if len( points ) > 2 :
        points = points[-2:-1]
      elif len( points ) < 2:
        continue
      new_edges.append( "-".join( points ) )
    return ",".join( new_edges )
    
  def SetWireframe(self, wireframe ):
    self.wireframe = wireframe
    self.wireframe_id = wireframe.id
    self.forms['wfname'].SetValue( wireframe.wfname )
    self.forms['wfdesc'].SetValue( wireframe.wfdesc )
    self.forms['edgelist'].SetValue( wireframe.edges.replace( "-", " " ).replace( ",","\n")  )
    #print wireframe.edges
  
  def SetDimension(self, dim ):
    if( dim ):
      self.forms['dimension'].SetValue( str( dim ) )


