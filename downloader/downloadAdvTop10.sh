#!/bin/bash
user_agent="Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.12) Gecko/20080201 Firefox/2.0.0.12" #This might be an unnecessary precaution
if [ ! -f "config/cookies.dat" ]; then
  username="$(cat config/credentials |grep username|cut -d= -f2)"
  password="$(cat config/credentials |grep password|cut -d= -f2)"
  curl -c "config/cookies.dat" -d"username=$username&password=$password" "https://ssl.what.cd/login.php"
  #wget --save-cookies "config/cookies.dat" --keep-session-cookies --post-data "username=$username&password=$password" "https://ssl.what.cd/login.php"
fi
#wget --load-cookies "config/cookies.dat" -p "https://ssl.what.cd/top10.php?type=torrents&advanced=1&limit=10&details=day&tags=$1" -O /tmp/.whattop10page
curl -b "config/cookies.dat" "https://ssl.what.cd/top10.php?type=torrents&advanced=1&limit=10&details=day&tags=$1" -o /tmp/.whattop10page
cat /tmp/.whattop10page | grep '<span><a href="torrents.php?action=download' | cut -d'"' -f2 | cut -d= -f3 | cut -d\& -f1 > /tmp/.links