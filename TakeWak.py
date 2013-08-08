#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import MultipartPostHandler
from HTMLParser import HTMLParser
from CookieProcessor import CookieProcessor


class ExtractContentParser(HTMLParser):

    def __init__(self):
        self.content = ""
        self.confirm = ""
        HTMLParser.__init__(self)

    def handle_starttag(self,tagname,attribute):
        if tagname == "input":
            for i in attribute:
                if i[0] == "name" and i[1] == "description":
                    for j in attribute:
                        if j[0] == "value":
                            self.content = j[1]
                if i[0] == "name" and i[1] == "confirm":
                    for j in attribute:
                        if j[0] == "value":
                            self.confirm = j[1]

class ExtractLvidParser(HTMLParser):

    def __init__(self):
        self.lvurl = ""
        self.lvid = ""
        HTMLParser.__init__(self)

    def handle_starttag(self,tagname,attribute):
        if tagname == "meta":
            for i in attribute:
                if i[0] == "property" and i[1] == "og:url":
                    for j in attribute:
                        if j[0] == "content":
                            self.lvurl = j[1]
                            self.lvid = self.lvurl.replace("http://live.nicovideo.jp/watch/", "")

class TakeWak:

    def __init__(self):
        self.title = "";
        self.community = "";
        self.category = "";
        self.content = "";
        self.livetags = [];

    def set_params(self):
        content = self.content.replace("\n","<br />\r\n").encode("utf-8")
        params = { "is_wait" : "", "usecoupon": "", "title": self.title,
                "default_community": self.community, "timeshift_enabled": 1,
                    "tags[]": self.category, "description": content}
        index = 1
        for tag in self.livetags:
            params["livetags" + str(index)] = tag
            index += 1

        self.params = params

    def take(self):
        url_editstream = "http://live.nicovideo.jp/editstream"
        url_profile = "http://watch.live.nicovideo.jp/api/getfmeprofile?v="

        self.set_params()
        opener = urllib2.build_opener(CookieProcessor.get(),
                MultipartPostHandler.MultipartPostHandler)
        res = opener.open(url_editstream, self.params).read()

        cparser = ExtractContentParser()
        cparser.feed(res)
        cparser.close()
        self.params["description"] = cparser.content
        self.params["confirm"] = cparser.confirm
        self.params["kiyaku"] = "true"

        res = opener.open(url_editstream, self.params).read()

        self.writefile("temp.html", res)
        lvparser = ExtractLvidParser()
        lvparser.feed(res.decode("utf-8"))
        lvparser.close()
        lvid = lvparser.lvid

        if lvid != "":
            res = opener.open(url_profile + lvid).read()
            self.writefile("nicolive_fme.xml", res)

        return lvid

    def writefile(self, filename, page):
        f = open(filename, "w")
        f.write(page)
        f.close()

