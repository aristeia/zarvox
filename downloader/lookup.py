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
  print("Populating lookup cache...")
  global genreList,artistList,artistAlbums,albumKups,artistKups,songKups,artistCache,albumCache,songCache
  if len(genreList) == 0:
    genreList = [x[0] for lst in con.db.prepare(
      '''SELECT genre FROM genres''').chunks() for x in lst]
  if len(artistList) == 0:
    artistList = [x[0] for lst in con.db.prepare(
      '''SELECT artist FROM artists''').chunks() for x in lst]

  artistAlbums = con.db.prepare(
    '''SELECT album FROM albums 
    INNER JOIN artists_albums ON albums.album_id = artists_albums.album_id 
    INNER JOIN artists ON artists_albums.artist_id = artists.artist_id 
    WHERE artists.artist = $1''')
  
  albumKups = con.db.prepare(
    '''SELECT albums.kups_playcount FROM albums 
    INNER JOIN artists_albums ON albums.album_id = artists_albums.album_id 
    INNER JOIN artists ON artists_albums.artist_id = artists.artist_id 
    WHERE artists.artist = $1 and albums.album = $2''')
  artistKups = con.db.prepare(
    '''SELECT kups_playcount FROM artists WHERE artist = $1''')
  songKups = con.db.prepare(
    '''SELECT songs.kups_playcount FROM songs 
    INNER JOIN albums on albums.album_id = songs.album_id 
    where songs.song = $1 and albums.album = $2''')
  
  artistCache = con.db.prepare(
    '''SELECT * FROM artists WHERE artist = $1''')
  albumCache = con.db.prepare(
    '''SELECT albums.* FROM albums 
    INNER JOIN artists_albums ON albums.album_id = artists_albums.album_id
    WHERE artists_albums.artist_id = $2 AND albums.album = $1''')
  songCache = con.db.prepare(
    '''SELECT * FROM songs 
    WHERE album_id = $2 AND song = $1''')
  print("Populated!")


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
  if con is not None and any(x is None for x in [songCache,songKups]):
    populateCache(con)
  credentials = getCreds()
  songCached = (reduce(
      lambda x,y: x if y is None else y,
      [x for artist in metadata['artists'] 
        for lst in songCache.chunks(song['name'],metadata['album_id']) 
        for x in lst],
      None) if songCache is not None and 'album_id' in metadata
    else None)
  if songCached is not None:
    print("Using cached song values")
    explicit = songCached[5]
    spotify_popularity = songCached[6]
    lastfm_listeners = songCached[7]
    lastfm_playcount = songCached[8]
    kups_playcount = songCached[11]
    path_to_song = songCached[2]
  else: #default values
    explicit = False
    spotify_popularity = 0
    lastfm_listeners = 0
    lastfm_playcount = 0
    kups_playcount = 0
    if all(len(x)>0 for x in [path, metadata['path_to_album']]):
      path_to_song = metadata['path_to_album']+'/'+path
    else:
      path_to_song = ''

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
      tempArtistIndex+=1

  if lastfm_listeners==0 or lastfm_playcount==0:
    tempArtistIndex = 0
    while lastfm_listeners==0 and lastfm_playcount==0 and tempArtistIndex<len(metadata['artists']):
      try:
        lastfm = lookup('lastfm','song',{'artist':metadata['artists'][tempArtistIndex], 'song':song['name']}) 
        if 'track' in lastfm:
          lastfm_listeners = lastfm['track']['listeners'] if lastfm['track']['listeners']!='' else 0
          lastfm_playcount = lastfm['track']['playcount'] if lastfm['track']['playcount']!='' else 0
      except Exception as e:
        handleError(e,"Warning: cannot get song lastfm data. Using 0s.")
      tempArtistIndex+=1

  if kups_playcount == 0:
    if songKups is not None:
      kups_playcount = sum([x[0] for lst in songKups.chunks(song['name'],metadata['album']) for x in lst])

  return Song(song['name'],path_to_song,song['duration'],explicit,spotify_popularity,lastfm_listeners,lastfm_playcount,kups_playcount)


def albumLookup(metadata, apihandle=None, con=None):
  #Get genres for album from lastfm, what.cd
  #Get popularities for album from spotify, lastfm, what.cd  
  login = apihandle is not None
  if (con is not None and 
    any(x is None or (type(x)==list and len(x)==0) 
    for x in [albumCache,albumKups,genreList])):
    populateCache(con)
  credentials = getCreds()

  albumCached = (reduce(
      lambda x,y: x if y is None else y,
      [x for artist in metadata['artists'] 
        for lst in albumCache.chunks(metadata['album'],metadata['artist_id']) 
        for x in lst],
      None) if albumCache is not None and 'artist_id' in metadata
    else None)
  if albumCached is not None:
    print("Using cached album values")
    spotify_popularity = albumCached[3]
    lastfm_listeners = albumCached[4]
    lastfm_playcount = albumCached[5]
    whatcd_seeders = albumCached[6]
    whatcd_snatches = albumCached[7]
    p4kscore = albumCached[9]
    kups_playcount = albumCached[10]
  else: #default values
    spotify_popularity = 0
    lastfm_listeners = 0
    lastfm_playcount = 0
    whatcd_seeders = 0
    whatcd_snatches = 0
    p4kscore = 0
    kups_playcount = 0

  whatcd_genres = {}
  if whatcd_seeders==0 or whatcd_snatches==0:
    try:
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
        whatcd_genres = dict(filter(lambda x: not genreRegex.match(x[0]), 
          [(genreReplace.sub('.',x.strip('.').lower()),0.5) 
            for x in whatcd_album['group']["tags"]]))
    except Exception as e:
      handleError(e,"Warning: cannot get album whatcd data.")

  lastfm_genres = {}
  if lastfm_listeners==0 or lastfm_playcount==0:
    try:
      lastfm = max([y for y in [lookup('lastfm','album',{'artist':x, 'album':metadata['album']}) for x in metadata['artists']] if 'album' in y],
        key=lambda x: x['album']['playcount'])
      if len(lastfm)>0 and 'album' in lastfm:
        lastfm = lastfm['album']
        try:
          lastfm_listeners = int(lastfm['listeners']) if lastfm['listeners']!='' else 0
          lastfm_playcount = int(lastfm['playcount']) if lastfm['playcount']!='' else 0
        except Exception as e:
          handleError(e,"Warning: cannot get album lastfm playcount data.")
        try:
          tempDict = countToJSON(lookup('lastfm','albumtags',{'artist':lastfm['artist'], 'album':lastfm['name']})["toptags"]["tag"])
          for key in list(tempDict.keys())[:]:
            realKey = genreReplace.sub('.',key.lower().strip('.'))
            if realKey in genreList:
              tempDict[realKey] = tempDict[key]
            if key != realKey:
              tempDict.pop(key)
          if len(tempDict) > 0:
            rvar = norm(*norm.fit(list(tempDict.values())))
            lastfm_genres = dict(filter(lambda x: not genreRegex.match(x[0]), 
              [(x,rvar.cdf(float(y))) for x,y in tempDict.items()]))
        except Exception as e:
          handleError(e,"Warning: cannot get album lastfm genre data.")
    except Exception as e:
      handleError(e,"Warning: cannot get album lastfm general data.")

  if spotify_popularity == 0:
    tempArtistIndex = 0
    while spotify_popularity==0 and tempArtistIndex<len(metadata['artists']):
      try:
        spotify_arid,spotify_token = getSpotifyArtistToken(metadata['artists'][tempArtistIndex],credentials['spotify_client_id'],credentials['spotify_client_secret'])
        spotify_id = reduce((lambda x,y:x if x['name'].lower() == levi_misc(x['name'].lower(),y['name'].lower(),metadata['album'].lower()) else y), lookup('spotify','album',{'artistid':spotify_arid})['items'])['id']
        spotify_popularity = int(lookup('spotify','id',{'id':spotify_id, 'type':'albums'},None,{"Authorization": "Bearer "+spotify_token})['popularity'])
      except Exception as e:
        handleError(e,"Warning: cannot get album spotify data.")
      tempArtistIndex+=1

  # if len(genres) < maxSimGenres and (len(whatcd_genres)>0 or len(lastfm_genres)>0)
  genres = sorted(
    [(x,y) for x,y in whatcd_genres.items() if x not in lastfm_genres]
      +[(x,(float(y)+float(whatcd_genres[x]))/2.0) for x,y in lastfm_genres.items() if x in whatcd_genres]
      +[(x,y) for x,y in lastfm_genres.items() if x not in whatcd_genres],
    key=lambda x:x[1],
    reverse=True)

  genres = dict(genres[:min(len(genres),maxSimGenres)])

  if p4kscore == 0:
    try:
      p4kscore = int(round(10.0*pitchfork.search(metadata['artists'][0],metadata['album']).score()))
    except Exception as e:
      handleError(e,"Warning: cannot get album pitchfork data.")
  
  if kups_playcount == 0:
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
  if (con is not None and 
    any(x is None or (type(x)==list and len(x)==0) 
    for x in [artistCache,artistKups,genreList,artistAlbums,artistList])):
    populateCache(con)
  credentials = getCreds()
  if login:
    cookies = pickle.load(open('config/.cookies.dat', 'rb'))
    apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
  
  artistCached = (reduce(
      lambda x,y: x if y is None else y,
      [x for lst in artistCache.chunks(artist) 
        for x in lst],
      None) if artistCache is not None
    else None)
  if artistCached is not None:
    print("Using cached artist values")
    spotify_popularity = artistCached[2]
    lastfm_listeners = artistCached[3]
    lastfm_playcount = artistCached[4]
    whatcd_seeders = artistCached[5]
    whatcd_snatches = artistCached[6]
    p4kscore = artistCached[8]
    kups_playcount = artistCached[9]
  else: #default values
    spotify_popularity = 0
    lastfm_listeners = 0
    lastfm_playcount = 0
    whatcd_seeders = 0
    whatcd_snatches = 0
    p4kscore = 0
    kups_playcount = 0

  whatcd_genres = {}
  whatcd_similar = {}
  if whatcd_seeders==0 or whatcd_snatches==0:
    whatcd_artist = apihandle.request("artist", artistname=whatquote(artist))["response"]
    artist = unescape(whatcd_artist['name'])
    whatcd_seeders = whatcd_artist["statistics"]["numSeeders"]
    whatcd_snatches = whatcd_artist["statistics"]["numSnatches"]
    try:
      tempDict = countToJSON( whatcd_artist["tags"])
      for key in list(tempDict.keys())[:]:
        realKey = genreReplace.sub('.',key.lower().strip('.'))
        if realKey in genreList:
          tempDict[realKey] = tempDict[key]
        if key != realKey:
          tempDict.pop(key)
      if len(tempDict) > 0:
        rvar = norm(*norm.fit(list(tempDict.values())))
        whatcd_genres = dict(filter(lambda x:not genreRegex.match(x[0]), 
          [(x,rvar.cdf(float(y))) 
            for x,y in tempDict.items()]))
    except Exception as e:
      handleError(e,"Warning: cannot get artist whatcd data.")
    if sim:
      try:
        tempDict = apihandle.request("similar_artists", id=whatcd_artist['id'], limit=25)
        if tempDict is not None:
          tempDict = countToJSON(tempDict, 'score')
          if len(tempDict) > 0:
            rvar = norm(*norm.fit(list(tempDict.values())))
            whatcd_similar = dict([(x,rvar.cdf(float(y))) for x,y in tempDict.items()])    
      except Exception as e:
        handleError(e,"Warning: cannot get artist whatcd simartists.")


  lastfm_genres = {}
  lastfm_similar = {}
  if lastfm_listeners==0 or lastfm_playcount==0:
    # query lastfm for popularity and genres and similar
    try:
      lastfm_stats = lookup('lastfm','artist',{'artist':artist.replace(' ','+')})['artist']['stats']
      lastfm_listeners = int(lastfm_stats['listeners']) if lastfm_stats['listeners']!='' else 0
      lastfm_playcount = int(lastfm_stats['playcount']) if lastfm_stats['playcount']!='' else 0
    except Exception as e:
      handleError(e,"Warning: cannot get artist lastfm statistics.")
    try:
      tempDict = countToJSON(lookup('lastfm','artisttags',{'artist':artist})["toptags"]['tag'])
      for key in list(tempDict.keys())[:]:
        realKey = genreReplace.sub('.',key.lower().strip('.'))
        if realKey in genreList:
          tempDict[realKey] = tempDict[key]
        if key != realKey:
          tempDict.pop(key)
      if len(tempDict) > 0:
        rvar = norm(*norm.fit(list(tempDict.values())))
        lastfm_genres = dict(filter(lambda x: not genreRegex.match(x[0]) and x[1]>0,
          [(genreReplace.sub('.',x.lower().strip('.')),rvar.cdf(float(y))) 
            for x,y in tempDict.items()]))
    except Exception as e:
      handleError(e,"Warning: cannot get artist lastfm genres.")
    if sim:
      try:
        lastfm_similar = countToJSON(lookup('lastfm','artistsimilar',{'artist':artist})["similarartists"]["artist"], "match")
      except Exception as e:
        handleError(e,"Warning: cannot get artist lastfm simartists.")

  if spotify_popularity == 0:
    # query spotify for popularity
    try:
      spotify_id,spotify_token = getSpotifyArtistToken(artist,credentials['spotify_client_id'],credentials['spotify_client_secret'])
      if spotify_token is not None and spotify_id is not None:
        spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'artists'},None,{"Authorization": "Bearer "+spotify_token})['popularity']
    except Exception as e:
      handleError(e,"Warning: cannot get album spotify data.")
  genres =  sorted([(x,y) for x,y in whatcd_genres.items() if x not in lastfm_genres]
        +[(x,((float(y)+float(whatcd_genres[x]))/2.0)) for x,y in lastfm_genres.items() if x in whatcd_genres and (float(y)+float(whatcd_genres[x]))>0.2]
        +[(x,y) for x,y in lastfm_genres.items() if x not in whatcd_genres],
    key=lambda x:x[1],
    reverse=True)
  genres = dict(genres[:min(len(genres),maxSimGenres)])

  if p4kscore == 0:
    p4k = []
    try:
      p4kscore = int(round(10.0*pitchfork.search(artist,'').score()))
    except Exception as e:
      handleError(e,"Warning: cannot get artist pitchfork data.")
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

  if kups_playcount == 0:
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
