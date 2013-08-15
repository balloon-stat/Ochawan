#! /usr/bin/python
# -*- encoding: utf-8 -*-

import re
import sys
import subprocess
import urllib
import urllib2
import socket
import threading
import asyncore
import time
from CookieProcessor import CookieProcessor
from HTMLParser import HTMLParser
from xml.etree.ElementTree import *

import Bouyomi

class ConServer:
    def __init__(self, lvid=""):
        self.count = 0
        self.postkey = ""
        self.token = ""
        self.opener = urllib2.build_opener(CookieProcessor.get())

        self.lvid = lvid
        self.addr = ""
        self.port = ""
        self.thread = ""
        if not lvid == "":
            self.getPlayerStatus()

    def getPlayerStatus(self):
        url = "http://live.nicovideo.jp/api/getplayerstatus?v=" + self.lvid
        res = self.opener.open(url).read()
        elem = fromstring(res)

        self.addr   = elem.findtext(".//addr")
        self.port   = elem.findtext(".//port")
        self.thread = elem.findtext(".//thread")

    def set_speech(self, speech):
        self.bym.speech = speech

    def getPostKey(self):
        block_no = self.count // 100
        url = "http://live.nicovideo.jp/api/getpostkey?thread=%s&block_no=%s" % (self.thread, block_no)
        res = self.opener.open(url).read()
        self.postkey = res[8:]

    def getToken(self):
        url = "http://live.nicovideo.jp/api/getpublishstatus?v="
        res = self.opener.open(url + self.lvid).read()
        elem = fromstring(res)
        self.token = elem.findtext(".//token")

    def sendMsg(self, body, mail=None):
        urlprefix = "http://watch.live.nicovideo.jp/api/broadcast/"
        if mail is None:
            query = [
                ("body",  body),
                ("token", self.token)
            ]
        else:
            query = [
                ("body",  body),
                ("mail",  mail),
                ("token", self.token)
            ]
        url = urlprefix + self.lvid + "?" + urllib.urlencode(query)
        res = self.opener.open(url).read()
        return res

    def takeUserName(self, uid):
        try:
            url = "http://www.nicovideo.jp/user/" + uid
            res = self.opener.open(url).read()
            uparser = UserNameParser()
            uparser.feed(res.decode("utf-8"))
            return uparser.name
        except urllib2.HTTPError:
            print "ユーザ名の取得に失敗しました"
            return None

    def takeLvid(self):
        url = "http://live.nicovideo.jp/my"
        res = self.opener.open(url).read()
        lvparser = LvidParser()
        lvparser.feed(res)
        return lvparser.lvid

    def saveFmeXml(self, lvid):
        url_profile = "http://watch.live.nicovideo.jp/api/getfmeprofile?v="
        res = self.opener.open(url_profile + lvid).read()
        open("nicolive_fme.xml", "w").write(res)

    def takeComments(self, proc=lambda no, uid, comm: None):
        host = socket.gethostbyname(self.addr)
        return takeCommentThread(host, int(self.port), self.thread, proc)

class takeCommentThread(threading.Thread):
    def __init__(self, host, port, thread, proc):
        threading.Thread.__init__(self)
        self.info = (host, port, thread)
        self.proc = proc

    def run(self):
        self.comc = CommClient(self.info, self.proc)
        asyncore.loop()

    def resend(self):
        self.comc.resend()

    def close(self):
        self.comc.close()

#原宿バージョンとQバージョン両対応
class UserNameParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.isin = False
        self.isname = False
        self.name = ""

    def handle_starttag(self, tag, attr):
        if tag == "div":
            for i in attr:
                if i[0] == "id" and i[1] == "headingUser":
                    self.isin = True
                if i[0] == "class" and i[1] == "profile":
                    self.isname = True
        elif tag == "strong" and self.isin:
            self.isname = True
        elif tag == "small":
            self.isname = False

    def handle_endtag(self, tag):
        if tag == "div":
            self.isin = False
        elif tag == "strong":
            self.isname = False

    def handle_data(self, data):
        if self.isname and self.name == "":
            self.name = data

class LvidParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.lvid = ""

    def handle_starttag(self, tag, attr):
        if tag == "a":
            for i in attr:
                if i[0] == "title" and i[1] == "生放送ページへ戻る":
                    for j in attr:
                        if j[0] == "href":
                            self.lvid = j[1].replace("http://live.nicovideo.jp/watch/", "").replace("?ref=my_live", "")

class CommClient(asyncore.dispatcher):
    def __init__(self, info, proc):
        asyncore.dispatcher.__init__(self)
        (host, port, thread) = info
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( (host, port) )
        self.thread = thread
        self.buf = "<thread thread=\"" + thread + "\" version=\"20061206\" res_from=\"-100\"/>\0"
        self.prev = ""
        self.proc = proc
        self.count = 0

    def resend(self):
        self.buf = "<thread thread=\"" + self.thread + "\" version=\"20061206\" res_from=\"-1\"/>\0"

    def handle_close(self):
        print "close"
        self.close()

    def handle_read(self):
        res = self.recv(1024)
        if res.startswith("<chat") and res.endswith("</chat>"):
            xml = res
        else:
            xml = self.prev + res
            self.prev = ""

#<thread hoge />\0<chat>情報</chat>\0<chat>情報</chat>\0の形で受信する
        for line in xml.split("\0"):
            if line.startswith("<thread"):
                elem = fromstring(line)
                comticket = elem.findtext(".//ticket")
                srvtime = elem.findtext(".//sever_time")
                continue

            if not line.endswith("</chat>"):
                self.prev = line
                continue

            if line.startswith("<chat_result"):
                continue

            if line.startswith("<chat"):
                elem = fromstring(line)
                text = elem.text + "\n"
                self.proc(elem.get("no"), elem.get("user_id"), text)
                if text == "/disconnect\n":
                    time.sleep(2)
                    self.close()
                    return
                self.count = int(elem.get("no"))
                continue

    def writable(self):
        return (len(self.buf) > 0)

    def handle_write(self):
        sent = self.send(self.buf)
        self.buf = self.buf[sent:]

"""
bym = Bouyomi.Bouyomi()

def proc(no, uid, text):
    bym.proc(text.encode('utf-8'))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "use: ConServer.py lvxxxxxx"
    con = ConServer(sys.argv[1])
    thread = con.takeComments(proc)
    thread.start()
    while True:
        if raw_input() == 'q':
            print "closing..."
            thread.close()
            break
"""
