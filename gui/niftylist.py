import wx

import bisect 
   
class NiftyListItem(object):
    def __init__(self, baseList, text ="", image = -1, data = None):
        numColumns = baseList.GetColumnCount()
        self.texts = [text] + (numColumns - 1) * [""]
        self.images = [image] + (numColumns - 1) * [-1]
        self.attr = None
        self.baseList = baseList
        self.data = data
        self.baseList._PositionItem(self)
    
    def Delete(self):
        idx = None
        try:
            idx = self.baseList._filteredView.index(self)
        except ValueError:
            self.baseList._items.remove(self)
        else:
            self.baseList.DeleteItem(idx)
    
    def __cmp__(self, other):
        if isinstance(other, NiftyListItem):
          other = other.GetPyData()
        #print self, other
        a = self.GetPyData()
        b = other
        #print a, b
        #print self.baseList
        #print other.group3
        return self.baseList._rowDataCmpFunc(self.GetPyData(), other)
    
    def GetPyData(self):
        return self.data
    
    def SetPyData(self, data):
        self.data = data
        self.baseList._RePositionItem(self)
    
    def GetText(self, col = 0):
        return self.texts[col]
    
    def SetText(self, text, col = 0):
        self.texts[col] = text
    
    def GetImage(self, col = 0):
        return self.images[col]
    
    def SetImage(self, img, col = 0):
        self.images[col] = img
    
    def SetAttr(self, attr):
        self.attr = attr
        
    def GetAttr(self):
        return self.attr

class NiftyVirtualList(wx.ListCtrl):    
    
    def __init__(self, *args, **kwds):
        wx.ListCtrl.__init__(self, *args, **kwds)
        self._items = []
        self._filteredView = []
        self._filter = lambda x: True
        self._rowDataCmpFunc = lambda x, y: cmp(x, y)
    
    def InsertItem(self, data, text = "", image = -1):
        return NiftyListItem(self, text, image, data)
    
    def DeleteAllItems(self):
        self._items = []
        self._filteredView = []
        self.SetItemCount(0)
        
    def DeleteItem(self, item):
        if isinstance(item, NiftyListItem):
            item.Delete()
        else:
            obj = self._filteredView[item]
            del self._filteredView[item]
            self._items.remove(obj)
            self.SetItemCount(len(self._filteredView))
            self.Refresh()
    
    def _PositionItem(self, item):
        if not self.ItemFiltered(item):
            idx = bisect.bisect(self._filteredView, item)
            self._filteredView.insert(idx, item)
            self.Refresh()
        
        idx = bisect.bisect(self._items, item)
        self._items.insert(idx, item)
        self.SetItemCount(len(self._filteredView))

    def ItemFiltered(self, item):
        return not self._filter(item)
    
    def SetFilter(self, filter):
        self._filter = lambda x: filter(x.GetPyData())
        self._filteredView = [item for item in self._items
                               if not self.ItemFiltered(item)]
        self.SetItemCount(len(self._filteredView))
        self.Refresh()
    
    def SetSort(self, cmp):
        selected = self.GetFirstSelected()
        
        if (selected > -1):
          sel_item = self._items[selected]
          
        self._rowDataCmpFunc = cmp
        self._items.sort()
        self._filteredView.sort()
        self.Refresh()
        
        if (selected > -1):
          self.Select(selected, 0) # deselect
          new_sel = self._items.index(sel_item)
          self.Select(new_sel) # select again
          self.Focus(new_sel) # focus again
          

    def _RePositionItem(self, item):
        self._items.remove(item)
        self._filteredView.remove(item)
        self._PositionItem(item)
    
    def OnGetItemText(self, item, col):
        if isinstance(item, NiftyListItem):
            return item.GetText(col)
        return self._filteredView[item].GetText(col)

    def OnGetItemColumnImage(self, item, col):
        if isinstance(item, NiftyListItem):
            return item.GetImage(col)
        return self._filteredView[item].GetImage(col)
    
    def OnGetItemImage(self, item):
        if isinstance(item, NiftyListItem):
            return item.GetImage(0)
        return self._filteredView[item].GetImage(0)    

    def GetPyData(self, item):
        if isinstance(item, NiftyListItem):
            return item.GetPyData()        
        return self._filteredView[item].GetPyData()

    def SetPyData(self, item, value):
        if isinstance(item, NiftyListItem):
            return item.SetPyData(value)        
        self._filteredView[item].SetPyData(value)

    def OnGetItemAttr(self, item):
        if isinstance(item, NiftyListItem):
            return item.GetAttr()
        return self._filteredView[item].GetAttr()

def NiftifyList(list):
    list.__class__ = NiftyVirtualList
    NiftyVirtualList.__init__(list) 