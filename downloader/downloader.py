import sys,os,math,datetime,pg,json,Levenshtein, pickle
sys.path.append("packages")
import whatapi
from libzarv import *

def startup_tests():
  global db
  try:
    db = pg.connect('zarvox', user='kups', passwd='fuck passwords')
  except Exception:
    print("Error: cannot connect to database\n")
    exit(1)
  print("Zarvox database are online")
  try:
    pingtest(['whatcd','music'])
  except Exception:
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
  genres = [(1,'hip.hop','hip-hop','7')]#db.query("SELECT * FROM genres;").getresult()
  hour = datetime.datetime.now().hour
  credentials = getCreds()
  conf = getConfig()
  downloads = []
  #cookies = pickle.load(open('config/.cookies.dat', 'rb'))
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'])#, cookies=cookies)
  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  for genre in genres:
    #download based on pop
    try:
      subprocess.call(' bash downloader/downloadAdvTop10.sh \''+genre[1].replace("'","'\''")+"'", shell=True)
    except Exception:
      print("Execution of downloader.sh failed:\n")
      exit(1)
    popularity = 1#downloadFrequency(genre[3])
    subprocess.call('echo 32275904 >/tmp/.links', shell=True)
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
            'whatid' : album['torrent']['id'],
            'path_to_album':'/'+conf["albums_folder"].strip(' /') +'/'+albumPath,
            'album':album['group']['name'],
            'artist':album['group']['musicInfo']['artists'][0]['name'], #FIX THIS 
            #Songs need to be gotten by their levienshtein ratio to filenames and closeness of duration
            'format':album['torrent']['format'].lower()
          }
          i+=1
          fileAssoc = []
          for song in album['torrent']['fileList'].split("|||"):
            if song.split("{{{")[0].split('.')[-1].lower() == metadata['format']:
              temp = {}
              temp['size'] = song.split("{{{")[1][:-3]
              temp['name'] = song.split("{{{")[0].replace('&amp;','&').replace('&#39;',"'\\''")
              #reduce(lambda x1,x2,y1,y2: levi_misc(),[(x,y) for x in songList for y in songPathAssoc])
              fileAssoc.append(temp)
          if not os.path.isdir(metadata['path_to_album']):
            subprocess.call('mkdir \''+metadata['path_to_album'].replace("'","'\\''")+'\'', shell=True)
          print "Downloaded data for "+metadata['artist'] + " - "+metadata['album']
          data = {}
          data['metadata'] = metadata
          data['fileAssoc'] = fileAssoc
          with open(metadata['path_to_album']+"/.metadata.json",'w') as metadataFile:
            json.dump(data,metadataFile)
          downloads.append(metadata['artist'] + "-"+metadata['album'])
          #make folder for it, then make .info file with metadata
          #download a few (by popularity) torrents of each
          t=None
          torPath = conf['torrents_folder']+'/'+str(metadata['whatid'])+'.torrent'
          try:
            t = apihandle.get_torrent(metadata['whatid'])
          except Exception as e:
            print("Error: cannot retreive torrent for "+metadata['artist'] + "-"+metadata['album']+" despite being able to connect to what.cd\n"+"\nTrying a few more times...")
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