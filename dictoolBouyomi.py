#! /usr/bin/python
# -*- encoding: utf-8 -*-

import os, re, time, json
from ctypes import *
from subprocess import *

talk = cdll.LoadLibrary(os.getcwd() + "/libtalk.so")
transpattern = re.compile(u"教育(?:\(|（)([^=＝\)）]+)(?:=|＝)([^=＝\)）]+)(?:\)|）)")
dic_code = u"""
格助詞接続	=	y
語幹のみで文節	=	y
する接続	=	n
さ接続	=	n
な接続	=	n
品詞	=	名詞


"""
class Bouyomi:
    def __init__(self):
        talk.open()
        proc = Popen(["anthy-dic-tool", "--dump", "--utf8"], stdout=PIPE)
        self.dic_text = proc.stdout.read()
        proc.wait()

    def __del__(self):
        talk.close()

    def proc(self, text):
        if text.startswith("教育(") or text.startswith("教育（"):
            self.addWord(text)
            return
        elif text.startswith("忘却(") or text.startswith("忘却（"):
            self.rmWord(text)
            return
        cstr = c_char_p(text)
        result = talk.talk(cstr)


    def addWord(self, text):
        res = transpattern.match(text.decode("utf-8"))
        if res is None:
            result = talk.talk(c_char_p("教育失敗しました"))
            return
        key = res.group(1)
        val = res.group(2)
        dic_text = key + ' 500 ' + val + dic_code
        proc = Popen(["anthy-dic-tool", "--append", "--utf8"], stdin=PIPE)
        dic_text = dic_text.encode("utf-8")
        proc.stdin.write(dic_text)
        proc.stdin.write("\x04")
        time.sleep(0.5)
        proc.terminate()
        self.dic_text += dic_text
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
        dct = self.dic_text
        result = dct.find(" " + text + "\n")
        if result == -1:
            result = talk.talk(c_char_p(text + "を覚えていません"))
        else:
            para_start = dct.rfind("\n", 0, result)
            para_start += 1
            para_end = dct.find("\n\n", result)
            dct = dct.replace(dct[para_start:para_end], "")
            proc = Popen(["anthy-dic-tool", "--load", "--utf8"],stdin=PIPE)
            proc.stdin.write(dct.encode("utf-8"))
            proc.stdin.write('\x03')
            ret = proc.wait()
            print "anthy-dic-tool return code:" + ret
            self.dic_text = dct
            result = talk.talk(c_char_p(text + "を忘れました"))

