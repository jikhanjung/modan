import wx 
#import sys
from libpy.model_mddataset import MdDataset
from libpy.model_mdobject import MdObject
from libpy.droptarget import MdDropTarget   
from gui.tree_menu import MainTreeMenu
from gui.dialog_dataset import ModanDatasetDialog   
   
  
class MdDatasetTree(wx.TreeCtrl):
  def __init__(self, parent, id):
    window_style = wx.TR_HAS_BUTTONS|wx.TR_LINES_AT_ROOT#|wx.TR_HIDE_ROOT
    #window_style = wx.TR_HAS_BUTTONS
    super(MdDatasetTree, self).__init__(parent, id, style=window_style) 
    self.Refresh()
    self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSelChanged)
    self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated)
    self.Bind( wx.EVT_TREE_ITEM_MENU, self.OnContextMenu )
    #self.Bind( wx.EVT_TREE_ITEM_MENU, self.OnContextMenu )
    self.Bind( wx.EVT_TREE_BEGIN_DRAG, self.OnBeginDrag )

    target = MdDropTarget( self )
    self.SetDropTarget(target )    
    self.dataset_selected = False

  def OnBeginDrag( self, event ):
    #print "aa"
    treeitem = event.GetItem()

    ds = self.GetItemPyData( treeitem )
    #dataobj = MdDataObject()
    #dataobj.SetData( str( mo.id ) )

    textobj = wx.TextDataObject( "Dataset:"+str( ds.id ) )
    dropSource = wx.DropSource( self )
    dropSource.SetData( textobj )
    result = dropSource.DoDragDrop( wx.Drag_AllowMove )

    #if( result == wx.DragMove ):
      #print "delete [" + str( mo.id  ) + "]"
      #print "drag ok"
      #self.Delete( treeitem )
    self.Refresh()  

  def RefreshObjectList(self ):
    selected = self.GetSelection()
    app = wx.GetApp()
    #print "selected:", selected
    #if ds == None:
    #  app.objectList.ClearList()
    if selected:
      sel_item = self.GetItemText(selected)
      #print "sel_item:", sel_item
      ds = self.GetItemPyData(selected)
      #print ds
      if ds == None:
        app.objectList.ClearList()
    else:
      #print "refreshobjectlist no sel_item"
      if app.objectList :
        #print "objectlist exist"
        app.objectList.ClearList()
      return

    ds = MdDataset()
    ds = ds.find_by_name(sel_item)
    for d in ds:
      d.load_objects()
      for o in d.objects:
        o.load_landmarks()
      app.objectList.SetObjectList( d.objects )

  def Refresh(self, dsid = -1):
    if (self.GetSelection()):
      selected = self.GetSelection()
      sel_item = self.GetItemText(selected)
      #print "selected:", sel_item
      
      if (not self.ItemHasChildren(selected)):
        parentid = self.GetItemParent(selected)
        #print "selected: ", selected
        #print "parentid: ", parentid
        #print "root: ", self.root
        sel_parent = self.GetItemText(self.GetItemParent(selected))
        #print "parent text:", sel_parent
      else:
        sel_parent = ''
      #print ""
    else:
      sel_item = 'All'
      sel_parent = ''
    #sel_parent
    self.DeleteAllItems()
    self.root = self.AddRoot('Data')
    self.categories = dict()
    self.categories['2D'] = self.AppendItem(self.root, '2D')
    self.categories['3D'] = self.AppendItem(self.root, '3D')
    
    selected = False  
    ds = MdDataset()
    selected_dataset = MdDataset()
    for d in ds.find_all():
      dsdim = str( d.dimension ) + 'D'
      id = self.AppendItem(self.categories[dsdim], d.dsname, data = wx.TreeItemData( d ) )
      if( d.dsname == sel_item ):
        self.SelectItem( id )
        selected = True
        selected_dataset = d
    
    self.Expand( self.root )
    self.Expand( self.categories['2D'] )
    self.Expand( self.categories['3D'] )
    if( selected == True and selected_dataset != None ):
      self.RefreshObjectList()
    else:
      self.RefreshObjectList()
      
  def ResetTree(self):
    self.DeleteAllItems()
    self.RefreshObjectList()
    
  def OnTreeSelChanged(self, event):
    selected_item = event.GetItem()
    #selected_text = self.GetItemPyData(selected_item)
    #print selected_item
    wx.BeginBusyCursor()
    ds = self.GetItemPyData(selected_item)
    #print selected_item
    app = wx.GetApp()
    #print "1"
    if( ds == None ):
      #print "none"
      self.dataset = None
      self.dataset_selected = False
      self.RefreshObjectList()
      wx.EndBusyCursor()
      return
    #print "2"
    #print ds
    #ds = MdDataset( ds )
    ds.load_objects()
#    if( len( ds.objects ) == 0 ):
#      ds.set_objects()
    mos = ds.objects
    for mo in mos:
      mo.load_landmarks()
    #print mos
    
#    mo = MdObject()
#    mos = []
#    mos = mo.find_by_dataset_name( selected_text )
    self.dataset = ds
    self.dataset_selected = True
    app.objectList.SetDataset( ds )
    app.objectList.SetObjectList(mos)
    wx.EndBusyCursor()

  def ChangeToAnItem(self, category_name, tag_name):
    return
    
  def OnActivated( self, evt ):
    itemid = evt.GetItem()
    #print itemid
    ds = self.GetItemPyData( itemid )
    if( ds == None ):
      return
    ds_dialog = ModanDatasetDialog( self, -1 )
    ds_dialog.SetMdDataset( ds )
    ret = ds_dialog.ShowModal()
    if ret == wx.ID_EDIT:
      self.Refresh()

  def OnContextMenu( self, evt ):
    itemid = evt.GetItem()
    ds = self.GetItemPyData( itemid )
    if( itemid == self.categories['2D'] ):
      self.PopupMenu( MainTreeMenu( self, mode='root', dim = 2 ), evt.GetPoint())    
    elif( itemid == self.categories['3D'] ):
      self.PopupMenu( MainTreeMenu( self, mode='root', dim = 3 ), evt.GetPoint())    
    else:
      self.PopupMenu( MainTreeMenu( self, mode='dataset', ds=ds ), evt.GetPoint())    

  def DropObject( self, x, y, data, action ):
    ( itemid, flag ) = self.HitTest( ( x, y ) )
    flag
    app = wx.GetApp()
    #print app.cmd_down, app.alt_down
    ( datatype, id ) = data.split(":")
    if( datatype == 'Dataset' ):
      #if( itemid == self.categories['2D'] or
      #    itemid == self.categories['3D']    ):
      #ds = self.GetItemPyData( itemid )
      #print "dataset dropped"
      self.Refresh()
      return wx.DragNone

#      ds = MdDataset()
#      ds.id = int( id )
#      ds.find()
#      id = self.AppendItem( itemid, ds.dsname, data = ds )
#      
      #return wx.DragMove
    elif( datatype == 'Object' ):
    #print "object dropped!"
    #print "x=" + str(x) +",y="+str(y)
    #print "itemid : " + str( itemid )
      wx.BeginBusyCursor()
      id_list = id.split( "," )
      ds = self.GetItemPyData( itemid )
      for id in id_list:
        mo = MdObject()
        mo.id = int( id )
        mo.find()
        #print "dsname: " + ds.dsname
        #print "data:",
        #print data
        #print data.GetDataHere()
        #print "object dropped"
        mo.dataset_id = ds.id
        if action == wx.DragMove:
          mo.update()
        elif action == wx.DragCopy:
          mo.id = 0
          mo.insert()
      #self.RefreshObjectList()
      wx.EndBusyCursor()
      return action
    return wx.DragNone