#!/usr/bin/env python
# -*- coding: utf-8 -*-
import wx

from libpy.modan_dbclass import MdDataset, MdObject
from libpy.droptarget import MdDropTarget
from gui.tree_menu import MainTreeMenu
from gui.dialog_dataset import ModanDatasetDialog


class MdDatasetTree(wx.TreeCtrl):
    def __init__(self, parent, wid, frame):
        window_style = wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT  # |wx.TR_HIDE_ROOT
        # window_style = wx.TR_HAS_BUTTONS
        super(MdDatasetTree, self).__init__(parent, wid, style=window_style)

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_sel_changed)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_activated)
        self.Bind(wx.EVT_TREE_ITEM_MENU, self.on_context_menu)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.on_begin_drag)

        target = MdDropTarget(self)
        self.SetDropTarget(target)
        self.dataset_selected = False
        self.dataset_list = []
        self.dataset = None
        self.frame = frame
        self.app = wx.GetApp()
        self.refresh_dataset()

    def on_begin_drag(self, event):
        treeitem = event.GetItem()

        ds = self.GetItemPyData(treeitem)

        textobj = wx.TextDataObject("Dataset:" + str(ds.id))
        dropSource = wx.DropSource(self)
        dropSource.SetData(textobj)
        result = dropSource.DoDragDrop(wx.Drag_AllowMove)

        self.refresh_dataset()

    def refresh_object_list(self):
        selected = self.GetSelection()

        self.frame.object_list_pane.ClearList()

        if selected:
            ds = self.GetItemPyData(selected)
            if ds is not None:
                session = self.app.get_session()
                print "session in refresh_object_list:", session
                if ds not in session:
                    session.add(ds)
                object_list = ds.object_list
                #session.close()
                self.frame.object_list_pane.SetDataset( ds )

    def refresh_dataset(self):
        selected_dataset = None
        if self.GetSelection():
            selected = self.GetSelection()
            sel_item = self.GetItemText(selected)

            if (not self.ItemHasChildren(selected)):
                parentid = self.GetItemParent(selected)
                sel_parent = self.GetItemText(self.GetItemParent(selected))
            else:
                sel_parent = ''
        else:
            sel_item = 'All'
            sel_parent = ''
        self.DeleteAllItems()
        self.root = self.AddRoot('Data')
        self.categories = dict()
        self.categories['2D'] = self.AppendItem(self.root, '2D')
        self.categories['3D'] = self.AppendItem(self.root, '3D')

        selected = False
        session = self.app.get_session()
        print "session in refresh_dataset:", session
        self.dataset_list = [ds for ds in session.query(MdDataset)]
        #session.close()
        for d in self.dataset_list:
            dsdim = str(d.dimension) + 'D'
            id = self.AppendItem(self.categories[dsdim], d.dsname, data=wx.TreeItemData(d))
            if ( d.dsname == sel_item ):
                self.SelectItem(id)
                selected = True
                selected_dataset = d

        self.Expand(self.root)
        self.Expand(self.categories['2D'])
        self.Expand(self.categories['3D'])
        if (selected) and (selected_dataset is not None):
            self.refresh_object_list()
        else:
            self.refresh_object_list()

    def reset_tree(self):
        self.DeleteAllItems()
        self.refresh_object_list()

    def on_tree_sel_changed(self, event):
        # selected_text = self.GetItemPyData(selected_item)
        #print selected_item
        wx.BeginBusyCursor()
        session = self.app.get_session()
        print "session in on_tree_sel_changed:", session
        selected_item = event.GetItem()
        ds = self.GetItemPyData(selected_item)
        #print selected_item
        app = wx.GetApp()
        #print "1"
        if ( ds == None ):
            #print "none"
            self.dataset = None
            self.dataset_selected = False
            self.refresh_object_list()
            #wx.EndBusyCursor()
        else:    #return
            #print "id map:", session.identity_map
            #if ds in session:
            #    print "ds is in session", ds, session
            #else:
            #    print "ds not in session", ds, session
            if ds not in session:
                session.add(ds)
            #print "id map:", session.identity_map
            self.dataset = ds
            self.dataset_selected = True
            self.frame.object_list_pane.SetDataset(ds)
        wx.EndBusyCursor()

    def change_to_an_item(self, category_name, tag_name):
        return

    def on_activated(self, evt):
        itemid = evt.GetItem()
        # print itemid
        ds = self.GetItemPyData(itemid)
        self.frame.open_dataset_dialog(ds)
        return

    def on_context_menu(self, evt):
        itemid = evt.GetItem()
        ds = self.GetItemPyData(itemid)
        self.SelectItem(itemid)
        if ( itemid == self.categories['2D'] ):
            treemenu = MainTreeMenu(self, mode='root', dim=2)
        elif ( itemid == self.categories['3D'] ):
            treemenu = MainTreeMenu(self, mode='root', dim=3)
        else:
            treemenu = MainTreeMenu(self.frame.dataset_tree_pane, mode='dataset', dataset=ds)

        self.PopupMenu(treemenu, evt.GetPoint())

    def drop_object(self, x, y, data, action):
        # TODO take care of property list differences between datasets
        ( itemid, flag ) = self.HitTest(( x, y ))
        # flag
        app = wx.GetApp()
        # print app.cmd_down, app.alt_down
        ( datatype, id ) = data.split(":")
        if ( datatype == 'Dataset' ):
            # if( itemid == self.categories['2D'] or
            #    itemid == self.categories['3D']    ):
            #ds = self.GetItemPyData( itemid )
            #print "dataset dropped"
            self.refresh_dataset()
            return wx.DragNone

        # ds = MdDataset()
        #      ds.id = int( id )
        #      ds.find()
        #      id = self.AppendItem( itemid, ds.dsname, data = ds )
        #
        #return wx.DragMove
        elif ( datatype == 'Object' ):
            #print "object dropped!"
            #print "x=" + str(x) +",y="+str(y)
            #print "itemid : " + str( itemid )
            wx.BeginBusyCursor()
            id_list = id.split(",")
            ds = self.GetItemPyData(itemid)
            for id in id_list:
                mo = MdObject()
                mo.id = int(id)
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