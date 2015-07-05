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
  genres = [(1,'black.metal','rock','7')]#db.query("SELECT * FROM genres;").getresult()
  hour = datetime.datetime.now().hour
  credentials = getCreds()
  conf = getConfig()
  downloads = []
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'])
  for genre in genres:
    #download based on pop
    try:
      subprocess.call(' bash downloader/downloadAdvTop10.sh "'+genre[1]+'"', shell=True)
    except Exception, e:
      print("Execution of downloader.sh failed:\n"+str(e))
      exit(1)
    popularity = 3#downloadFrequency(genre[3])
    with open("/tmp/.links") as f:
      i=0
      for line in iter(f):
        if i==popularity:
          break
        album = apihandle.request("torrent", id=line)["response"]
        #only continue if freetorrent is false and categoryname=music
        if album['torrent']['freeTorrent'] or not album['group']['categoryName']=='Music':
          print("Error: freeTorrent is "+str(album['torrent']['freeTorrent'])+" and categoryName is "+ album['group']['categoryName'])
        elif album['group']['musicInfo']['artists'][0]['name']+"-"+album['group']['name'] in downloads:
          print("Skipping current download since already downloaded")
        else:
          albumPath = album["torrent"]["filePath"]
          metadata = {
            'whatid' = album['torrent']['id'],
            'path_to_album':'/'+conf["albums_folder"].strip(' /') +'/'+albumPath,
            'album':album['group']['name'],
            'artist':album['group']['musicInfo']['artists'][0]['name'], #FIX THIS 
            #Songs need to be gotten by their levienshtein ratio to filenames and closeness of duration
            'format':album['torrent']['format'].lower()
          }
          i+=1
          lastfmList = lookup('lastfm','album',{'artist':metadata['artist'], 'album':metadata['album']})['album']['tracks']['track']
          songList = [ (track['name'],track['@attr']['rank'],track['duration']) for track in lastfmList]
          songAssoc = []
          for lastfmSong in songList:
            temp = {}
            temp['name'] = lastfmSong[0] #sanitize for unicode?
            temp['filename']=(('0'+str(lastfmSong[1])) if int(lastfmSong[1])<10 else str(lastfmSong[1]))+'-'+metadata['artist'].replace(' ','_')+'-'+lastfmSong[0].replace(' ','_')+'.'+metadata['format']
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
          if not os.path.isdir(path_to_album):
            subprocess.call('mkdir \''+path_to_album+'\'', shell=True)
          print "Downloaded data for "+metadata['artist'] + " - "+metadata['album']
          with open(path_to_album+"/.metadata.json",'w') as metadataFile:
            json.dump(data,metadataFile)
          downloads.append(metadata['artist'] + "-"+metadata['album'])
          #make folder for it, then make .info file with metadata
          #download a few (by popularity) torrents of each
          t=None
          torPath = config['torrents_folder']+'/'+metadata['whatid']+'.torrent'
          try:
            t = apihandle.get_torrent(metadata['whatid'])
          except Exception as e:
            print("Error: cannot retreive torrent for "+metadata['artist'] + "-"+metadata['album']+" despite being able to connect to what.cd\n"+str(e)+"\nTrying a few more times...")
            for _ in xrange(3):
              time.sleep(10)
              if not os.path.isfile(torPath):
                try:
                  t = apihandle.get_torrent(metadata['whatid'])
                except:
                  pass
          if t is not None:
            with open(torPath, 'wb') as fd:
              fd.write(t)

if  __name__ == '__main__':
  main()