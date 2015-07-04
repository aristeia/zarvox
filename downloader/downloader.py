import sys,os,math,datetime,pg,json,Levenshtein
sys.path.append("packages")
import whatapi
from libzarv import *


def startup_tests():
  global db
  try:
    db = pg.connect('zarvox', user='kups', passwd='fuck passwords')
  except Exception, e:
    print("Error: cannot connect to database\n"+str(e))
    exit(1)
  print("Zarvox database are online")
  try:
    pingtest(['whatcd'])
  except Exception, e:
    print(e)
    exit(1)
  print("Pingtest complete; sites are online")

#classvars
credentials = None
apihandle = None
db = None
conf = None

#Usage (to be ran from root of zarvox): python downloader.py
def main():
  global db,credentials,apihandle,conf
  #get all subgenres
  startup_tests()
  genres = ['black.metal']#db.query("SELECT * FROM genres;").getresult()
  hour = datetime.datetime.now().hour
  credentials = getCreds()
  conf = getConfig()
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'])
  for genre in genres:
    #download based on pop
    try:
      subprocess.call(' bash downloader/downloadAdvTop10.sh "'+genre[1]+'"', shell=True)
    except Exception, e:
      print("Execution of downloader.sh failed:\n"+str(e))
      exit(1)
    popularity = 2#downloadFrequency(genre[3])
    with open("/tmp/.lines") as f:
      for line in iter(f)[0:(popularity+1)]:
        album = apihandle.request("torrent", id=line)["response"]
        #only continue if freetorrent is false and categoryname=music
        if album['torrent']['freeTorrent'] or not album['group']['categoryName']=='Music':
          print("Error: freeTorrent is "+str(album['torrent']['freeTorrent'])+" andcategoryName is "+ album['group']['categoryName'])
          break
        albumPath = album["torrent"]["filePath"]
        path_to_album = '/'+conf["albums_folder"].strip(' /') +albumPath
        metadata = {
          'path_to_album':'/'+conf["albums_folder"].strip(' /') + '/'+albumPath,
          'album':album['group']['name'],
          'artist':album['group']['musicInfo'],
          #Songs need to be gotten by their levienshtein ratio to filenames and closeness of duration
          'format':album['torrent']['format'].lower()
        }
        lastfmList = lookup('lastfm','album',{'artist':song.artist, 'album':song.album})['album']['tracks']['track']
        songList = [ (track['name'],track['rank'],track['duration']) for track in lastfmList]
        songAssoc = []
        for lastfmSong in songList:
          temp = {}
          temp['name']=lastfmSong[1]+'-'+metadata['artist'].replace(' ','-')+'-'+lastfmSong[0].replace(' ','-')+'.'+metadata['format']
          temp['duration']=lastfmSong[2]
          songAssoc.append(temp)
        fileAssoc = []
        for song in album['torrent']['fileList'].split("|||"):
          if song.split("{{{")[0].split('.')[1].lower() == metadata['format']:
            temp = {}
            temp['size'] = song.split("{{{")[1][:-3]
            temp['name'] = song.split("{{{")[0]
            #reduce(lambda x1,x2,y1,y2: levi_misc(),[(x,y) for x in songList for y in songPathAssoc])
            fileAssoc.append(temp)
        data = {}
        data['metadata'] = metadata
        data['songAssoc'] = songAssoc
        data['fileAssoc'] = fileAssoc
        subprocess.call('mkdir '+path_to_album, shell=True)
        with open(path_to_album+"/.metadata.json",'w') as metadataFile:
          json.dump(data,metadataFile)
  #make folder for it, then make .info file with metadata
  #download a few (by popularity) torrents of each




if  __name__ == '__main__':
  main()