#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import os
import sys
import json
import pygtk
import gtk
import threading
import subprocess
import ConServer

class CommListView(gtk.TreeView):
    (
        COLUMN_NUM,
        COLUMN_UID,
        COLUMN_COMM,
    ) = range(3)

    def __init__(self, *args, **kwargs):
        gtk.TreeView.__init__(self, *args, **kwargs)
        self.udic = None
        self.nmdic = {}
        self.renderer_num = gtk.CellRendererText()
        self.renderer_uid = gtk.CellRendererText()
        self.renderer_comm = gtk.CellRendererText()

        self.col_num = gtk.TreeViewColumn('No.',
                                      self.renderer_num,
                                      text=self.COLUMN_NUM)
        self.col_uid = gtk.TreeViewColumn('UserID',
                                      self.renderer_uid,
                                      text=self.COLUMN_UID)
        self.col_comm = gtk.TreeViewColumn('Comment',
                                      self.renderer_comm,
                                      text=self.COLUMN_COMM)

        self.append_column(self.col_num)
        self.append_column(self.col_uid)
        self.append_column(self.col_comm)

        self.item_open     = gtk.MenuItem('_Open this URL')
        self.item_profile  = gtk.MenuItem('_Open Profile ')
        self.item_copy     = gtk.MenuItem('_Copy this')
        self.item_setname  = gtk.MenuItem('_Set Name')
        self.item_takename = gtk.MenuItem('_Take Name')
        self.menu_popup = gtk.Menu()
        self.menu_popup.add(self.item_open)
        self.menu_popup.add(self.item_profile)
        self.menu_popup.add(self.item_copy)
        self.menu_popup.add(self.item_setname)
        self.menu_popup.add(self.item_takename)
        self.menu_popup.show_all()
        self.item_open.connect(    'activate', self.on_open_activated)
        self.item_profile.connect( 'activate', self.on_profile_activated)
        self.item_copy.connect(    'activate', self.on_copy_activated)
        self.item_setname.connect( 'activate', self.on_setname_activated)
        self.item_takename.connect('activate', self.on_takename_activated)
        self.connect('button_press_event', self.on_button_press_event)

        self.clipboard = gtk.Clipboard()
        self.srv = None

    def on_button_press_event(self, widget, event):
        path_at_pos = None
        if event.button == 3:
            path_at_pos = self.get_path_at_pos(int(event.x), int(event.y))
        if path_at_pos:
            self.menu_popup.popup(None, None, None, event.button, event.time)

    def on_open_activated(self, widget):
        (model, iterr) = self.get_selection().get_selected()
        text = model.get_value(iterr, self.COLUMN_COMM)
        start = text.find("http://")
        if end == -1:
            return
        end = text.find(" ")
        if end == -1:
            end = text.find("　")
        if end == -1:
            end = len(text)
        subprocess.call(["firefox", text[start:end]])

    def on_profile_activated(self, widget):
        (model, iterr) = self.get_selection().get_selected()
        name = model.get_value(iterr, self.COLUMN_UID)
        uid = self.nmdic[name]
        url = "http://www.nicovideo.jp/user/" + uid
        subprocess.call(["firefox", url])

    def on_copy_activated(self, widget):
        (model, iterr) = self.get_selection().get_selected()
        text = model.get_value(iterr, self.COLUMN_COMM)
        self.clipboard.set_text(text)

    def on_setname_activated(self, widget):
        (model, iterr) = self.get_selection().get_selected()
        name = model.get_value(iterr, self.COLUMN_UID)
        indlg = InputDialog()
        indlg.run()
        newname = indlg.get_text()
        indlg.destroy()
        if newname == "":
            return
        uid = self.nmdic[name]
        self.recordDic(uid, newname)
        model.set_value(iterr, self.COLUMN_UID, self.showName(uid))


    def on_takename_activated(self, widget):
        (model, iterr) = self.get_selection().get_selected()
        uid = model.get_value(iterr, self.COLUMN_UID)
        if uid.isdigit():
            uname = self.srv.takeUserName(uid)
            if uname is None:
                return
            self.recordDic(uid, uname)
            model.set_value(iterr, self.COLUMN_UID, self.showName(uid))

    def showName(self, uid):
        if self.udic.has_key(uid):
            uname = self.udic[uid]
            return uname + " :" + uid[:4]
        return uid[:10]

    def recordDic(self, uid, name):
        self.udic[uid] = name
        self.nmdic[self.showName(uid)] = uid

class MainWindow(gtk.Window):
    def __init__(self, *args, **kwargs):
        gtk.Window.__init__(self, *args, **kwargs)

        self.entry = gtk.Entry()
        # ショートカットキー(アクセラレータ)
        self.accelgroup = gtk.AccelGroup()
        self.add_accel_group(self.accelgroup)
        # メニュー項目
        self.item_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT, self.accelgroup)
        self.menu_file = gtk.Menu()
        self.menu_file.add(self.item_quit)
        self.item_file = gtk.MenuItem('_File')
        self.item_speech = gtk.MenuItem('_Speech ON')
        self.item_publish = gtk.MenuItem('_Publish')
        self.item_retake = gtk.MenuItem('_ReTake')
        self.item_reconn = gtk.MenuItem('_ReConnect')
        self.item_file.set_submenu(self.menu_file)
        self.menubar = gtk.MenuBar()
        self.menubar.append(self.item_file)
        self.menubar.append(self.item_speech)
        self.menubar.append(self.item_publish)
        self.menubar.append(self.item_retake)
        self.menubar.append(self.item_reconn)
        # ツリービュー
        self.view = CommListView(model=gtk.ListStore(str, str, str))
        self.view.set_rules_hint(True)
        if os.path.isfile("uid_dictionary"):
            udic = open("uid_dictionary")
            self.view.udic = json.load(udic)
            udic.close
        else:
            self.view.udic = {}
        # ツリービュー向けスクロールウィンドウ
        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.add(self.view)
        # レイアウト用コンテナ
        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.menubar, expand=False, fill=False)
        self.vbox.pack_start(self.entry, expand=False)
        self.vbox.pack_start(self.sw)
        # シグナル
        self.connect('delete_event', self.end_application)
        self.item_quit.connect('activate', self.end_application)
        self.item_speech.connect('activate', self.on_speech_activated, self.item_speech)
        self.item_publish.connect('activate', self.on_publish_activated)
        self.item_retake.connect('activate', self.on_retake_activated)
        self.item_reconn.connect('activate', self.on_reconn_activated)
        self.view.connect('size-allocate', self.on_view_changed)
        self.entry.connect("activate", self.on_entry_activated, self.entry)
        # ウィンドウ
        self.add(self.vbox)
        self.set_title("Ochawan")
        self.set_size_request(350, 300)

    def on_speech_activated(self, widget, speech):
        label = speech.get_label()
        if label == "_Speech ON":
            speech.set_label("_Speech OFF")
            self.view.srv.set_speech(False)
        else:
            speech.set_label("_Speech ON")
            self.view.srv.set_speech(True)

    def on_publish_activated(self, widget):
        lvid = self.view.srv.takeLvid()
        self.view.srv.lvid = lvid
        self.view.srv.getPlayerStatus()
        self.view.srv.getToken()
        self.view.srv.saveFmeXml(lvid)

        self.thread_start()
        self.proc = subprocess.Popen("./ffnico.sh", stdin=subprocess.PIPE)

    def on_retake_activated(self, widget):
        self.proc.stdin.write("q")
        subprocess.check_call(["./ochawan.py"])
        self.end_application(self)

    def on_reconn_activated(self, widget):
        self.thread_start()

    def on_view_changed(self, widget, event, data=None):
        adj = self.sw.get_vadjustment()
        print adj.get_value()
        if adj.get_value() < 50:
            adj.set_value(0)

    def on_entry_activated(self, widget, entry):
        msg = entry.get_text()
        res = self.view.srv.sendMsg(msg)
        if res == "status=ok":
            entry.set_text("")
        else:
            print res

    def takeComms(self):
        self.view.srv.takeComments(self.prependRow)

    def prependRow(self, no, uid, comm):
        print comm
        if comm == "/disconnect\n":
            self.proc.stdin.write("q")
            print "disconnect"
        name = self.view.showName(uid)
        self.view.nmdic[name] = uid
        index = comm.find("@")
        if index != -1:
            newname = comm[index:]
            self.view.recordDic(uid, newname)
            name = self.view.showName(uid)

        gtk.gdk.threads_enter()
        self.view.get_model().prepend((no, name, comm))
        gtk.gdk.threads_leave()

    def end_application(self, widget, data=None):
        udic = open("uid_dictionary", "w")
        json.dump(self.view.udic, udic)
        udic.close

        if not self.proc is None and self.proc.poll() is None:
            self.proc.stdin.write("q")
        gtk.main_quit()
        return False

    def thread_start(self):
        auto = threading.Thread(target=self.takeComms)
        auto.setDaemon(True)
        auto.start()

class InputDialog(gtk.Dialog):
    def __init__(self, *args, **kwargs):
        gtk.Dialog.__init__(self, *args, **kwargs)

        self.entry = gtk.Entry()
        self.vbox.add(self.entry)
        self.vbox.show_all()
        self.set_title("Input new name")
        self.set_size_request(200, 40)
        self.entry.connect("activate", self.on_entry_activated, self.entry)

    def on_entry_activated(self, widget, entry):
        self.hide()

    def get_text(self):
        return self.entry.get_text()

class CommGUI:

    def main(self):
        win = MainWindow()
        win.view.srv = ConServer.ConServer()

        if sys.platform == "win32":
            gobject.threads_init()
        else:
            gtk.gdk.threads_init()

        if len(sys.argv) == 1:
            win.show_all()
            gtk.main()
            return

        win.view.srv.lvid = sys.argv[1]
        win.view.srv.getPlayerStatus()
        win.view.srv.getToken()
        win.thread_start()
        if len(sys.argv) == 2:
            win.proc = subprocess.Popen("./ffnico.sh", stdin=subprocess.PIPE)
        win.show_all()
        gtk.main()


if __name__ == '__main__':
    app = CommGUI()
    app.main()

