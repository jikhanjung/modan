import wx

from gui.niftylist import NiftyVirtualList  # , NiftyListItem
from gui.dialog_object import ModanObjectDialog
from gui.dialog_export import ModanExportDialog
from libpy.modan_dbclass import *
from gui.list_menu import MainListMenu


WIDTH_ID = 100
WIDTH_NAME = 200
WIDTH_DESC = 200

# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/426407

class MdObjectList(NiftyVirtualList):
    def __init__(self, parent, wid, frame):
        window_style = wx.LC_REPORT
        super(MdObjectList, self).__init__(parent, wid, style=window_style | wx.LC_VIRTUAL)
        self.frame = frame
        self.app = wx.GetApp()
        self.dataset = None
        self.object_list = []
        self.alt_down = False
        self.cmd_down = False

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListObjectSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnMdObjectActivated)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnItemRightClick)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnBeginDrag)

        self.colsort = [0, 0, 0]  # 0=ascending ready, 1=descending ready
        self.colsortfunc = [
            lambda x, y: cmp(x.id, y.id),
            lambda x, y: cmp(x.objname, y.objname),
            lambda x, y: cmp(x.objdesc, y.objdesc),
            lambda x, y: cmp(y.id, x.id),
            lambda x, y: cmp(y.objname, x.objname),
            lambda x, y: cmp(y.objdesc, x.objdesc)
        ]

    def OnBeginDrag(self, event):

        itemid = self.GetFirstSelected()
        #print "first selected item: ", itemid
        if ( itemid < 0 ):
            return
        object_list = []
        itemid_list = []
        while ( itemid >= 0 ):
            mo = self.GetPyData(itemid)
            object_list.append(mo)
            #print itemid
            #print itemid_list
            itemid_list.append(itemid)
            itemid = self.GetNextSelected(itemid)
        self.selected_object_list = object_list

        textobj = wx.TextDataObject(
            "Object:" + ",".join([str(mo.id) for mo in self.selected_object_list]))  #str( mo.id ) )
        dropSource = wx.DropSource(self)
        dropSource.SetData(textobj)
        result = dropSource.DoDragDrop(wx.Drag_AllowMove)
        #print itemid, itemid_list
        itemid_list.reverse()
        #print itemid_list
        if result == wx.DragMove:
            #print "move"
            for itemid in itemid_list:
                self.Select(itemid, 0)
                self.DeleteItem(itemid)
            #self.Select()
            pass
        elif result == wx.DragCopy:
            #print "copy"
            pass
        return
        # print "delete [" + str( mo.id  ) + "]"
        #self.DeleteItem( itemidx )

    def RefreshList(self, object_id=-1):

        self.DeleteAllItems()
        self.DeleteAllColumns()
        self.SetSort(lambda x, y: cmp(x.id, y.id))  # default sorting

        propertyname_list = self.dataset.propertyname_list
        number_of_group = len(propertyname_list)

        self.colsortfunc = []
        self.colsort = []
        self.colsortfunc.append([])
        self.colsortfunc.append([])
        columnheader = ['Name', 'LM', 'Csize']
        columnwidth = [100, 40, 60]
        # TODO enhance objname sort: in such case as "specimen 1", 1 should be treated as number, not string.
        self.colsortfunc[0] = [lambda x, y: cmp(x.objname, y.objname),
                               lambda x, y: cmp(len(x.landmark_list), len(y.landmark_list)),
                               lambda x, y: cmp(x.get_centroid_size(), y.get_centroid_size())
        ]
        self.colsortfunc[1] = [lambda y, x: cmp(x.objname, y.objname),
                               lambda y, x: cmp(len(x.landmark_list), len(y.landmark_list)),
                               lambda y, x: cmp(x.get_centroid_size(), y.get_centroid_size())
        ]
        #if self.dataset.dimension == 2:
        #columnheader.append( 'Img' )
        #columnwidth.append( 40 )
        #self.colsortfunc[0].append( lambda x, y: cmp( x.objname, y.objname ) )
        #self.colsortfunc[1].append( lambda y, x: cmp( x.objname, y.objname ) )
        for i in range(len(columnheader)):
            self.colsort.append(0)
        #print groupname_list
        f = []
        f.append([])
        f.append([])
        for k in range(len(propertyname_list)):
            f[0].append(lambda x, y: cmp(x.property_list[k].property, y.property_list[k].property))
        for k in range(len(propertyname_list)):
            f[1].append(lambda y, x: cmp(x.property_list[k].property, y.property_list[k].property))
        i = 0
        for p in propertyname_list:
            columnheader.append(p.propertyname)
            columnwidth.append(100)
            self.colsort.append(0)
            #print i, len( self.colsortfunc[0] )
            self.colsortfunc[0].append(f[0][i])
            self.colsortfunc[1].append(f[1][i])
            #self.colsortfunc[1].append( lambda y, x: cmp( x.group_list[i], y.group_list[i] ) )
            i += 1
        #print columnheader
        #print self.colsort, self.colsortfunc

        for i in range(len(columnheader)):
            self.InsertColumn(i, columnheader[i], width=columnwidth[i])

        for mdobject in self.object_list:
            mdobject.get_centroid_size(True)
            mdobject.unpack_landmark()
            item = self.InsertItem(data=mdobject)
            #print "item:" + str( item )
            #item.SetText(str(mdobject.id), 0)
            i = 0
            item.SetText(mdobject.objname, i)
            i += 1
            item.SetText(str(len(mdobject.landmark_list)), i)
            i += 1
            #print "%.3f" % 1.382123
            #print str( "%.3f", 1.382123 )
            item.SetText("%.3f" % mdobject.get_centroid_size(), i)
            i += 1

            #if mdobject.has_image: has_image = 'Y'
            #else: has_image = 'N'
            #item.SetText( has_image, i )
            #i+= 1

            #print mdobject.group_list

            for p in mdobject.property_list:
                pn_id = p.propertyname_id
                for j in range(len(mdobject.dataset.propertyname_list)):
                    if pn_id == mdobject.dataset.propertyname_list[j].id:
                        print i, j
                        item.SetText(p.property, i + j)

            #for j in range(len(mdobject.property_list)):
                #item.SetText(mdobject.property_list[j].property, i + j)
                #i += 1
                #print "item id: ",
                #print item.GetData()
                #print mdobject
        ''' a
        self.colsort = [0, 0, 0] # 0=ascending ready, 1=descending ready
        self.colsortfunc = [
                            lambda x, y: cmp(x.id, y.id),
                            lambda x, y: cmp(x.objname, y.objname),
                            lambda x, y: cmp(x.objdesc, y.objdesc),
                            lambda x, y: cmp(y.id, x.id),
                            lambda x, y: cmp(y.objname, x.objname),
                            lambda x, y: cmp(y.objdesc, x.objdesc)
                           ]
        '''
        #self.colsort = [0, 0, 0] # 0=ascending ready, 1=descending ready
        self.frame.object_content_pane.SetBlank()

    def RefreshAll(self):
        self.DeleteAllItems()
        self.SetSort(lambda x, y: cmp(x.id, y.id))  # default sorting

    def AppendObject(self, mo):
        self.object_list.append(mo)
        item = self.InsertItem(data=mo)
        self.RefreshList(mo.id)

    def SetDataset(self, dataset):
        self.dataset = dataset
        self.object_list = dataset.object_list
        self.RefreshList()
        #self.RefreshList()

    def remove_by_mdobject_id(self, id):
        self.SetFilter(lambda x: x.id == id)
        self.DeleteItem(0)
        self.SetFilter(lambda x: True)

    def OnColClick(self, event):
        col = event.m_col
        colsort = self.colsort[col]
        #print colsort, col
        self.SetSort(self.colsortfunc[colsort][col])
        self.colsort[col] = 1 - self.colsort[col]

    def OnResize(self):
        pass

    #    if( self.GetSize().x > 0 ):
    #      WIDTH_DESC = self.GetSize().x - WIDTH_ID - WIDTH_NAME
    #      self.SetColumnWidth(2, width=WIDTH_DESC)

    def OnListObjectSelected(self, event):
        idx = event.GetIndex()
        #print idx
        item = self._items[idx]
        #print item
        pydata = item.GetPyData()
        #print pydata
        #return
        self.frame.object_content_pane.SetObjectContent(pydata)
        event.Skip()

    def EditObject(self, mdobject):
        self.frame.open_object_dialog( mdobject )

    def OnMdObjectActivated(self, event):
        idx = event.GetIndex()
        #print idx
        item = self._items[idx]
        #print item
        mo = item.GetPyData()
        #print mo
        self.EditObject(mo)
        #print mo
        #mo = self._items[event.GetItem().GetId()].GetPyData()
        #mo = MdObject()
        #mo.id = event.GetItem().GetText()
        #mo.find()
        #print "object_id:", mo.id, "dataset_id:", mo.dataset_id
        #print
        #mo.load_landmarks()

    def ClearList(self):
        self.DeleteAllItems()
        self.frame.object_content_pane.SetBlank()
        self.Refresh()

    def OnGroup(self, event):
        #print self.selected_object_list
        id = event.GetId()
        #print "group", event
        item = self.group_menu.FindItemById(id)
        label = item.GetLabel()
        propertyDlg = propertyInputDlg(self, -1, label)
        res = propertyDlg.ShowModal()
        if res == wx.ID_OK:
            property_value = propertyDlg.GetValue()
        else:
            return
            #print groupval
            #print self.pixels_per_millimeter, "pixels in 1 mm"
        propertyDlg.Destroy()
        name_list = ", ".join([o.objname for o in self.selected_object_list])
        #print name_list + " all belong to " + groupval + " " + label

        found = False
        propertyname_id = -1
        for i in range(len(self.dataset.propertyname_list)):
            if self.dataset.propertyname_list[i].propertyname == label:
                found = True
                propertyname_id = self.dataset.propertyname_list[i].id

        if found:
            wx.BeginBusyCursor()
            session = self.app.get_session()
            for mdobject in self.selected_object_list:
                print mdobject, mdobject.id
                session.add(mdobject)
                print mdobject, mdobject.id
                print "prop_list 1", [ [ p.id, p.propertyname_id, p.object_id ] for p in mdobject.property_list ]
                for p in mdobject.property_list:
                    if p.propertyname_id == propertyname_id:
                        session.delete(p)
                        #mdobject.property_list.remove(p)
                #print object
                #print object.id
                mdproperty = MdProperty(property_value)
                mdproperty.object_id = mdobject.id
                mdproperty.propertyname_id = propertyname_id
                mdobject.property_list.append( mdproperty )
                print mdproperty, mdproperty.object_id, mdproperty.propertyname_id, mdproperty.property
                print "prop_list 2", [ [ p.id, p.object_id ] for p in mdobject.property_list ]
            session.commit()
            self.RefreshList()
            wx.EndBusyCursor()


    def OnEdit(self, event):
        self.EditObject(self.selected_object_list[0])
        return

    def OnExport(self, event):
        export_dialog = ModanExportDialog(self, -1)
        export_list = self.selected_object_list
        object_list = []
        for itemid in range(len(self.object_list)):
            if not self.IsSelected(itemid):
                mo = self.GetPyData(itemid)
                object_list.append(mo)

        if len(export_list) <= 0:
            return
        ds = MdDataset()
        ds.id = export_list[0].dataset_id
        ds.find()

        export_dialog.SetDataset(ds)
        export_dialog.SetObjectList(object_list)
        export_dialog.SetExportList(export_list)
        #print ds[0].objects
        export_dialog.ShowModal()
        export_dialog.Destroy()
        return

    def OnDelete(self, event):
        # confirm deletion
        msg_box = wx.MessageDialog(self,
                                   "Do you really want to delete " + str(len(self.selected_object_list)) + " objects?",
                                   "Warning", wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE | wx.ICON_EXCLAMATION)
        result = msg_box.ShowModal()
        session = self.app.get_session()
        if ( result == wx.ID_YES ):

            wx.BeginBusyCursor()
            for mdobject in self.selected_object_list:
                session.add(mdobject)
                for p in mdobject.property_list:
                    session.delete( p )
                session.delete(mdobject)
                #print object
                #print object.id
                #self.remove_by_mdobject_id(object.id)
            session.commit()
            self.RefreshList()
            wx.EndBusyCursor()
        return

    def OnItemRightClick(self, evt):
        #print evt
        itemid = self.GetFirstSelected()
        #print "first selected item: ", itemid
        if ( itemid < 0 ):
            return
        object_list = []
        while ( itemid >= 0 ):
            mo = self.GetPyData(itemid)
            object_list.append(mo)
            itemid = self.GetNextSelected(itemid)
        self.selected_object_list = object_list
        event_point = evt.GetPoint()

        m = wx.Menu()
        if len(object_list) == 1:
            i = m.Append(wx.NewId(), '&Edit')
            self.Bind(wx.EVT_MENU, self.OnEdit, i)
        else:
            i = m.Append(wx.NewId(), 'E&xport')
            self.Bind(wx.EVT_MENU, self.OnExport, i)
        i = m.Append(wx.NewId(), '&Delete')
        self.Bind(wx.EVT_MENU, self.OnDelete, i)
        #i = m.Append( wx.NewId(), '&Add Tag' )
        #self.Bind( wx.EVT_MENU, self.OnMenu, i )

        self.group_menu = m2 = wx.Menu()

        for prop in self.dataset.propertyname_list:
            i = m2.Append(wx.NewId(), prop.propertyname )
            self.Bind(wx.EVT_MENU, self.OnGroup, i)
        m.AppendMenu(wx.NewId(), 'Set property', m2)

        self.PopupMenu(m, event_point)
        return
        #m = MainListMenu( self, object_list )
        #m.AddGroupSubmenu( self.dataset.groupname_list )
        #self.PopupMenu( m, event_point )


class propertyInputDlg(wx.Dialog):
    def __init__(self, parent, id, group_name):
        wx.Dialog.__init__(self, parent, id, 'Set property', size=(320, 180))
        self.panel = panel = wx.Panel(self, -1)
        self.maintext = wx.StaticText(panel, -1, 'Set ' + group_name.lower() + " as:", style=wx.ALIGN_LEFT)
        self.groupinfo = wx.TextCtrl(panel, -1, '')

        self.okButton = wx.Button(panel, -1, 'OK')
        self.cancelButton = wx.Button(panel, -1, 'Cancel')
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.okButton)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancelButton)

        #x = self.GetSize().width / 2
        #y = self.GetSize().height/ 2
        rowHeight = 22
        controlWidth = ( 100, 150)
        controls = ( self.maintext, self.groupinfo )
        x = 60
        y = 50
        for i in range(len(controls)):
            controls[i].SetSize(( controlWidth[i], rowHeight ))
            controls[i].SetPosition(( x, y ))
            x += controlWidth[i]

        x = 110
        y = 100
        buttonWidth = ( 45, 45)
        buttons = ( self.okButton, self.cancelButton )
        for i in range(len(buttons)):
            buttons[i].SetSize(( buttonWidth[i], rowHeight ))
            buttons[i].SetPosition(( x, y ))
            x += buttonWidth[i]

        panel.Fit()
        #self.Show()
        self.groupinfo.SetFocus()
        #self.forms['objname'] = wx.TextCtrl(panel, -1, '')

    def OnOk(self, event):
        self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def GetValue(self):
        return self.groupinfo.GetValue()

