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
from statistics import mean

# escapeChars = re.compile()

def myEscape(s, bash=True):
  # for c in ["'",'"']+(['#'] if bash else []):
  #   s = s.replace(c,'\\'+c)
  return s.replace("'","'\\''")

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

def getDuration(path_to_song):
  try:
    durations = str(subprocess.check_output("exiftool -Duration '"+path_to_song+"'", shell=True)).split()[2].split(':')
    duration = reduce(lambda x,y:x+y,[int(''.join([c for c in durations[x] if str.isdigit(c)]))*pow(60,2-x) for x in range(len(durations))]) 
  except Exception as e:
    print("Error: cannot get duration properly:",file=sys.stderr)
    print(e,file=sys.stderr)
    exit(1)
  return duration


def main():
  global apihandle
  credentials = getCreds()
  db = startup_tests(sys.argv,credentials)
  #get all subgenres
  conf = getConfig()
  path_to_album = conf['albums_folder']+'/'+sys.argv[1].strip('/')+'/'
  if not os.path.isdir(path_to_album):
    print("Error: path "+path_to_album+" doesnt lead to a directory")
    exit(1)
  print(path_to_album, sys.argv[1])
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
      artists+=[x.strip() for x in subprocess.check_output("exiftool -Artist '"+myEscape(path_to_album+f)+"' | cut -d: -f2-10",shell=True).decode('utf8').strip().split('\n')]
      albums+=[x.strip() for x in subprocess.check_output("exiftool -Album -Product '"+myEscape(path_to_album+f)+"' | cut -d: -f2-10",shell=True).decode('utf8').strip().split('\n')]
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
  artist = artist.strip('!:;\\')
  print("For the provided dir "+path_to_album+", the following artist and album was found:")
  print("Artist: "+artist)
  print("Album: "+album)
  whatAlbum = getAlbumArtistNames(album,artist,apihandle)
  whatGroup = apihandle.request("torrentgroup",id=whatAlbum['groupId'])
  if whatGroup is None or whatGroup['status']!='success': 
    print("Error: couldnt get group from what")
    exit(1)
  metadata = getTorrentMetadata(whatGroup['response'], whatAlbum['artist-credit-phrase'])
  if metadata == {}:
    print("Error: couldn't generate metadata from given info")
    exit(1)
  metadata['path_to_album'] = path_to_album
  print("Successfully generated metadata")
  fileAssoc = []
  songs = getSongs(whatAlbum)
  if len(songs) < 1:
    print("Error with songlist")
    exit(1)
  for i in range(len(songs)):
    songs[i] = (songs[i][0],songs[i][1],str(i))
  fileList = [f.strip('/') for f in os.listdir(path_to_album) if f[(-1*len(extension)):]==extension]
  if len(fileList) < 1:
    print("Error with music folder")
    exit(1)
  for f in sorted(fileList ,key=lambda x: mean([Levenshtein.ratio(x.lower(),y.lower()) for y in fileList if y!=x])):
    temp = { 'path': f }
    temp['duration'] = getDuration(myEscape(path_to_album+f))
    temp['size'] = int(subprocess.call('du -s \''+myEscape(path_to_album+f)+'\'| tr "\t" " " | cut -d\  -f1', shell=True))
    temp['fname'] = f
    temp['title'] = str(subprocess.check_output("exiftool -Title '"+myEscape(path_to_album+f)+"' | cut -d: -f2-10",shell=True).decode('utf8').strip())
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
    print("Closest track to "+temp['title']+" is "+temp['track'])
    fileAssoc.append(temp)
    songs.remove(closestTrack)
  print("Downloaded data for "+(' & '.join(metadata['artists']))+ " - "+metadata['album'])
  data = {}
  data['metadata'] = metadata
  data['fileAssoc'] = fileAssoc
  with io.open(metadata['path_to_album']+"/.metadata.json",'w',encoding='utf8') as metadataFile:
    json.dump(data,metadataFile, ensure_ascii=False)
  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  

if  __name__ == '__main__':
  main()
