import sys,os,math,datetime,json,Levenshtein, pickle, io
sys.path.append("packages")
import whatapi
from libzarv import *
from numpy import float128
from html import unescape

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
  global apihandle
  # db = startup_tests()
  #get all subgenres
  genres = [(1,'hip.hop','hip-hop','7')]#db.query("SELECT * FROM genres;").getresult()
  hour = datetime.datetime.now().hour
  credentials = getCreds()
  conf = getConfig()
  downloads = []
  credentials = getCreds()
  cookies = {'cookies':pickle.load(open('config/.cookies.dat', 'rb'))} if os.path.isfile('config/.cookies.dat') else {}
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], **cookies)
  for genre in genres:
    #download based on pop
    try:
      #subprocess.call(' bash downloader/downloadAdvTop10.sh \''+genre[1].replace("'","'\''")+"'", shell=True)
      subprocess.call('echo 72914207>/tmp/.links',shell=True)
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
        metadata = getTorrentMetadata(albumGroup)
        metadata['path_to_album'] = '/'+conf["albums_folder"].strip(' /') +metadata['path_to_album']
    
        #only continue if freetorrent is false and categoryname=music
        if int(hash(''.join(metadata['artist']+[metadata['album']]))) in downloads:
          print("Skipping current download since already downloaded")
        else:
          i+=1
          fileAssoc = []
          torrent = [x for x in albumGroup["torrents"] if x['id']==metadata['whatid']][0]
          for song in torrent['fileList'].split("|||"):
            if song.split("{{{")[0].split('.')[-1].lower() == metadata['format']:
              temp = {}
              temp['size'] = song.split("{{{")[1][:-3]
              temp['name'] = unescape(song.split("{{{")[0]).encode('latin-1').decode('unicode-escape')
              #reduce(lambda x1,x2,y1,y2: levi_misc(),[(x,y) for x in songList for y in songPathAssoc])
              fileAssoc.append(temp)
          if not os.path.isdir(metadata['path_to_album']):
            subprocess.call('mkdir \''+metadata['path_to_album'].replace("'","'\\''")+'\'', shell=True)
          print("Downloaded data for "+' & '.join(metadata['artist']) + " - "+metadata['album'])
          data = {}
          data['metadata'] = metadata
          data['fileAssoc'] = fileAssoc
          with io.open(metadata['path_to_album']+"/.metadata.json",'w',encoding='utf8') as metadataFile:
            json.dump(data,metadataFile, ensure_ascii=False)
          downloads.append(int(hash(''.join(metadata['artist']+[metadata['album']]))))
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