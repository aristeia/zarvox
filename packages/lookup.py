import sys,pickle
sys.path.append("packages")
import whatapi
from libzarv import *
from libzarvclasses import *
from functools import reduce
from binascii import unhexlify
from base64 import encodestring


#song is pseudo-songobj, having attr for name and duration
def songLookup(metadata,song,path):
  try:
    credentials = getCreds()
    spotify_arids = lookup('spotify','artist',{'artist':metadata['artist']})['artists']['items']
    spotify_token=lookup('spotify','token',{},{'grant_type':'client_credentials'},{'Authorization':b'Basic '+encodestring(bytes(('%s:%s' % (credentials['spotify_client_id'],credentials['spotify_client_secret'])),encoding='utf-8')).replace(b'\n', b'')})['access_token']
    spotify_arid = reduce((lambda x,y:x if x['name'].lower()==levi_misc(x['name'].lower(),y['name'].lower(),metadata['artist'].lower()) else y), spotify_arids)['id']
    spotify_alid = reduce((lambda x,y:x if x['name'].lower() == levi_misc(x['name'].lower(),y['name'].lower(),metadata['album'].lower()) else y), lookup('spotify','album',{'artistid':spotify_arid})['items'])['id']
    spotify_id = reduce((lambda x,y:x if x['name'].lower() == levi_misc(x['name'].lower(),y['name'].lower(),song['name'].lower()) else y), lookup('spotify','song',{'albumid':spotify_alid})['items'])['id']
    spotify = lookup('spotify','id',{'id':spotify_id, 'type':'tracks'},None,{"Authorization": "Bearer "+spotify_token})
    spotify_popularity = spotify['popularity']
  except Exception:
    spotify_popularity = 0
    spotify = {'explicit':False}
  try:
    explicit=spotify['explicit']
    lyricsLookup = str(lookup('lyrics','song',{'artist':metadata['artist'], 'song':song['name']})['query']['pages'])
    if 'lyrics' in lyricsLookup:
      explicit = is_explicit(lyricsLookup.split('lyrics>')[0]) and spotify['explicit']
  except Exception:
    explicit = False
  try:
    lastfm = lookup('lastfm','song',{'artist':metadata['artist'], 'song':song['name']})['track']
    lastfm_listeners = lastfm['listeners']
    lastfm_playcount = lastfm['playcount']
  except Exception:
    lastfm_listeners = 0
    lastfm_playcount = 0
  return Song(song['name'],path,song['duration'],explicit,spotify_popularity,lastfm_listeners,lastfm_playcount)


def albumLookup(metadata, apihandle=None):
  #Get genres for album from lastfm, what.cd
  #Get popularities for album from spotify, lastfm, what.cd
  try:
    login=(not apihandle)
    credentials = getCreds()
    if login:
      cookies = pickle.load(open('config/.cookies.dat', 'rb'))
      apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
    try:
      lastfm = lookup('lastfm','album',{'artist':metadata['artist'], 'album':metadata['album']})['album']
      try:
        lastfm_listeners = lastfm['listeners']
        lastfm_playcount = lastfm['playcount']
      except Exception:
        lastfm_listeners = 0
        lastfm_playcount = 0
      try:
        lastfm_genres = countToJSON(lookup('lastfm','albumtags',{'artist':metadata['artist'], 'album':metadata['album']})["toptags"]["tag"])
        maxGenre = max([float(y) for x,y in lastfm_genres.items()])
        lastfm_genres = dict([((x.replace(' ','.').lower()),(float(y)/maxGenre)) for x,y in lastfm_genres.items()])
      except Exception:
        lastfm_genres = {}
    except Exception:
      lastfm_listeners = 0
      lastfm_playcount = 0
      lastfm_genres = {}
    try:
      spotify_arids = lookup('spotify','artist',{'artist':metadata['artist']})['artists']['items']
      spotify_token=lookup('spotify','token',{},{'grant_type':'client_credentials'},{'Authorization':b'Basic '+encodestring(bytes(('%s:%s' % (credentials['spotify_client_id'],credentials['spotify_client_secret'])),encoding='utf-8')).replace(b'\n', b'')})['access_token']
      spotify_arid = reduce((lambda x,y:x if x['name'].lower()==levi_misc(x['name'].lower(),y['name'].lower(),metadata['artist'].lower()) else y), spotify_arids)['id']
      spotify_id = reduce((lambda x,y:x if x['name'].lower() == levi_misc(x['name'].lower(),y['name'].lower(),metadata['album'].lower()) else y), lookup('spotify','album',{'artistid':spotify_arid})['items'])['id']
      spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'albums'},None,{"Authorization": "Bearer "+spotify_token})['popularity']
    except Exception:
      spotify_popularity=0
    try:
      whatcd_artist = apihandle.request("artist", artistname=whatquote(metadata['artist']))["response"]
      whatcd_albums = [x for x in whatcd_artist["torrentgroup"] for y in x['torrent'] if y['id']==metadata['whatid']]
      if len(whatcd_albums)>0:
        whatcd_album = whatcd_albums[0]
        whatcd_snatches = reduce(lambda x,y: {"snatched":(x["snatched"]+y["snatched"])},whatcd_album["torrent"])["snatched"]
        whatcd_seeders = reduce(lambda x,y: {"seeders":(x["seeders"]+y["seeders"])},whatcd_album["torrent"])["seeders"]
        whatcd_genres = dict([(x,0.5) for x in whatcd_album["tags"]])
    except Exception:
      whatcd_genres = {}
      whatcd_snatches = 0
      whatcd_seeders = 0
    genres =  ([(x,y) for x,y in whatcd_genres.items() if x not in lastfm_genres]
            +[(x,(float(y)+float(whatcd_genres[x]))/2.0) for x,y in lastfm_genres.items() if x in whatcd_genres]
            +[(x,y) for x,y in lastfm_genres.items() if x not in whatcd_genres])
    genres = dict(genres)
  except Exception:
    print("Error: cannot get all album metadata\n")
    exit(1)
  if login:
    pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  return Album(metadata['album'],metadata['path_to_album'],genres,spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches)


def artistLookup(artist, apihandle=None):
  # query whatcd for genres and similar and popularity
  try:
    try:
      credentials = getCreds()
      login=(not apihandle)
      if login:
        cookies = pickle.load(open('config/.cookies.dat', 'rb'))
        apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
      whatcd_artist = apihandle.request("artist", artistname=whatquote(artist))["response"]
      whatcd_seeders = whatcd_artist["statistics"]["numSeeders"]
      whatcd_snatches = whatcd_artist["statistics"]["numSnatches"]
      try:
        whatcd_genres = countToJSON( whatcd_artist["tags"]) 
        maxGenre = float(max([y for x,y in whatcd_genres.items()]))
        whatcd_genres = dict([(x,(y/maxGenre)) for x,y in whatcd_genres.items()])
      except Exception:
        whatcd_genres = {}
      try:
        whatcd_similar = apihandle.request("similar_artists", id=whatcd_artist['id'], limit=25)
        if whatcd_similar is not None:
          whatcd_similar = countToJSON(whatcd_similar, 'score')
          maxSimilarity = float(max([y for x,y in whatcd_similar.items()]))
          whatcd_similar = dict([(x,(y/maxSimilarity)) for x,y in whatcd_similar.items()])
        else:
          whatcd_similar = {}
      except Exception:
        whatcd_similar = {}
    except Exception:
      whatcd_genres = {}
      whatcd_snatches = 0
      whatcd_seeders = 0
      whatcd_similar = {}
    # query lastfm for popularity and genres and similar
    try:
      lastfm = lookup('lastfm','artist',{'artist':artist})['artist']
      try:
        lastfm_listeners = lastfm['stats']['listeners']
        lastfm_playcount = lastfm['stats']['playcount']
      except Exception:
        lastfm_listeners = 0
        lastfm_playcount = 0
      try:
        lastfm_genres = countToJSON(lookup('lastfm','artisttags',{'artist':artist})["toptags"]['tag'])
        maxGenre = float(max([y for x,y in lastfm_genres.items()]))
        lastfm_genres = dict([(x.replace(' ','.').lower(),(y/maxGenre)) for x,y in lastfm_genres.items()])
      except Exception:
        lastfm_genres = {}
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
      spotify_ids = lookup('spotify','artist',{'artist':artist})['artists']['items']
      spotify_token=lookup('spotify','token',{},{'grant_type':'client_credentials'},{'Authorization':b'Basic '+encodestring(bytes(('%s:%s' % (credentials['spotify_client_id'],credentials['spotify_client_secret'])),encoding='utf-8')).replace(b'\n', b'')})['access_token']
      spotify_id = reduce((lambda x,y:x if x['name'].lower()==levi_misc(x['name'].lower(),y['name'].lower(),artist.lower()) else y), spotify_ids)['id']
      spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'artists'},None,{"Authorization": "Bearer "+spotify_token})['popularity']
    except Exception:
      spotify_popularity=0
    genres =  ([(x,y) for x,y in whatcd_genres.items() if x not in lastfm_genres]
          +[(x,(float(y)+float(whatcd_genres[x]))/2.0) for x,y in lastfm_genres.items() if x in whatcd_genres])
    genres = dict(genres)
    similar_artists = ([(x,y) for x,y in whatcd_similar.items() if x not in lastfm_similar]
          +[(x,(float(y)+float(whatcd_similar[x]))/2.0) for x,y in lastfm_similar.items() if x in whatcd_similar])
    # for x,y in lastfm_similar.items():
    #   if x not in whatcd_similar:
    #     check =  apihandle.request("artist",artistname=whatquote(x))['status']
    #     if check == 'success':
    #       similar_artists.append((x,y))
    similar_artists = dict(similar_artists)
  except exception:
    print("Error: cannot get all artist metadata\n")
    exit(1) 
  if login:
    pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  return Artist(artist, genres, similar_artists, spotify_popularity,lastfm_listeners,lastfm_playcount, whatcd_seeders,whatcd_snatches)
print(str(songLookup({"album": "FWA", "format": "mp3", "whatid": 31959442, "path_to_album": "/Users/jon/Downloads/Lil Wayne - Free Weezy Album (2015) WEB V0", "artist": "Lil Wayne"}, {'name':'Glory','duration':306},"1-15. Glory.mp3")))