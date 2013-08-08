#!/usr/bin/python
# -*- coding: utf-8 -*-

title = "放送タイトル"
content = u"""放送詳細"""

community = "放送コミュ番号"
category = "一般(その他)"
livetags = ["タグ１", "タグ２"]

"""
"一般(その他)", "政治", "動物", "料理", "演奏してみた","歌ってみた",
"踊ってみた", "描いてみた", "講座", "ゲーム", "動画紹介", "R18"
"""

import os
from TakeWak import TakeWak
from subprocess import *

tw = TakeWak()
tw.title = title
tw.content = content
tw.community = community
tw.category = category
tw.livetags = livetags

lvid = tw.take();
if lvid == "":
    check_call(["firefox", "temp.html"])
    check_call(["./CommGUI.py"])
    exit()

check_call(["firefox", "http://live.nicovideo.jp/watch/" + lvid])
check_call(["./CommGUI.py", lvid])
