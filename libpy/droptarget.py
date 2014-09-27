import wx
  
class MdDropTarget(wx.TextDropTarget):
  def __init__(self, win):
    wx.TextDropTarget.__init__(self) 
    self.data = wx.TextDataObject()
    self.SetDataObject(self.data)
    self.win = win
  def OnDropText( self, x, y, text ):
    ''' not used anymore'''
    #print "ondroptext"
    rv = self.win.DropObject( x, y, text )
    return rv
  def OnData(self, x, y, default_val ):
    getdata = self.GetData()
    #print getdata
    data = self.data.GetText()
    #print data
    #print "ondata", default_val
    #print default_val
    rv = self.win.DropObject( x, y, data, default_val )
    #print rv
    #print wx.DragError, wx.DragNone, wx.DragCopy, wx.DragMove, wx.DragLink, wx.DragCancel
    return rv
    