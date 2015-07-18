import sys,os,math,datetime,json,Levenshtein, pickle,musicbrainzngs as mb
from decimal import Decimal
sys.path.append("packages")
import whatapi
from libzarv import *
from numpy import float128

formats = ['MP3','FLAC','AC3','ACC','DTS']

encoding = ['V0', 'Lossless','24bit Lossless']

def compareTors(x,y):
  def getEncoding(z):
    def calcLosslessness(bitrate):
      return 0.0724867+ float128(Decimal(bitrate-220.0)**Decimal(0.3940886699507389))
    if z in encoding:
      return encoding.index(z)
    else:
      if z[0] == 'V':
        return int(z[1])+2
      else:
        if str(int(z)) == z:
          if int(z) >= 220:
            return calcLosslessness(float(z))
          else:
            return calc_vbr(int(z))+2
        else:
          return 11
  if formats.index(x['format']) != formats.index(y['format']):
    return x if formats.index(x['format'])<formats.index(y['format']) else y
  ex,ey = getEncoding(x['encoding']), getEncoding(y['encoding'])
  if ex != ey:
    return x if ex>ey else y
  return x if x['seeders']>=y['seeders'] else y

def startup_tests():
  # try:
  #   db = pg.connect('zarvox', user='kups', passwd='fuck passwords')
  # except Exception:
  #   print("Error: cannot connect to database\n")
  #   exit(1)
  print("Zarvox database are online")
  try:
    pingtest(['whatcd','music'])
  except Exception:
    print(e)
    exit(1)
  print("Pingtest complete; sites are online")
  # return db


#Usage (to be ran from root of zarvox): python downloader.py
def main():
  # db = startup_tests()
  #get all subgenres
  genres = [(1,'hip.hop','hip-hop','7')]#db.query("SELECT * FROM genres;").getresult()
  hour = datetime.datetime.now().hour
  credentials = getCreds()
  conf = getConfig()
  downloads = []
  credentials = getCreds()
  cookies = pickle.load(open('config/.cookies.dat', 'rb'))
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
  for genre in genres:
    #download based on pop
    try:
      subprocess.call(' bash downloader/downloadAdvTop10.sh \''+genre[1].replace("'","'\''")+"'", shell=True)
    except Exception:
      print("Execution of downloader.sh failed:\n")
      exit(1)
    popularity = 1#downloadFrequency(genre[3])
    with open("/tmp/.links") as f:
      i=0
      for line in iter(f):
        if i==popularity:
          break
        albumGroup = apihandle.request("torrentgroup", id=line)["response"]
        #determine trueartists using musicbrainz
        if len(albumGroup['group']['musicInfo']['artists']) == 1:
          artists = albumGroup['group']['musicInfo']['artists']
        else:
          mb.set_useragent('Zarvox Automated DJ','Pre-Alpha',"KUPS' Webmaster (Jon Sims) at jsims@pugetsound.edu")
          albums = []
          for x in albumGroup['group']['musicInfo']['artists']:
            albums+=mb.search_releases(artistname=x,release=albumGroup['group']['name'],limit=10)['release-list'])
          ranks = {}
          for x in albums:
            ranks[x['id']]=Levenshtein.ratio(albumGroup['group']['name'].lower(),x['title']) + (ranks[x['id']] if x['id'] in ranks else 0)
          albumid = reduce(lambda x1,x2,y1,y2: (x1,x2) if x2>y2 else (y1,y2),ranks.items())[0]
          album = mb.get_release_by_id(id=albumid, includes=['recordings'])
        #only continue if freetorrent is false and categoryname=music
        if albumGroup['group']['musicInfo']['artists'][0]['name']+"-"+albumGroup['group']['name'] in downloads:
          print("Skipping current download since already downloaded")
        else:
          torrent = reduce(lambda x,y: compareTors(x,y),albumGroup["torrents"])
          metadata = {
            'whatid' : torrent['id'],
            'path_to_album':'/'+conf["albums_folder"].strip(' /') +'/'+torrent["filePath"],
            'album':albumGroup['group']['name'],
            'artist':albumGroup['group']['musicInfo']['artists'][0]['name'], #FIX THIS 
            #Songs need to be gotten by their levienshtein ratio to filenames and closeness of duration
            'format':torrent['format'].lower()
          }
          i+=1
          fileAssoc = []
          for song in torrent['fileList'].split("|||"):
            if song.split("{{{")[0].split('.')[-1].lower() == metadata['format']:
              temp = {}
              temp['size'] = song.split("{{{")[1][:-3]
              temp['name'] = song.split("{{{")[0].replace('&amp;','&').replace('&#39;',"'\\''")
              #reduce(lambda x1,x2,y1,y2: levi_misc(),[(x,y) for x in songList for y in songPathAssoc])
              fileAssoc.append(temp)
          if not os.path.isdir(metadata['path_to_album']):
            subprocess.call('mkdir \''+metadata['path_to_album'].replace("'","'\\''")+'\'', shell=True)
          print("Downloaded data for "+metadata['artist'] + " - "+metadata['album'])
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
  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  

if  __name__ == '__main__':
  main()