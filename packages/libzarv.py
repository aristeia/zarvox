import sys,os,re,traceback,datetime,subprocess, yaml, json, time, socket, Levenshtein, codecs, musicbrainzngs as mb,requests
from urllib.parse import quote,urlencode
from copy import deepcopy
from statistics import mean
from math import sqrt,log
from functools import reduce
from html import unescape
from numpy import float128, isnan, isinf
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

request_times = {
  'lastfm':0,
  'spotify':0,
  'lyrics':0,
  'pandora':0,
  'music':0,
  'spinitron':0
}
request_limits = {
  'lastfm':1,
  'spotify':0.125,
  'lyrics':0,
  'pandora':0,
  'music':1,
  'spinitron':1/2
}

queries = {
  'lastfm':{
    'song': 'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key=@apikey&artist=@artist&track=@song&format=json',
    #'song': 'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key=@apikey&mbid=@mbid&format=json',
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

headers = {
    'Content-type': 'application/x-www-form-urlencoded',
    'Accept-Charset': 'utf-8',
    'User-Agent': 'Zarvox_Automated_DJ/Alpha ('+(';'.join(os.uname()))+'; bot\'s contact is KUPS\' webmaster (Jon Sims) at communications@kups.net)'
    }

session = requests.Session()
session.mount('https://',requests.adapters.HTTPAdapter(max_retries=3))

formats = ['MP3','FLAC','AC3','ACC','AAC','DTS']

encoding = ['V0', 'Lossless','24bit Lossless']

def handleError(e, eStr="Error"):
  for output in [sys.stderr, sys.stdout]:
    print(eStr,file=output)
  print(e, file=sys.stderr)
  for frame in traceback.extract_tb(sys.exc_info()[2]):
      fname,lineno,fn,text = frame
      print("  Occurred in %s on line %d" % (fname, lineno), file=sys.stderr)
  print('\n', file=sys.stderr)

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

#When we have validated data, get the whatcd dict associated with it
#Consider skipping this using a config parameter  
def getTorrentMetadata(albumGroup, albumArtistCredit = None):
  def checkArtistTypes(types):
    whatArtists = [unescape(x['name']) for x in albumGroup['group']['musicInfo'][types[0]]]
    types.pop(0)
    if len(whatArtists) == 1:
      return whatArtists
    elif len(whatArtists)>1:
      return whatArtists+[unescape(x['name']) for y in types for x in albumGroup['group']['musicInfo'][y]]
    return checkArtistTypes(types) if len(types)>0 else []
  #is this not music?
  if albumGroup['group']['categoryName'] != 'Music':
    print("Group "+albumGroup['group']['name']+" is not music")
    return {}
  #determine trueartists using musicbrainz
  whatArtists = checkArtistTypes(['artists','composers','conductor','dj'])
  if len(whatArtists) == 1:
    artists = whatArtists
  else:
    if len(whatArtists)==0:
      whatArtists = [unescape(y['name']) for x in albumGroup['group']['musicInfo'] if x not in ['artists','composers','dj'] for y in albumGroup['group']['musicInfo'][x]]
    if albumArtistCredit is None:
      mb.set_useragent('Zarvox_Automated_DJ','Alpha',"KUPS' Webmaster (Jon Sims) at communications@kups.net")
      mb.set_rate_limit()
      albums = []
      for x in whatArtists:
        albums+=mb.search_releases(artistname=mbquote(x),release=mbquote(albumGroup['group']['name']),limit=3)['release-list']
      ranks = {}
      for x in albums:
        ranks[x['id']]=Levenshtein.ratio(albumGroup['group']['name'].lower(),x['title'].lower())
      albumRankMax=max(ranks.values())
      albumArtistCredit = ' '.join([ z['artist-credit-phrase'] for z in albums if ranks[z['id']]>=(albumRankMax*0.9)])
    artists = [ unescape(x) for x in whatArtists 
      if unescape(x.lower()) in albumArtistCredit.lower()] #split by what artists
    if len(artists)==0:  
      raise RuntimeError("Len of artists is zero!!")
  torrent = reduce(lambda x,y: compareTors(x,y),albumGroup["torrents"])
  print("Original artists are: "+', '.join(whatArtists))
  print("Final artists are: "+', '.join(artists))
  metadata = {
    'whatid' : torrent['id'],
    'album':unescape(albumGroup['group']['name']),
    'path_to_album':'',
    'artists':sorted(artists),
    #Songs need to be gotten by their levienshtein ratio to filenames and closeness of duration
    'format':torrent['format'].lower()#fix this like path
  }
  return metadata

def mbEscape(obj):
  for char in ['?','!','(',')']:
    obj = obj.replace(char,"\\"+char)
  obj = obj.replace('/',' & ')
  obj = obj.replace('\\',' ')
  return obj

#When we have user-entered data that could be wrong, use this to make validated data
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
  mb.set_useragent('Zarvox_Automated_DJ','Alpha',"KUPS' Webmaster (Jon Sims) at communications@kups.net")
  mb.set_rate_limit()
  mbAlbums = []
  parens = re.compile('[\(\[].*[\)\]]')
  if song is not None:
    includes = ['recordings']
    artists = set(re.split(' &|and|ft\.?|featuring|feat\.? ',artist))
    if len(artists) > 1:
      artists.add(artist)
    for ar in artists:
      lastfmres = [x['mbid'] for x in lookup('lastfm','songsearch',{'artist':ar, 'song':song})['results']['trackmatches']['track'] if 'mbid' in x and len(x['mbid'])>0]
      if len(lastfmres)>0:
        for lastfmRecId in set(lastfmres[:min(5,len(lastfmres))]):
          try:
            lastfmAlbum = mb.get_recording_by_id(id=lastfmRecId,includes=['releases','artist-credits'])
            for alb in lastfmAlbum['recording'].pop('release-list'):
              alb['medium-list'] = [{}]
              alb['medium-list'][0]['track-list'] = []
              alb['medium-list'][0]['track-list'].append(lastfmAlbum)
              alb['artist-credit-phrase'] = lastfmAlbum['recording']['artist-credit-phrase']
              mbAlbums.append(alb)
          except Exception as e:
            print(e)
        mbAlbums += mb.search_releases(artist=mbquote(ar),query=mbquote(album),limit=max(6-len(mbAlbums),3))['release-list']
      else:
        temp = mb.search_releases(artist=mbquote(ar),query=mbquote(album),limit=20)['release-list']
        if len(temp)>10:
          mbAlbums+=sorted(temp, key=(lambda x:
            Levenshtein.ratio(album.lower(),x['title'].lower())
            +Levenshtein.ratio(artist.lower(),x['artist-credit-phrase'].lower())
            +0.5*Levenshtein.ratio(ar.lower(),x['artist-credit-phrase'].lower())),
          reverse=True)[:10]
  else:
    includes = []
    mbArtists = mb.search_artists(query=mbquote(artist),limit=5)['artist-list']
    mbAlbums += mb.search_releases(artist=mbquote(artist),query=mbquote(album),limit=10)['release-list']
    for mbArtist in mbArtists:
      if Levenshtein.ratio(artist.lower(),mbArtist['name'].lower()) > 0.75:
        mbAlbums+=[ dict(list(x.items())+[('artist-credit-phrase',mbArtist['name'])]) for x in mb.browse_releases(artist=mbArtist['id'],includes=includes,limit=6)['release-list']]
  if (len(album)<7 and ('/' in album or ' & ' in album) and 's' in album.lower() and 't' in album.lower()) or ('self' in album.lower() and 'titled' in album.lower()):
    mbAlbums += mb.search_releases(artist=mbquote(artist),query=mbquote(artist),limit=10)['release-list']
  temp = []
  for x in mbAlbums[:]:
    if x["id"] in temp and not ('medium-list' in x and len(x['medium-list'])>0 and all('track-list' in z and len(z['track-list'])>0 for z in x['medium-list'])):
      mbAlbums.remove(x)
    else:
      temp.append(x['id'])
  print("Done searching musicbrainz for album suggestions, have "+str(len(mbAlbums))+" to rank")
  
  ranks = {}
  for x in mbAlbums:
    ranks[x['id']] = Levenshtein.ratio(album.lower(),x['title'].lower())
    if song is not None:
      x['song'] = {}
      temp = ([(y['recording']['title'],
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
          "groupName":x['title']}))
      x['song']['name'], x['song']['duration'] = (max(temp, 
        key=lambda y: Levenshtein.ratio(y[0].lower(),song.lower())) if len(temp)>0 else ("",-1))
      if ranks[x['id']] < Levenshtein.ratio(x['song']['name'].lower(),song.lower()):
        ranks[x['id']] /= 6
        ranks[x['id']] +=  (Levenshtein.ratio(x['song']['name'].lower(),song.lower())
          + Levenshtein.ratio(parens.sub('',x['song']['name'].lower()),parens.sub('',song.lower())) )*5/12
      else:
        ranks[x['id']] /= 3
        ranks[x['id']] +=  (Levenshtein.ratio(x['song']['name'].lower(),song.lower())
          + Levenshtein.ratio(parens.sub('',x['song']['name'].lower()),parens.sub('',song.lower())) )/3
    ranks[x['id']] += Levenshtein.ratio(artist.lower(),x['artist-credit-phrase'].lower())*7/6
  if len(ranks) == 0:
    return None
  mbAlbumId, mbAlbumRank = max(ranks.items(),key=(lambda x:x[1]))
  mbAlbum = [x for x in mbAlbums if x['id']==mbAlbumId][0]
  print("For the artist and album derived from the provided dir ("+artist+" and "+album+" respectively),\nthe following artist and album was matched on musicbrains:")
  print("Artist: "+mbAlbum['artist-credit-phrase'])
  print("Album: "+mbAlbum['title'])
  whatAlbums = searchWhatAlbums([mbAlbum['title']+' '+mbAlbum['artist-credit-phrase'], artist+' '+album])
  if len(whatAlbums) == 0:
    whatAlbums = searchWhatAlbums([artist,album,mbAlbum['title'],mbAlbum['artist-credit-phrase']])
    if len(whatAlbums) == 0:
      return None
  whatAlbums = sorted(whatAlbums, key=(lambda x:
      Levenshtein.ratio(x['groupName'],mbAlbum['title'])
      +Levenshtein.ratio(x['groupName'].lower(),album.lower())*3/8
      +Levenshtein.ratio(x['artist'],mbAlbum['artist-credit-phrase'])
      +Levenshtein.ratio(x['artist'].lower(),artist.lower())*5/8),
    reverse=True)#[:min(10,len(whatAlbums))]
  whatAlbum = whatAlbums[0]
  whatAlbum['artist-credit-phrase'] = mbAlbum['artist-credit-phrase']
  if song is not None:
    whatAlbum['song'] = mbAlbum['song']
  print("For the album and artist found on musicbrainz, the following torrent group was found on what:")
  print("Artist: "+whatAlbum['artist'])
  print("Album: "+whatAlbum['groupName'])
  return whatAlbum

def getSongs(whatGroup):
  mb.set_useragent('Zarvox_Automated_DJ','Alpha','kups webmaster')
  mb.set_rate_limit()
  mbAlbum = mb.search_releases(
    artistname=mbquote(whatGroup['artist']),
   release= mbquote(whatGroup['groupName']), 
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
     
def getArtist(artist,apihandle):
  mb.set_useragent('Zarvox_Automated_DJ','Alpha',"KUPS' Webmaster (Jon Sims) at communications@kups.net")
  mb.set_rate_limit()
  mbArtists = [ (x['name'],x['score'])
    for x in mb.search_artists(query=mbquote(artist),limit=5)['artist-list']
    if 'name' in x and 'score' in x]
  mbDict = { }
  for mbAr in mbArtists:
    if mbAr[0] not in mbDict:
      vals = [x[1]**2 for x in mbArtists if x==mbAr[0]]
      mbDict[mbAr[0]] = [sqrt(mean(vals))/100]
  maxWhatcdScore = 0
  for mbAr,mbScores in mbDict.items():
    whatcd_artist = apihandle.request("artist", artistname=whatquote(mbAr))["response"]
    artist = unescape(whatcd_artist['name'])
    mbScores.append(log(mean(3*whatcd_artist["statistics"]["numSeeders"],2*whatcd_artist["statistics"]["numSnatches"])))
    if mbScores[-1]>maxWhatcdScore:
      maxWhatcdScore = mbScores[-1]
    mbScores.append(2*Levenshtein.ratio(artist.lower(),mbAr.lower()))
  for mbScores in mbDict.values():
    mbScores[1] /= maxWhatcdScore
  return max([(sum(scores),name)
    for name, scores in mbDict.items()]
    +[(1.5,artist)])[1]




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

def getFileContents(t):
  d = dict()
  if not os.path.isfile("config/"+t):
    t = t+"_default"
    if not os.path.isfile("config/"+t):
      return d
  with open("config/"+t) as f:
    lastKey = ''
    for line in iter(f):
      if len(line)>2:
        if '=' in line:
          temp = line.split('=')
          lastKey = temp[0].strip()
          d[lastKey] = temp[1].strip()
        else:
          d[lastKey] += line.strip()
    for key in d.keys():
      d[key] = yaml.load(d[key])
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

def lookup(site, medium, args={}, data=None,hdrs={}):
  def getResponse(query):
    time_diff = request_limits[site]-time.clock()+request_times[site]
    if time_diff > 0:
      time.sleep(time_diff)
    try:
      if data is not None:
        return session.post(url=query,data=data,timeout=(3.05,9.05))
      else:
        return session.get(url=query,timeout=(3.05,9.05))
    except Exception as e:
      print("Error: cannot reach site "+site+"\n")
      print(e)
      raise e

  session.headers = deepcopy(headers)
  session.headers.update(hdrs)
  items = list(args.items())
  if site == 'lastfm':
    items.append(('apikey',lastfm_apikey))
    items = [(x,quote(y.replace(' ','+'),'+',encoding='utf-8')) for (x,y) in items]
  elif site=='lyrics':
    items = [(x,quote(y.replace(' ','_'),'_',encoding='utf-8')) for x,y in items]
  elif site!='spinitron':
    items = [(x,quote(y,'',encoding='utf-8')) for x,y in items]
  try:
    response = getResponse(massrep(items,queries[site][medium]))
    request_times[site] = time.clock()
    while response.status_code == 429:
      print("Warning: response code 429 Too Many Requests")
      if site == "spotify" or "Retry-After" in response.headers:
        print("Waiting "+str(response.headers['Retry-After'])+" seconds")
        time.sleep(response.headers['Retry-After'])
      else:
        print("Waiting default (5) seconds")
        time.sleep(5)
      response = getResponse(massrep(items,queries[site][medium]))
  except Exception as e:
    print("Error: cannot get response from site "+site)
    print(e,file=sys.stderr)
    return {}
  try:
    return response.json()
  except Exception as e:
    print("Error: cannot convert response to json")
    print(e,file=sys.stderr)
  return {}

def is_safe_harbor():
	return (datetime.datetime.now().time() < time(6) or datetime.datetime.now().time() > time(22))

def is_explicit(text):
  return ('fuck' in text or 'cunt' in text or cocksucker.match(text))

def levi_misc(x,y, thing):
  return y if Levenshtein.ratio(y.lower(),thing.lower())>Levenshtein.ratio(x.lower(),thing.lower()) else x

def calc_vbr(br):
  if br>=61:
    return round(10-10*pow(((br-60.0)/160.0),1.125),3)
  return 9.99

def pingtest(args):
  print("Pinging "+sites[args[0]])
  try:
    subprocess.check_output('ping -c 3 '+sites[args[0]], shell=True)
  except Exception:
    print("Error: cannot ping "+sites[args[0]]+"\n")
    exit(1)
  if len(args)>1:
    pingtest(args[1:])

def concat3D(list1,list2):
  if len(list1)==len(list2):
    return [ list1[x]+list2[x] for x in xrange(list1)]
  print("Error: cannot add two lists who differ in length")
  return []

def getConfig():
  return getFileContents('config')

def whatquote(text):
  return text.replace('+','%2B')

def mbquote(text):
  newText = text
  for badchar in '()[]^@/~=&"':
    newText = newText.replace(badchar, ' ')
  for badchar in '!':
    newText = newText.strip(badchar)
  return newText.strip()

def bashEscape(s):
  return s.replace("'","'\"'\"'")

def percentValidation(n):
  #too small/BAD
  if n is None or n<0 or isnan(n):
    return 0.0
  #too big
  if n>1 or isinf(n):
    return 1.0
  return n

def closeEnough(lst1,lst2, closeness=0.5):
  return (
    mean(
      list(
        map(lambda z: Levenshtein.ratio(*[zz.lower() for zz in z]),
          zip(lst1,lst2)))) >= closeness)

def getIllegalChars():
  _illegal_unichrs = [(0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F), 
    (0x7F, 0x84), (0x86, 0x9F), 
    (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF)] 
  if sys.maxunicode >= 0x10000:  # not narrow build 
    _illegal_unichrs.extend([(0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF), 
     (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF), 
     (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF), 
     (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF), 
     (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF), 
     (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF), 
     (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF), 
     (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)]) 

  _illegal_ranges = ["%s-%s" % (unichr(low), unichr(high)) 
    for (low, high) in _illegal_unichrs] 
  return re.compile(u'[%s]' % u''.join(_illegal_ranges)) 