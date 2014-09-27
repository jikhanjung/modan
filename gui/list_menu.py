import wx
from gui.dialog_object import ModanObjectDialog 

class GroupMenu( wx.Menu ):
  def __init__(self,parent,group_list):
    wx.Menu.__init__(self)
    self.parent = parent
    for item in group_list:
      i = wx.MenuItem( self, -1, 'Set ' + item )
      item = self.AppendItem( i )
      print i, item
      #print i.GetId()
      self.Bind( wx.EVT_MENU, self.OnGroup, i )

  def OnGroup(self,evt):
    print evt
    

class MainListMenu(wx.Menu): 
  def __init__(self, parent, ol = None ): 
    wx.Menu.__init__(self) 
    self.parent = parent 
    self.object_list = ol
    editObject = wx.MenuItem( self, -1, '&Edit' )
    addTag = wx.MenuItem( self, -1, 'Add &Tag' )
    #self.AppendItem( addNew ) 
    self.AppendItem( editObject ) 
    self.AppendItem( addTag ) 
      #self.Bind(wx.EVT_MENU, self.OnAddDataset, id=addNew.GetId()) 
    self.Bind(wx.EVT_MENU, self.OnEditObject, id=editObject.GetId()) 
    self.Bind(wx.EVT_MENU, self.OnAddTag, id=addTag.GetId()) 
    #print self.object_list

  def OnGroup(self,evt):
    print evt
    
  def AddGroupSubmenu(self,group_list):
    m = wx.Menu()
    for s in group_list:
      m.AppendMenu( wx.NewId(), )
      
    m = GroupMenu( self, group_list)
    self.AppendMenu( -1, 'Set group', m )

  def OnAddTag(self, event): 
    print event
    return
    #ds_dialog = ModanDatasetDialog( self.parent, -1 )
    #ds_dialog.SetDimension( str( self.dim ) )
    #ds_dialog.ShowModal()
    #self.parent.Refresh()
    #print "add dataset"
    #self.Close()

  def OnEditObject(self, event):
    print event
    mo_dialog = ModanObjectDialog( self.parent, -1 )
    mo_dialog.SetModanObject( self.object_list[0] )
    mo_dialog.ShowModal()
    #if( self.ds ):
    #  ds_dialog.SetMdDataset( self.ds )
    #ds_dialog.ShowModal()
    #self.parent.Refresh()
    #print "edit dataset"
    #self.Close()

  def OnDelObject(self, event): 
    print event
    ds_dialog = ModanObjectDialog( self.parent, -1 )
    ds_dialog.ShowModal()
    #self.parent.Refresh()
    #print "del dataset"
    #self.Close()

