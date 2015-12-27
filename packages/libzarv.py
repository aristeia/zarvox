import sys,os,re,datetime,subprocess, json, Levenshtein, codecs, musicbrainzngs as mb
from urllib.request import urlopen,Request
from urllib.parse import quote,urlencode
from functools import reduce
import socket
from html import unescape
from numpy import float128
from decimal import Decimal
from difflib import SequenceMatcher

socket.setdefaulttimeout(5)

cocksucker = re.compile('cock.{,12}suck')
number = re.compile('^[0-9]+$')

sites = {
  'whatcd':'www.what.cd',
  'lastfm':'ws.audioscrobbler.com',
  'spotify':'www.spotify.com',
  'lyrics':'lyrics.wikia.com',
  'pandora':'www.pandora.com',
  'music':'www.musicbrainz.com',
  'spinitron':'www.spinitron.com'
}

queries = {
  'lastfm':{
    'song': 'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key=@apikey&artist=@artist&track=@song&format=json',
    'song': 'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key=@apikey&mbid=@mbid&format=json',
    'songsearch': 'http://ws.audioscrobbler.com/2.0/?method=track.search&api_key=@apikey&artist=@artist&track=@song&format=json',
    'album': 'http://ws.audioscrobbler.com/2.0/?method=album.getInfo&api_key=@apikey&artist=@artist&album=@album&format=json',
    'albumtags': 'http://ws.audioscrobbler.com/2.0/?method=album.gettoptags&artist=@artist&album=@album&api_key=@apikey&format=json',
    'artist': 'http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&api_key=@apikey&artist=@artist&format=json',
    'artisttags': 'http://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&artist=@artist&api_key=@apikey&format=json',
    'artistsimilar': 'http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist=@artist&api_key=@apikey&format=json'
    },
  'spotify':{
    'song': "https://api.spotify.com/v1/albums/@albumid/tracks",
    'album': "https://api.spotify.com/v1/artists/@artistid/albums",
    'artist': "https://api.spotify.com/v1/search?q=@artist&limit=5&type=artist",
    'id': "https://api.spotify.com/v1/@type/@id",
    'token':"https://accounts.spotify.com/api/token"
    },
  'lyrics': {
    'song':"http://lyrics.wikia.com/api.php?action=query&prop=revisions&format=json&rvprop=content&titles=@artist:@song"
    },
  'spinitron': {
    'query':"@url"
    }
}

formats = ['MP3','FLAC','AC3','ACC','AAC','DTS']

encoding = ['V0', 'Lossless','24bit Lossless']

def getLongestSubstring(x,y):
  match = (SequenceMatcher(None, x,y)
    .find_longest_match(0, len(x), 0, len(y)))
  return x[match[0]:match[2]]

def compareTors(x,y):
  def getEncoding(z):
    def calcLosslessness(bitrate):
      return 0.0724867+ float128(Decimal(bitrate-220.0)**Decimal(0.3940886699507389))
    if len(z)>1 and z[0:2] in encoding:
      return encoding.index(z[0:2])
    else:
      if z[0] == 'V':
        return int(z[1])+2
      else:
        if number.match(z):
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
    return x if ex<ey else y
  return x if x['seeders']>y['seeders'] else y


def getTorrentMetadata(albumGroup, albumArtistCredit = None):
  def checkArtistTypes(types):
    whatArtists = [unescape(x['name']) for x in albumGroup['group']['musicInfo'][types[0]]]
    types.pop(0)
    if len(whatArtists) == 1:
      return whatArtists
    elif len(whatArtists)>1:
      return whatArtists+[unescape(x['name']) for y in types for x in albumGroup['group']['musicInfo'][y]]
    return checkArtistTypes(types) if len(types)>0 else []
  #determine trueartists using musicbrainz
  whatArtists = checkArtistTypes(['artists','composers','conductor','dj'])
  if len(whatArtists) == 1:
    artists = whatArtists
  else:
    if len(whatArtists)==0:
      whatArtists+=[unescape(y['name']) for x in albumGroup['group']['musicInfo'] if x not in ['artists','composers','dj'] for y in albumGroup['group']['musicInfo'][x]]
    if albumArtistCredit is None:
      mb.set_useragent('Zarvox Automated DJ','Pre-Alpha',"KUPS' Webmaster (Jon Sims) at jsims@pugetsound.edu")
      albums = []
      for x in whatArtists:
        albums+=mb.search_releases(artistname=x,release=albumGroup['group']['name'],limit=3)['release-list']
      ranks = {}
      for x in albums:
        ranks[x['id']]=Levenshtein.ratio(albumGroup['group']['name'].lower(),x['title'].lower())
      albumRankMax=max(ranks.values())
      albumArtistCredit = ' '.join([ z['artist-credit-phrase'].lower() for z in albums if ranks[z['id']]>=(albumRankMax*0.95)])
    artists = [ x for x in whatArtists 
      if x.lower() in albumArtistCredit 
      and (x.lower()== albumArtistCredit 
      or any([ y.lower() in albumArtistCredit for y in [' '+x,x+' ']]))] #split by what artists
    if len(artists)==0:  
      return {}
  torrent = reduce(lambda x,y: compareTors(x,y),albumGroup["torrents"])
  print("Original artists are: "+', '.join(whatArtists))
  print("Final artists are: "+', '.join(artists))
  metadata = {
    'whatid' : torrent['id'],
    'album':unescape(albumGroup['group']['name']),
    'path_to_album':unescape(torrent["filePath"]),
    'artists':sorted(artists),
    #Songs need to be gotten by their levienshtein ratio to filenames and closeness of duration
    'format':torrent['format'].lower()
  }
  return metadata

def getAlbumArtistNames(album,artist, apihandle, song=None):
  '''
  Given a supposed album and artist, determine the real ones
  '''
  def searchWhatAlbums(args):
    if len(args)==0:
      return []
    whatResponse = apihandle.request(action='browse',searchstr=args[0])
    if whatResponse['status']=='success':
      args.pop(0)
      return searchWhatAlbums(args)+[x for x in whatResponse['response']['results'] if 'artist' in x and 'groupName' in x]
    return []
  mb.set_useragent('Zarvox Automated DJ','Pre-Alpha',"KUPS' Webmaster (Jon Sims) at jsims@pugetsound.edu")
  mbArtists = mb.search_artists(query=artist,limit=10)['artist-list']
  if song is not None:
    includes = ['recordings']
    artists = set(re.split('&|and',artist)+[artist])
    for ar in artists:
      mbAlbums = mb.search_releases(artist=ar,release=album,limit=10)['release-list']
      lastfmres = [x['mbid'] for x in lookup('lastfm','songsearch',{'artist':ar, 'song':song})['results']['trackmatches']['track'] if 'mbid' in x and len(x['mbid'])>0]
      if len(lastfmres)>0:
        for lastfmRecId in set(lastfmres[:min(5,len(lastfmres))]):
          lastfmAlbum = mb.get_recording_by_id(id=lastfmRecId,includes=['releases','artist-credits'])
          for alb in lastfmAlbum['recording'].pop('release-list'):
            alb['medium-list'] = [{}]
            alb['medium-list'][0]['track-list'] = []
            alb['medium-list'][0]['track-list'].append(lastfmAlbum)
            alb['artist-credit-phrase'] = lastfmAlbum['recording']['artist-credit-phrase']
            mbAlbums.append(alb)
  else:
    includes = []
    mbAlbums = mb.search_releases(artist=artist,release=album,limit=15)['release-list']
    for mbArtist in mbArtists:
      if Levenshtein.ratio(artist,mbArtist['name']) > 0.75:
        mbAlbums+=[ dict(list(x.items())+[('artist-credit-phrase',mbArtist['name'])]) for x in mb.browse_releases(artist=mbArtist['id'],includes=includes,limit=10)['release-list']]
  if len(album)<4 and 's' in album.lower() and 't' in album.lower():
    mbAlbums = mb.search_releases(artist=artist,release=artist,limit=10)['release-list']
    album = artist  
  ranks = {}
  for x in mbAlbums:
    ranks[x['id']] = Levenshtein.ratio(album,x['title'])
    if song is not None:
      x['song'] = {}
      x['song']['name'], x['song']['duration'] = max(
        [(y['recording']['title'],
          int(float(
            y['recording']['length'] if 'length' in y['recording'] 
            else (y['track_or_recording_length'] if 'track_or_recording_length' in x 
            else y['length'] if 'length' in x else 0)
          )/1000.))
        for tracklist in x['medium-list']
        for y in tracklist['track-list']] 
        if 'medium-list' in x and len(x['medium-list'])>0 and all('track-list' in z and len(z['track-list'])>0 for z in x['medium-list'])
        else getSongs(
          {"artist":x['artist-credit-phrase'], 
          "groupName":x['title']}), 
        key=lambda y: Levenshtein.ratio(y[0],song))
      if ranks[x['id']] < Levenshtein.ratio(x['song']['name'],song):
        ranks[x['id']] /= 6
        ranks[x['id']] +=  Levenshtein.ratio(x['song']['name'],song)*5/6
      else:
        ranks[x['id']] /= 3
        ranks[x['id']] +=  Levenshtein.ratio(x['song']['name'],song)*2/3
    ranks[x['id']] += Levenshtein.ratio(artist,x['artist-credit-phrase'])*5/6
  mbAlbumId, mbAlbumRank=max(ranks.items(),key=(lambda x:x[1]))
  mbAlbum = [x for x in mbAlbums if x['id']==mbAlbumId][0]
  print("For the artist and album derived from the provided dir ("+artist+" and "+album+" respectively),\nthe following artist and album was matched on musicbrains:")
  print("Artist: "+mbAlbum['artist-credit-phrase'])
  print("Album: "+mbAlbum['title'])
  if mbAlbumRank < 1:
    print("Warning: similarity of mbAlbum and album less than 50%; throwing mbAlbum and mbArtist away")
    mbAlbum={'title': album, 'artist-credit-phrase': artist, 'song': None}
  whatAlbums = searchWhatAlbums([mbAlbum['title']+' '+mbAlbum['artist-credit-phrase'],mbAlbum['title'],mbAlbum['artist-credit-phrase'], artist+' '+album])
  if len(whatAlbums) == 0:
    whatAlbums = searchWhatAlbums([artist,album])
    if len(whatAlbums) == 0:
      return None
  whatAlbums = sorted(whatAlbums, key=(lambda x:
      Levenshtein.ratio(x['groupName'],mbAlbum['title'])
      +0.5*Levenshtein.ratio(x['groupName'],album)
      +Levenshtein.ratio(x['artist'],mbAlbum['artist-credit-phrase'])
      +0.5*Levenshtein.ratio(x['artist'],artist)),
    reverse=True)#[:min(10,len(whatAlbums))]
  #if song is None:
  whatAlbum = whatAlbums[0]
  whatAlbum['song'] = mbAlbum['song']
  # else:
  #   for wAlb in whatAlbums:
  #     wAlb['song'] = {}
  #     wAlb['song']['name'], wAlb['song']['duration'] = max(
  #       getSongs(wAlb), 
  #       key=lambda x: Levenshtein.ratio(x[0],song))
  #     print(wAlb)
  #   whatAlbum = max(whatAlbums, key=(lambda x:
  #     Levenshtein.ratio(x['groupName'],mbAlbum['title'])
  #     +Levenshtein.ratio(x['groupName'],album)
  #     +Levenshtein.ratio(x['artist'],mbAlbum['artist-credit-phrase'])
  #     +Levenshtein.ratio(x['artist'],artist)
  #     +2.5*Levenshtein.ratio(x['song']['name'],song)))
  print("For the album and artist found on musicbrainz, the following torrent group was found on what:")
  print("Artist: "+whatAlbum['artist'])
  print("Album: "+whatAlbum['groupName'])
  return whatAlbum

def getSongs(whatGroup):
  mb.set_useragent('Zarvox Automated DJ','Pre-Alpha','kups webmaster')
  mbAlbum = mb.search_releases(
    artistname=whatGroup['artist'],
    release=whatGroup['groupName'], 
    limit=1)['release-list']
  return [
    (x['recording']['title'],
      int(float(
        x['recording']['length'] if 'length' in x['recording'] 
        else (x['track_or_recording_length'] if 'track_or_recording_length' in x 
        else x['length'] if 'length' in x else 0)
      )/1000.))
    for tracklist in 
      mb.get_release_by_id(
        mbAlbum[0]['id'],
        includes=['recordings'])['release']['medium-list']
    for x in tracklist['track-list']]
          


def averageResults(l):
  zeros = reduce(lambda x,y:tuple([x[i]+y[i] for i in range(len(x))]),[tuple([0 if y>0 else 1 for y in x]) for x in l])
  vals = reduce(lambda x,y:tuple([x[i]+y[i] for i in range(len(x))]),l)
  return [(float128(vals[x])/(len(l)-zeros[x])) if (len(l)-zeros[x])>0 else 0 for x in range(len(vals))]
    
def correctGenreNames(genres,db_genres):
  # for db_genre in db_genres:
  #   if db_genre['select'][1] not in genres:
  #     old_genre = reduce((lambda x,y: x if x[0] == levi_misc(x[0],y[0],db_genre['select'][1]) else y), genres.items())
  #     genres[db_genre['select'][1]] = old_genre[1]
  #     genres.pop(old_genre[0])
  #     print("Corrected "+old_genre[0]+" with "+db_genre['select'][1])
  return genres

def getFileContents(type):
  d = dict()
  with open("config/"+type) as f:
    for line in iter(f):
      if len(line)>2:
        d[line.split('=')[0].strip()] = line.split('=')[1].strip()
  return d

def getCreds():
  return getFileContents('credentials')

lastfm_apikey = getCreds()['lastfm_apikey']


def countToJSON(listOfTags, tagType = 'count'):
  return dict(map(lambda x: (x["name"],x[tagType]),listOfTags))


def massrep(args,query):
  if len(args)==0:
    return query
  return massrep(args[1:],query.replace('@'+args[0][0],args[0][1]))

def lookup(site, medium, args={}, data=None,headers=None):
  items = list(args.items())
  if site == 'lastfm':
    args['apikey'] = lastfm_apikey
    items = [(x,quote(y.replace(' ','+'),'+')) for (x,y) in items]
  elif site=='lyrics':
    items = [(x,quote(y.replace(' ','_'),'_')) for x,y in items]
  elif site!='spinitron':
    items = [(x,quote(y,'')) for x,y in items]
  query = massrep(items,queries[site][medium])
  if data is not None:
    data = codecs.encode(urlencode(data),'utf-8')
  try:
    if headers:
      with urlopen(Request(query,data,headers)) as response:
        res = response.readall().decode('utf-8')
    else:
      with urlopen(Request(query,data)) as response:
        res = response.readall().decode('utf-8')
  except Exception as e:
    print("Error: cannot reach site "+site+"\n")
    print(e)
  try:
    return json.loads(res)
  except Exception:
    print("Error: cannot convert response to json\n")
  return {}

def is_safe_harbor():
	return (datetime.datetime.now().time() < time(6) or datetime.datetime.now().time() > time(22))

def is_explicit(text):
  return ('fuck' in text or 'cunt' in text or cocksucker.match(text))

def levi_misc(x,y, thing):
  return y if Levenshtein.ratio(y.lower(),thing.lower())>Levenshtein.ratio(x.lower(),thing.lower()) else x

def calc_vbr(br):
  return round(10-10*pow(((br-60.0)/160.0),1.125),3)

def pingtest(args):
  print("Pinging "+sites[args[0]])
  try:
    print(subprocess.check_output('ping -c 3 '+sites[args[0]], shell=True))
  except Exception:
    print("Error: cannot ping "+sites[args[0]]+"\n")
    exit(1)
  if len(args)>1:
    pingtest(args[1:])

def concat3D(list1,list2):
  if len(list1)==len(list2):
    return [ list1[x]+list2[x] for x in xrange(list1)]
  print("Error: cannot add two lists who differ in length")
  exit(1)

def getConfig():
  return getFileContents('config')


#Given the percent of popularity in a supergenre having a subgenre,
#return the frequency of downloading that album as a dict
#in which key=time, val=number from 0-10 of top 10
def downloadFrequency(percent):
  averageDownloads = math.log(10.0*(percent+0.05),1.3)
  if averageDownloads<1:
    averageDownloads=1
  elif averageDownloads>10:
    averageDownloads=10
  #schedule is 24h clock
  return {
    0:math.round(averageDownloads/3.0),
    1:math.round(averageDownloads/3.0),
    2:math.round(averageDownloads/3.0),
    3:math.round(averageDownloads/3.0),
    4:math.round(averageDownloads/3.0),
    5:math.round(1.25*averageDownloads/3.0),#start
    6:math.round(1.875*averageDownloads/3.0),#start
    7:math.round(2.5*averageDownloads),#peak
    8:math.round(1.875*averageDownloads/3.0),#slow
    9:math.round(1.25*averageDownloads/3.0),
    10:math.round(averageDownloads/3.0),
    11:math.round(averageDownloads/3.0),
    12:math.round(averageDownloads/3.0),
    13:math.round(averageDownloads/3.0),
    14:math.round(averageDownloads/3.0),
    15:math.round(averageDownloads/3.0),
    16:math.round(1.5*averageDownloads/3.0),
    17:math.round(2.0*averageDownloads/3.0),#start
    18:math.round(2.5*averageDownloads/3.0),#START
    19:math.round(averageDownloads),#PEAK
    20:math.round(averageDownloads),#PEAK
    21:math.round(2.5*averageDownloads/3.0),#PEAK
    22:math.round(2.0*averageDownloads/3.0),#SLOW
    23:math.round(1.5*averageDownloads/3.0)
  }

def whatquote(text):
  return (text.replace('+','%2B')
    .replace('&','%26')
    .replace(',','%2C')
    .replace('=','%3D')
    .replace('+','%2B')
    .replace('@','%40')
    #.replace('#','%23')
    #.replace('$','%24')
    #.replace('/','%2F')
    .replace(';','%3B')
    .replace(':','%3A'))
    #.replace(' ','+'))  
  #quote(text,' $\'!')

#def genre() :
#	now = datetime.datetime.now().time()
	## etc..
