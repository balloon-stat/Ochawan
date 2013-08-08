Ochawan
=======

ワンコマンドでニコニコ放送をはじめるためのスクリプト類です。  
コメントの読み上げ機能もあります。

Linuxでの使用を想定しています。
できるだけコードを読んだ上での使用をお願いします。

コメントの読み上げ機能にAnthyとAquesTalkを必要とします。  
それぞれ共有ライブラリを用意してロードできる状態にしてください。

libtalk.soはその他のファイルと同じディレクトリに置くだけで良いです。  
libtalk.soのソースはsrc内にあります。

お好みのPhontファイルをaq.phontという名前にリネームして用意してください。

Cookieの取得はCookieProcessor.pyで行なっています。  
デフォルトはFireFoxになっています。  
Chromeを使っている方はコードを書き換えてください。


動画の配信はffmpegで行います。ffnico.shで設定の確認をしてください。

ochawan.pyを開いてそれぞれ変数に放送内容を書いてください。
* title
* content
* community
* category
* livetags

ochawan.pyを実行するとその内容で枠をとって放送ページを開きます。
