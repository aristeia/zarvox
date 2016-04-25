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
sys.path.extend(os.listdir(os.getcwd()))
from postprocessor import getDuration
import whatapi
from libzarv import *
from numpy import float128
from html import unescape
from statistics import mean

# escapeChars = re.compile()

def startup_tests(args, credentials):
  if len(args) != 2:
    raise RuntimeError("Error: postprocessor received wrong number of args")
  db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_password']+'@localhost/'+credentials['db_name'])
  print("Zarvox database are online")
  pingtest(['whatcd'])    
  print("Pingtest complete; sites are online")
  return db

def main():
  global apihandle
  credentials = getCreds()
  db = startup_tests(sys.argv,credentials)
  #get all subgenres
  conf = getConfig()
  path_to_album = conf['albums_folder']+'/'+sys.argv[1].strip('/') + '/'
  if not os.path.isdir(path_to_album):
    raise RuntimeError("Error: path "+path_to_album+" doesnt lead to a directory")
  downloads = []
  credentials = getCreds()
  cookies = {'cookies':pickle.load(open('config/.cookies.dat', 'rb'))} if os.path.isfile('config/.cookies.dat') else {}
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], **cookies)
  extensions = [y for y in [x.split('.')[-1].lower() for x in os.listdir(path_to_album) if os.path.isfile(path_to_album+x)] if y in ['mp3','flac','acc','alac','wav','wma','ogg','m4a']]
  if len(extensions)>0:
    extension = max([(x,extensions.count(x)) for x in set(extensions)],key=(lambda x:x[1]))[0]
    print("File extension most common is "+extension)
  else:
    raise RuntimeError("Error: cannot get extension")
  artists = []
  albums = []
  for f in os.listdir(path_to_album):
    if f[(-1*len(extension)):]==extension:
      artists+=[x.strip() for x in subprocess.check_output("exiftool -Artist '"+bashEscape(path_to_album+f)+"' | cut -d: -f2-10",shell=True).decode('utf8').strip().split('\n') if len(x.strip()) > 1]
      albums+=[x.strip() for x in subprocess.check_output("exiftool -Album -Product '"+bashEscape(path_to_album+f)+"' | cut -d: -f2-10",shell=True).decode('utf8').strip().split('\n') if len(x.strip()) > 1]
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
    artist = max([(x,artists.count(x)) for x in set(artists)], key=(lambda x:x[1]))[0]
  album = mbEscape(album)
  artist = mbEscape(artist)
  print("For the provided dir "+path_to_album+", the following artist and album was found:")
  print("Artist: "+artist)
  print("Album: "+album)
  whatAlbum = getAlbumArtistNames(album,artist,apihandle)
  if whatAlbum is None or not closeEnough([artist,album],[whatAlbum['artist'],whatAlbum['groupName']]):
    raise RuntimeError("Error: artist and album arent close enough;skipping")
  whatGroup = apihandle.request("torrentgroup",id=whatAlbum['groupId'])
  if whatGroup is None or whatGroup['status']!='success': 
    raise RuntimeError("Error: couldnt get group from what")
  metadata = getTorrentMetadata(whatGroup['response'], whatAlbum['artist-credit-phrase'])
  if metadata == {}:
    raise RuntimeError("Error: couldn't generate metadata from given info")
  metadata['path_to_album'] = path_to_album[:-1]
  metadata['format'] = extension
  print("Successfully generated metadata")
  fileAssoc = []
  songs = getSongs(whatAlbum)
  if len(songs) < 1:
    raise RuntimeError("Error with songlist; length 0!")
  for i in range(len(songs)):
    songs[i] = (songs[i][0],songs[i][1],str(i))
  fileList = [f.strip('/') for f in os.listdir(path_to_album) if f[(-1*len(extension)):]==extension]
  if len(fileList) < 1:
    raise RuntimeError("Error with music folder; length 0!")
  for f in sorted(fileList ,key=lambda x: mean([Levenshtein.ratio(x.lower(),y.lower()) if y!=x else 0.5 for y in fileList])):
    if len(songs) > 0:
      temp = { 'path': f }
      temp['duration'] = getDuration(path_to_album+f)
      temp['size'] = int(subprocess.call('du -s \''+bashEscape(path_to_album+f)+'\'| tr "\t" " " | cut -d\  -f1', shell=True))
      temp['fname'] = f
      temp['title'] = str(subprocess.check_output("exiftool -Title '"+bashEscape(path_to_album+f)+"' | cut -d: -f2-10",shell=True).decode('utf8').strip())
      if len(temp['title'])>1:
        temp['title'] = f.replace('_',' ').strip(' -')
        if len(artistSubstring) > 0:
          temp['title'] = temp['title'].split(artistSubstring)[-1]
      else:
        temp['title'] = temp['fname']
      closestTrack = max(songs,
        key=(lambda x: 
          Levenshtein.ratio(' - '.join([x[2],artistSubstring,x[0]]).lower(),temp['fname'].lower())/2
          +Levenshtein.ratio(x[0].lower(),temp['title'].lower())
          +(1 - (abs(temp['duration']-x[1])/temp['duration']))))
      temp['track'] = closestTrack[0]
      print("Closest track to '"+f+"' is '"+temp['track']+"'")
      if not closeEnough([temp['title']],[temp['track']],closeness=(3.0)**(-1)):
        print("Closeness isn't close enough, so not keeping")   
      else:
        fileAssoc.append(temp)
        songs.remove(closestTrack)
  print("Downloaded data for "+(' & '.join(metadata['artists']))+ " - "+metadata['album'])
  if len(fileAssoc) == 0:
    print("No files to be saved, so not saving metadata")
  else:
    data = {}
    data['metadata'] = metadata
    data['fileAssoc'] = fileAssoc
    with io.open(metadata['path_to_album']+"/.metadata.json",'w',encoding='utf8') as metadataFile:
      json.dump(data,metadataFile, ensure_ascii=False)
  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  

if  __name__ == '__main__':
  main()
