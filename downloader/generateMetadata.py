'''
generateMetadata.py

"Given a folder containing music, determine its metadata and fileassociations,
  writing them to a file to be read by the postprocessor."

Major functions:
- get most frequent extension
- get artist and album metadata from all files of extension
- use folder name as backup album name
- use most frequent substring in filenames as backup artist name
- search musicbrainzngs for album & artist credit phrase
- search what for album & artists
- use this whatgroup and artist-credit-phrase to generate metadata
- use metadata to generate file assoc
- save both to file

'''
import sys,os,math,datetime,re, io,json,postgresql as pg,Levenshtein, pickle,musicbrainzngs as mb
sys.path.append("packages")
import whatapi
from libzarv import *
from numpy import float128
from html import unescape

def startup_tests(args, credentials):
  if len(args) != 2:
    print("Error: postprocessor received wrong number of args")
    exit(1)
  # try:
  db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_password']+'@localhost/'+credentials['db_name'])
  # except Exception:
  #   print("Error: cannot connect to database\n")
  #   exit(1)
  print("Zarvox database are online")
  try:
    pingtest(['whatcd'])
  except Exception:
    print(e)
    exit(1)
  print("Pingtest complete; sites are online")
  return db

def searchWhatAlbums(apihandle,args):
  if len(args)==0:
    return []
  whatResponse = apihandle.request(action='browse',searchstr=args[0])
  if whatResponse['status']=='success':
    args.pop(0)
    return whatResponse['response']['results']+searchWhatAlbums(apihandle,args)
  return []

def main():
  global apihandle
  credentials = getCreds()
  db = startup_tests(sys.argv,credentials)
  #get all subgenres
  conf = getConfig()
  path_to_album = conf['albums_folder']+'/'+sys.argv[1]+'/'
  downloads = []
  credentials = getCreds()
  cookies = {'cookies':pickle.load(open('config/.cookies.dat', 'rb'))} if os.path.isfile('config/.cookies.dat') else {}
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], **cookies)
  extensions = [y for y in [x.split('.')[-1] for x in os.listdir(path_to_album) if os.path.isfile(path_to_album+x)] if y in ['mp3','flac','acc','alac','wav','wma','ogg','m4a']]
  if len(extensions)>0:
    extension = max([(x,extensions.count(x)) for x in set(extensions)],key=(lambda x:x[1]))[0]
  else:
    print("Error: cannot get extension")
    exit(1)
  artists = []
  albums = []
  for f in os.listdir(path_to_album):
    if f[(-1*len(extension)):]==extension:
      artists+=[x.strip() for x in subprocess.check_output("exiftool -Artist '"+(path_to_album+f).replace("'","'\\''")+"' | cut -d: -f2-10",shell=True).decode('utf8').strip().split('\n')]
      albums+=[x.strip() for x in subprocess.check_output("exiftool -Album -Product '"+(path_to_album+f).replace("'","'\\''")+"' | cut -d: -f2-10",shell=True).decode('utf8').strip().split('\n')]
  artistSubstring = reduce(
      getLongestSubstring
      , [f for f in os.listdir(path_to_album) if f[(-1*len(extension)):]==extension]).replace('_',' ').strip(' -')
  if len(albums)==0:
    print("No albums found in metadata; trying folder name")
    album = sys.argv[1].replace('_',' ').strip(' -')
  else:
    album = max([(x,albums.count(x))for x in set(albums)], key=(lambda x:x[1]))[0]
  if len(artists)==0:
    print("No artists found in metadata; trying common substrings in filenames")
    artist = artistSubstring
  else:
    artist = max([(x,artists.count(x))for x in set(artists)], key=(lambda x:x[1]))[0]
  print("For the provided dir "+path_to_album+", the following artist and album was found:")
  print("Artist: "+artist)
  print("Album: "+album)
  mb.set_useragent('Zarvox Automated DJ','Pre-Alpha',"KUPS' Webmaster (Jon Sims) at jsims@pugetsound.edu")
  mbAlbums = []
  mbAlbums=mb.search_releases(artist=artist,release=album,limit=10)['release-list']
  mbAlbums+=mb.search_releases(release=album,limit=10)['release-list']
  ranks = {}
  for x in mbAlbums:
    ranks[x['id']]=Levenshtein.ratio(album.lower(),x['title'].lower()) + Levenshtein.ratio(artist.lower(),x['artist-credit-phrase'].lower())
  mbAlbumId=max(ranks.items(),key=(lambda x:x[1]))[0]
  mbAlbum = [x for x in mbAlbums if x['id']==mbAlbumId][0]
  print("For the artist and album derived from the provided dir ("+artist+" and "+album+" respectively),\nthe following artist and album was matched on musicbrains:")
  print("Artist: "+mbAlbum['artist-credit-phrase'])
  print("Album: "+mbAlbum['title'])
  if Levenshtein.ratio(mbAlbum['title'],album) < 0.50:
    print("Warning: similarity of mbAlbum and album less than 50%; throwing mbAlbum and mbArtist away")
    mbAlbum=album
  whatAlbums = searchWhatAlbums(apihandle, [mbAlbum['title']])
  whatAlbum = max(
    [(x
      , Levenshtein.ratio(x['groupName'],mbAlbum['title'])+Levenshtein.ratio(x['artist'],mbAlbum['artist-credit-phrase'])) 
      for x in whatAlbums]
    , key=(lambda x:x[1]))[0]
  print("For the album and artist found on musicbrainz, the following torrent group was found on what:")
  print("Artist: "+whatAlbum['artist'])
  print("Album: "+whatAlbum['groupName'])
  whatGroup = apihandle.request("torrentgroup",id=whatAlbum['groupId'])
  if whatGroup['status']!='success': 
    print("Error: couldnt get group from what")
    exit(1)
  metadata = getTorrentMetadata(whatGroup['response'], mbAlbum['artist-credit-phrase'])
  if metadata == {}:
    print("Error: couldn't generate metadata from given info")
    exit(1)
  metadata['path_to_album'] = path_to_album
  print("Successfully generated metadata")
  fileAssoc = []
  for f in os.listdir(path_to_album):
    if f[(-1*len(extension)):]==extension:  
      temp = {}
      temp['size'] = int(subprocess.call('du -s \''+path_to_album+f+'\'| tr "\t" " " | cut -d\  -f1', shell=True))
      temp['name'] = f.replace('_',' ').strip(' -').split(artistSubstring)[-1]
      fileAssoc.append(temp)
  print("Downloaded data for "+' & '.join(metadata['artist']) + " - "+metadata['album'])
  data = {}
  data['metadata'] = metadata
  data['fileAssoc'] = fileAssoc
  with io.open(metadata['path_to_album']+"/.metadata.json",'w',encoding='utf8') as metadataFile:
    json.dump(data,metadataFile, ensure_ascii=False)
  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  

if  __name__ == '__main__':
  main()
