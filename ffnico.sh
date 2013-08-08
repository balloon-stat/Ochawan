#!/bin/bash

url=`xmlstarlet sel -t -v /flashmedialiveencoder_profile/output/rtmp/url nicolive_fme.xml`

stream=`xmlstarlet sel -t -v /flashmedialiveencoder_profile/output/rtmp/stream nicolive_fme.xml `

ffmpeg -re -r 5 \
-f x11grab -s 512x384 -i :0.0+190,165 \
-f alsa -ac 2 -i pulse -acodec libmp3lame -strict unofficial \
-vcodec libx264 -bt 200k -ar 22050 -ab 48k -threads 1 -tune zerolatency \
-pix_fmt yuv420p -vsync 1 -y \
-f flv ${url}/${stream}

