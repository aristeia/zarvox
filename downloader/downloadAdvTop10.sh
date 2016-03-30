#!/bin/bash 
rm -f '/tmp/.links' '/tmp/.whatpage'
user_agent="Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.12) Gecko/20080201 Firefox/2.0.0.12" #This might be an unnecessary precaution
#if [ ! -f "config/.curl_cookies.dat" ] || [ "$(find config -mtime 1 | grep '.curl_cookies.dat')" ]; then
username="$(cat config/credentials |egrep '^username'|cut -d= -f2)"
password="$(cat config/credentials |egrep '^password'|cut -d= -f2)"
echo "$username $password"
#curl -c "config/.curl_cookies.dat" -d"username=$username&password=$password" "https://ssl.what.cd/login.php"
wget --save-cookies "config/.bash_cookies.dat" --keep-session-cookies --post-data "username=$username&password=$password" "https://ssl.what.cd/login.php"
# fi
wget --load-cookies "config/.bash_cookies.dat" -p "https://ssl.what.cd/top10.php?type=torrents&advanced=1&limit=10&details=day&tags=$1" -O /tmp/.whatpage
#curl -b "config/.curl_cookies.dat" "https://ssl.what.cd/top10.php?type=torrents&advanced=1&limit=10&details=week&tags=$1" -o /tmp/.whatpage
cat /tmp/.whatpage | egrep "\<strong.*\<a\ href" | python3 -c "import sys 
for x in sys.stdin: print(x.split('torrents.php?id=')[1].split('&')[0])" > /tmp/.links