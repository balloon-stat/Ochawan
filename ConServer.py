#! /usr/bin/python
# -*- encoding: utf-8 -*-

import re
import sys
import subprocess
import urllib
import urllib2
import socket
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
        self.bym = Bouyomi.Bouyomi()
        self.uparser = UserNameParser()
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
            self.uparser.feed(res.decode("utf-8"))
            return self.uparser.name
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
        sock = socket.socket()
        sock.connect((host, int(self.port)))
        sock.send("<thread thread=\"" + self.thread + "\" version=\"20061206\" res_from=\"-100\"/>\0")

        prev = ""
        while True:
            res = sock.recv(1024)
            if res.startswith("<chat") and res.endswith("</chat>"):
                xml = res
            else:
                xml = prev + res
                prev = ""

#<thread hoge />\0<chat>情報</chat>\0<chat>情報</chat>\0の形で受信する
            for line in xml.split("\0"):
                if line.startswith("<thread"):
                    elem = fromstring(line)
                    comticket = elem.findtext(".//ticket")
                    srvtime = elem.findtext(".//sever_time")
                    break

                if not line.endswith("</chat>"):
                    prev = line
                    break

                if line.startswith("<chat_result"):
                    break

                if line.startswith("<chat"):
                    elem = fromstring(line)
                    text = elem.text + "\n"
                    proc(elem.get("no"), elem.get("user_id"), text)
                    if text == "/disconnect\n":
                        self.bym.proc("終了しました")
                        time.sleep(2)
                        exit()
                    self.bym.proc(text.encode("utf-8"))
                    self.count = int(elem.get("no"))

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
        if self.isname:
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
"""
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "use: ConServer.py lvxxxxxx"
    con = ConServer(sys.argv[1])
    con.takeComments()
"""
