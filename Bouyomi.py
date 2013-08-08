#! /usr/bin/python
# -*- encoding: utf-8 -*-

import os, re, time, json
from ctypes import *

talk = cdll.LoadLibrary(os.getcwd() + "/libtalk.so")
dicfile = "BouyomiDictionary.txt"
transpattern = re.compile(u"教育(?:\(|（)([^=＝\)）]+)(?:=|＝)([^=＝\)）]+)(?:\)|）)")

class Bouyomi:
    def __init__(self):
        self.speech = True
        talk.open()
        self.readdic()
    def __del__(self):
        talk.close()
        self.writedic()
    def readdic(self):
        if not os.path.isfile(dicfile):
            print "Can not find 'BouyomiDictionary.txt'" 
            print "New file is created at end"
            self.dic = {}
        else:
            dictext = open(dicfile).read()
            self.dic = json.loads(dictext)
    def writedic(self):
        dictext = json.dumps(self.dic)
        open(dicfile, "w").write(dictext)

    def proc(self, text):
        if not self.speech:
            return
        if text.startswith("教育(") or text.startswith("教育（"):
            self.addWord(text)
            return
        elif text.startswith("忘却(") or text.startswith("忘却（"):
            self.rmWord(text)
            return
        for key, val in self.dic.iteritems():
            text = text.decode("utf-8")
            text = text.replace(key, val)
            text = text.encode("utf-8")
        cstr = c_char_p(text)
        result = talk.talk(cstr)


    def addWord(self, text):
        res = transpattern.match(text.decode("utf-8"))
        if res is None:
            result = talk.talk(c_char_p("教育失敗しました"))
            return
        key = res.group(1)
        val = res.group(2)
        self.dic[key] = val
        text = key + u"を" + val + u"と覚えました"
        cstr = c_char_p(text.encode("utf-8"))
        result = talk.talk(cstr)

    def rmWord(self, text):
        text = text.replace("忘却", "")
        if text.startswith("(") and text.endswith(")\n"):
            text = text.replace("(", "")
            text = text.replace(")\n", "")
        elif text.startswith("（") and text.endswith("）\n"):
            text = text.replace("（", "")
            text = text.replace("）\n", "")
        else:
            print "Error:" + text
            result = talk.talk(c_char_p(text + "忘却失敗しました"))
            return
        if not self.dic.has_key(text.decode("utf-8")):
            result = talk.talk(c_char_p(text + "を覚えていません"))
        else:
            del(self.dic[text.decode("utf-8")])
            result = talk.talk(c_char_p(text + "を忘れました"))

