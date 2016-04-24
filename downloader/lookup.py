import sys,pickle,re,time,pitchfork,os
sys.path.extend(os.listdir(os.getcwd()))
import whatapi
from statistics import mean
from libzarv import *
from musicClasses import *
from functools import reduce
from binascii import unhexlify
from base64 import encodebytes
from urllib import parse
from html import unescape
from scipy.stats import norm

genreRegex = re.compile('^\d*.?$')
genreReplace = re.compile('\W')
genreList = []
artistList = []
artistAlbums = None
albumKups = None
artistKups = None
songKups = None
artistCache = None
albumCache = None
songCache = None
gC = getConfig()
maxSimArtists = int(gC['maxSimArtists']) if 'maxSimArtists' in gC else 10
maxSimGenres = int(gC['maxSimGenres']) if 'maxSimGenres' in gC else 15



def populateCache(con):
  global genreList,artistList,artistAlbums,albumKups,artistKups,songKups,artistCache,albumCache,songCache
  genreList = [x[0] for lst in con.db.prepare(
    '''SELECT genre FROM genres''').chunks() for x in lst]
  artistList = [x[0] for lst in con.db.prepare(
    '''SELECT artist FROM artists''').chunks() for x in lst]
  artistAlbums = con.db.prepare(
    '''SELECT album FROM albums 
    LEFT OUTER JOIN artists_albums ON albums.album_id = artists_albums.album_id 
    LEFT OUTER JOIN artists ON artists_albums.artist_id = artists.artist_id 
    WHERE artists.artist = $1''')
  
  albumKups = con.db.prepare(
    '''SELECT albums.kups_playcount FROM albums 
    LEFT OUTER JOIN artists_albums ON albums.album_id = artists_albums.album_id 
    LEFT OUTER JOIN artists ON artists_albums.artist_id = artists.artist_id 
    WHERE artists.artist = $1 and albums.album = $2''')
  artistKups = con.db.prepare(
    '''SELECT kups_playcount FROM artists WHERE artist = $1''')
  songKups = con.db.prepare(
    '''SELECT songs.kups_playcount FROM songs 
    LEFT OUTER JOIN albums on albums.album_id = songs.album_id 
    where songs.song = $1 and albums.album = $2''')
  
  artistCache = con.db.prepare(
    '''SELECT * FROM artists WHERE artist = $1''')
  albumCache = con.db.prepare(
    '''SELECT albums.* FROM albums 
    LEFT OUTER JOIN artists_albums ON albums.album_id = artists_albums.album_id 
    LEFT OUTER JOIN artists ON artists_albums.artist_id = artists.artist_id 
    WHERE artists.artist = $1 AND albums.album = $2''')
  songCache = con.db.prepare(
    '''SELECT songs.* FROM songs 
    LEFT OUTER JOIN albums on albums.album_id = songs.album_id 
    LEFT OUTER JOIN artists_albums ON albums.album_id = artists_albums.album_id 
    LEFT OUTER JOIN artists ON artists_albums.artist_id = artists.artist_id 
    WHERE artists.artist = $1 AND albums.album = $2 AND songs.song = $3''')


def getSpotifyArtistToken(artistName,spotify_client_id,spotify_client_secret):
  try:
    spotify_arids = lookup('spotify','artist',{'artist':artistName})['artists']['items']
    spotify_token=lookup('spotify','token',{},{'grant_type':'client_credentials'},{'Authorization':b'Basic '+encodebytes(bytes(('%s:%s' % (spotify_client_id,spotify_client_secret)),encoding='utf-8')).replace(b'\n', b'')})['access_token']
    if len(spotify_arids) > 0:
      spotify_arid = reduce((lambda x,y:x if x['name'].lower()==levi_misc(x['name'].lower(),y['name'].lower(),artistName.lower()) else y), spotify_arids)['id']
      return spotify_arid,spotify_token
  except Exception as e:
    handleError(e,"Cannot get artistid on spotify for "+artistName)
  return None, None


#song is pseudo-songobj, having attr for name and duration
def songLookup(metadata,song,path,con=None):
  if con is not None:
    populateCache(con)
  credentials = getCreds()
  songCached = (reduce(
      lambda x,y: x if y is None else y,
      [x for artist in metadata['artists'] 
        for lst in songCache.chunks(artist,metadata['album'],song['name']) 
        for x in lst],
      None) if songCache is not None
    else None)
  if songCached is not None:
    print("Using cached song values")
    explicit = songCached[5]
    spotify_popularity = songCached[6]
    lastfm_listeners = songCached[7]
    lastfm_playcount = songCached[8]
    kups_playcount = songCached[12]
  else:
    explicit = False
    spotify_popularity = 0
    lastfm_listeners = 0
    lastfm_playcount = 0
    kups_playcount = 0

  if spotify_popularity == 0:
    tempArtistIndex = 0
    spotify = {'explicit':False}
    while spotify_popularity==0 and tempArtistIndex<len(metadata['artists']):
      try:
        spotify_arid,spotify_token = getSpotifyArtistToken(metadata['artists'][tempArtistIndex],credentials['spotify_client_id'],credentials['spotify_client_secret'])
        if spotify_arid is not None:
          spotify_alid = reduce((lambda x,y:x if x['name'].lower() == levi_misc(x['name'].lower(),y['name'].lower(),metadata['album'].lower()) else y), lookup('spotify','album',{'artistid':spotify_arid})['items'])['id']
          spotify_id = reduce((lambda x,y:x if x['name'].lower() == levi_misc(x['name'].lower(),y['name'].lower(),song['name'].lower()) else y), lookup('spotify','song',{'albumid':spotify_alid})['items'])['id']
          spotify = lookup('spotify','id',{'id':spotify_id, 'type':'tracks'},None,{"Authorization": "Bearer "+spotify_token})
          spotify_popularity = int(lookup('spotify','id',{'id':spotify_id, 'type':'tracks'},None,{"Authorization": "Bearer "+spotify_token})['popularity'])
      except Exception as e:
        handleError(e,"Warning: cannot get song spotify data. Using 0s.")
        spotify_popularity=0
        spotify = {'explicit':False}
      tempArtistIndex+=1
    explicit = spotify['explicit']
    tempArtistIndex = 0
    while not spotify['explicit'] and tempArtistIndex<len(metadata['artists']):
      try:
        lyricsLookupRes = lookup('lyrics','song',{'artist':metadata['artists'][tempArtistIndex], 'song':song['name']})
        if 'query' in lyricsLookupRes:
          lyricsLookup = str(lyricsLookupRes['query']['pages'])
          if 'lyrics' in lyricsLookup:
            explicit = is_explicit(lyricsLookup.split('lyrics>')[1]) or spotify['explicit']
      except Exception as e:
        handleError(e,"Warning: cannot get song lyric data. Using 0s.")
        explicit = spotify['explicit']
      tempArtistIndex+=1

  if lastfm_listeners==0 or lastfm_playcount==0:
    tempArtistIndex = 0
    while lastfm_listeners==0 and lastfm_playcount==0 and tempArtistIndex<len(metadata['artists']):
      try:
        lastfm = lookup('lastfm','song',{'artist':metadata['artists'][tempArtistIndex], 'song':song['name']})['track'] 
        lastfm_listeners = lastfm['listeners'] if lastfm['listeners']!='' else 0
        lastfm_playcount = lastfm['playcount'] if lastfm['playcount']!='' else 0
      except Exception as e:
        handleError(e,"Warning: cannot get song lastfm data. Using 0s.")
        lastfm_listeners = 0
        lastfm_playcount = 0
      tempArtistIndex+=1

  if kups_playcount == 0:
    if songKups is not None:
      kups_playcount = sum([x[0] for lst in songKups.chunks(song['name'],metadata['album']) for x in lst])

  return Song(song['name'],path,song['duration'],explicit,spotify_popularity,lastfm_listeners,lastfm_playcount,kups_playcount)


def albumLookup(metadata, apihandle=None, con=None):
  #Get genres for album from lastfm, what.cd
  #Get popularities for album from spotify, lastfm, what.cd  
  login= apihandle is not None
  try:
    if con is not None:
      populateCache(con)
    credentials = getCreds()
    if login:
      cookies = pickle.load(open('config/.cookies.dat', 'rb'))
      apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
    whatcd_artists = [apihandle.request("artist", artistname=whatquote(x))["response"] for x in metadata['artists']]
    whatcd_albums = [{'tor':y,'group':x} for w in whatcd_artists for x in w["torrentgroup"] for y in x['torrent'] if y['id']==metadata['whatid']]
    if len(whatcd_albums)>0:
      whatcd_album = whatcd_albums[0]
      if not whatcd_album['tor']['freeTorrent']:
        whatcd_snatches = reduce(lambda x,y: {"snatched":(x["snatched"]+y["snatched"])},whatcd_album['group']['torrent'])["snatched"]
        whatcd_seeders = reduce(lambda x,y: {"seeders":(x["seeders"]+y["seeders"])},whatcd_album['group']['torrent'])["seeders"]
      else:
        whatcd_snatches = 0
        whatcd_seeders = 0
      whatcd_genres = dict(filter(lambda x:not genreRegex.match(x[0]), [(genreReplace.sub('.',x.strip('.').lower()),0.5) for x in whatcd_album['group']["tags"]]))
    else:
      whatcd_genres = {}
      whatcd_snatches = 0
      whatcd_seeders = 0
  except Exception:
    whatcd_genres = {}
    whatcd_snatches = 0
    whatcd_seeders = 0
  try:
    lastfm = max([y for y in [lookup('lastfm','album',{'artist':x, 'album':metadata['album']}) for x in metadata['artists']] if 'album' in y],
                key=lambda x: x['album']['playcount'])['album']
    try:
      lastfm_listeners = int(lastfm['listeners']) if lastfm['listeners']!='' else 0
      lastfm_playcount = int(lastfm['playcount']) if lastfm['playcount']!='' else 0
    except Exception:
      lastfm_listeners = 0
      lastfm_playcount = 0
    try:
      lastfm_genres = countToJSON(lookup('lastfm','albumtags',{'artist':lastfm['artist'], 'album':lastfm['name']})["toptags"]["tag"])
      for key in list(lastfm_genres.keys())[:]:
        realKey = genreReplace.sub('.',key.lower().strip('.'))
        if realKey in genreList:
          lastfm_genres[realKey] = lastfm_genres[key]
        if key != realKey:
          lastfm_genres.pop(key)
      if len(lastfm_genres) > 0:
        rvar = norm(*norm.fit(list(lastfm_genres.values())))
        lastfm_genres = dict(filter(lambda x:not genreRegex.match(x[0]), [(x,rvar.cdf(float(y))) for x,y in lastfm_genres.items()]))
    except Exception as e:
      print(e)
      lastfm_genres = {}
  except Exception as e:
    lastfm_listeners = 0
    lastfm_playcount = 0
    lastfm_genres = {}
    print(e)
  spotify_popularity = 0
  tempArtistIndex = 0
  while spotify_popularity==0 and tempArtistIndex<len(metadata['artists']):
    try:
      spotify_arid,spotify_token = getSpotifyArtistToken(metadata['artists'][tempArtistIndex],credentials['spotify_client_id'],credentials['spotify_client_secret'])
      spotify_id = reduce((lambda x,y:x if x['name'].lower() == levi_misc(x['name'].lower(),y['name'].lower(),metadata['album'].lower()) else y), lookup('spotify','album',{'artistid':spotify_arid})['items'])['id']
      spotify_popularity = int(lookup('spotify','id',{'id':spotify_id, 'type':'albums'},None,{"Authorization": "Bearer "+spotify_token})['popularity'])
    except Exception as e:
      print(e)
      spotify_popularity=0
    tempArtistIndex+=1
  genres = sorted(
    [(x,y) for x,y in whatcd_genres.items() if x not in lastfm_genres]
      +[(x,(float(y)+float(whatcd_genres[x]))/2.0) for x,y in lastfm_genres.items() if x in whatcd_genres]
      +[(x,y) for x,y in lastfm_genres.items() if x not in whatcd_genres],
    key=lambda x:x[1],
    reverse=True)
          # +[(x,y) for x,y in lastfm_genres.items() if x not in whatcd_genres])
  # for x,y in lastfm_genres.items():
  #   if x not in whatcd_genres:
  #     time.sleep(2)
  #     check =  apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(x,'.'))
  #     if check['status'] == 'success' and 'results' in check['response']:
  #       if 1000<sum(map(lambda z: z['totalSnatched'] if 'totalSnatched' in z else 0, check['response']['results'])):
  #         genres.append((x,y))
  genres = dict(genres[:min(len(genres),maxSimGenres)])
  try:
    p4kscore = int(round(10.0*pitchfork.search(metadata['artists'][0],metadata['album']).score()))
  except Exception:
    p4kscore = 0
  kups_playcount = 0
  if albumKups is not None:
    kups_playcount = sum([x[0]  for lst in albumKups.chunks(metadata['artists'][0],metadata['album']) for x in lst])
  if login:
    pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  popularity = con.updateGeneralPopularity((spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches,p4kscore,kups_playcount),'album')
  print("Popularity of album "+ metadata['album']+" is "+str(popularity))
  return Album(metadata['album'].strip(),metadata['path_to_album'],genres,spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches,p4kscore,kups_playcount,popularity)
  


def artistLookup(artist, apihandle=None, sim=True, con=None):
  # query whatcd for genres and similar and popularity
  login=apihandle is not None
  # try:
  if con is not None:
    populateCache(con)
  credentials = getCreds()
  if login:
    cookies = pickle.load(open('config/.cookies.dat', 'rb'))
    apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
  whatcd_artist = apihandle.request("artist", artistname=whatquote(artist))["response"]
  artist = unescape(whatcd_artist['name'])
  whatcd_seeders = whatcd_artist["statistics"]["numSeeders"]
  whatcd_snatches = whatcd_artist["statistics"]["numSnatches"]
  try:
    whatcd_genres = countToJSON( whatcd_artist["tags"])
    for key in list(whatcd_genres.keys())[:]:
      realKey = genreReplace.sub('.',key.lower().strip('.'))
      if realKey in genreList:
        whatcd_genres[realKey] = whatcd_genres[key]
      if key != realKey:
        whatcd_genres.pop(key)
    if len(whatcd_genres) > 0:
      rvar = norm(*norm.fit(list(whatcd_genres.values())))
      whatcd_genres = dict(filter(lambda x:not genreRegex.match(x[0]), [(x,rvar.cdf(float(y))) for x,y in whatcd_genres.items()]))
  except Exception as e:
    print(e)
    whatcd_genres = {}
  if sim:
    try:
      whatcd_similar = apihandle.request("similar_artists", id=whatcd_artist['id'], limit=25)
      if whatcd_similar is not None:
        whatcd_similar = countToJSON(whatcd_similar, 'score')
        if len(whatcd_similar) > 0:
          rvar = norm(*norm.fit(list(whatcd_similar.values())))
          whatcd_similar = dict([(x,rvar.cdf(float(y))) for x,y in whatcd_similar.items()])
      else:
        whatcd_similar = {}      
    except Exception as e:
      print(e)
      whatcd_similar = {}
  # query lastfm for popularity and genres and similar
  try:
    try:
      lastfm_stats = lookup('lastfm','artist',{'artist':artist.replace(' ','+')})['artist']['stats']
      lastfm_listeners = int(lastfm_stats['listeners']) if lastfm_stats['listeners']!='' else 0
      lastfm_playcount = int(lastfm_stats['playcount']) if lastfm_stats['playcount']!='' else 0
    except Exception:
      lastfm_listeners = 0
      lastfm_playcount = 0
    try:
      lastfm_genres = countToJSON(lookup('lastfm','artisttags',{'artist':artist})["toptags"]['tag'])
      for key in list(lastfm_genres.keys())[:]:
        realKey = genreReplace.sub('.',key.lower().strip('.'))
        if realKey in genreList:
          lastfm_genres[realKey] = lastfm_genres[key]
        if key != realKey:
          lastfm_genres.pop(key)
      if len(lastfm_genres) > 0:
        rvar = norm(*norm.fit(list(lastfm_genres.values())))
        lastfm_genres = dict(filter(lambda x:not genreRegex.match(x[0]) and x[1]>0,[(genreReplace.sub('.',x.lower().strip('.')),rvar.cdf(float(y))) for x,y in lastfm_genres.items()]))
    except Exception as e:
      print(e)
      lastfm_genres = {}
    if sim:
      try:
        lastfm_similar = countToJSON(lookup('lastfm','artistsimilar',{'artist':artist})["similarartists"]["artist"], "match")
      except Exception:
        lastfm_similar = {}
  except Exception:
    lastfm_listeners = 0
    lastfm_playcount = 0
    lastfm_genres = {}
    lastfm_similar = {}
  # query spotify for popularity
  try:
    spotify_id,spotify_token = getSpotifyArtistToken(artist,credentials['spotify_client_id'],credentials['spotify_client_secret'])
    spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'artists'},None,{"Authorization": "Bearer "+spotify_token})['popularity']
  except Exception:
    spotify_popularity=0
  genres =  sorted([(x,y) for x,y in whatcd_genres.items() if x not in lastfm_genres]
        +[(x,((float(y)+float(whatcd_genres[x]))/2.0)) for x,y in lastfm_genres.items() if x in whatcd_genres and (float(y)+float(whatcd_genres[x]))>0.2]
        +[(x,y) for x,y in lastfm_genres.items() if x not in whatcd_genres],
    key=lambda x:x[1],
    reverse=True)
  genres = dict(genres[:min(len(genres),maxSimGenres)])
  p4k = []
  try:
    p4kscore = int(round(10.0*pitchfork.search(artist,'').score()))
  except Exception:
    p4kscore = 0.0
  if artistAlbums is not None:
    artist_albums = [x for lst in artistAlbums.chunks(artist) for x in lst]
    for album in artist_albums:
      try:
        p4k.append(int(round(10.0*pitchfork.search(artist,album).score())))
      except Exception:
        pass
    if p4kscore>0 and p4kscore not in p4k:
      p4k.append(p4kscore)
  if len(p4k)>=1:
    p4kscore = int(round(mean(p4k)))
  kups_playcount = 0
  if artistKups is not None:
    kups_playcount = sum([x[0] for lst in artistKups.chunks(artist) for x in lst])
  if sim:
    similar_artists = sorted([(x,float(y)) for x,y in whatcd_similar.items() if x not in lastfm_similar and x.lower() != artist.lower()]
          +[(x,(float(y)+float(whatcd_similar[x]))/2.0) for x,y in lastfm_similar.items() if x in whatcd_similar and x.lower() != artist.lower()]
          +[(x,float(y)) for x,y in lastfm_similar.items() if x not in whatcd_similar and x in artistList and x.lower()!= artist.lower()],
          key=lambda x: x[1],
           reverse=True)
    similar_artists = dict(similar_artists[:min(maxSimArtists,len(similar_artists))])
  if login:
    pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  popularity = con.updateGeneralPopularity((spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches,p4kscore,kups_playcount),'artist')
  print("Popularity of artist "+ artist+" is "+str(popularity))
  return Artist(artist.strip(), genres, similar_artists if sim else {}, spotify_popularity,lastfm_listeners,lastfm_playcount, whatcd_seeders,whatcd_snatches,p4kscore,kups_playcount,popularity)
