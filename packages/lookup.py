import sys,pickle,re,time
sys.path.append("packages")
import whatapi
from libzarv import *
from libzarvclasses import *
from functools import reduce
from binascii import unhexlify
from base64 import encodebytes
from urllib import parse
from html import unescape

genreRegex = re.compile('^\d*.?$')
genreReplace = re.compile('\W')
genreList = []
artistList = []


def populateCache(con):
  genreList = [x[0] for lst in con.db.prepare("SELECT genre FROM genres").chunks() for x in lst]
  artistList = [x[0] for lst in con.db.prepare("SELECT artist FROM artists").chunks() for x in lst]

def getSpotifyArtistToken(artistName,spotify_client_id,spotify_client_secret):
  try:
    spotify_arids = lookup('spotify','artist',{'artist':artistName})['artists']['items']
    spotify_token=lookup('spotify','token',{},{'grant_type':'client_credentials'},{'Authorization':b'Basic '+encodebytes(bytes(('%s:%s' % (spotify_client_id,spotify_client_secret)),encoding='utf-8')).replace(b'\n', b'')})['access_token']
    spotify_arid = reduce((lambda x,y:x if x['name'].lower()==levi_misc(x['name'].lower(),y['name'].lower(),artistName.lower()) else y), spotify_arids)['id']
    return spotify_arid,spotify_token
  except Exception:
    print("Error: cannot get artistid on spotify")
  return -1


#song is pseudo-songobj, having attr for name and duration
def songLookup(metadata,song,path):
  try:
    credentials = getCreds()
    spotify_arid,spotify_token = getSpotifyArtistToken(metadata['artist'],credentials['spotify_client_id'],credentials['spotify_client_secret'])
    spotify_alid = reduce((lambda x,y:x if x['name'].lower() == levi_misc(x['name'].lower(),y['name'].lower(),metadata['album'].lower()) else y), lookup('spotify','album',{'artistid':spotify_arid})['items'])['id']
    spotify_id = reduce((lambda x,y:x if x['name'].lower() == levi_misc(x['name'].lower(),y['name'].lower(),song['name'].lower()) else y), lookup('spotify','song',{'albumid':spotify_alid})['items'])['id']
    spotify = lookup('spotify','id',{'id':spotify_id, 'type':'tracks'},None,{"Authorization": "Bearer "+spotify_token})
    spotify_popularity = spotify['popularity']
  except Exception:
    spotify_popularity = 0
    spotify = {'explicit':False}
  try:
    explicit=spotify['explicit']
    try:
      lyricsLookup = str(lookup('lyrics','song',{'artist':metadata['artist'], 'song':song['name']})['query']['pages'])
      if 'lyrics' in lyricsLookup:
        explicit = is_explicit(lyricsLookup.split('lyrics>')[1]) or spotify['explicit']
    except Exception:
      explicit = spotify['explicit']
  except Exception:
    explicit = False
  try:
    lastfm = lookup('lastfm','song',{'artist':metadata['artist'], 'song':song['name']})['track']
    lastfm_listeners = lastfm['listeners'] if lastfm['listeners']!='' else 0
    lastfm_playcount = lastfm['playcount'] if lastfm['playcount']!='' else 0
  except Exception:
    lastfm_listeners = 0
    lastfm_playcount = 0
  return Song(song['name'],path,song['duration'],explicit,spotify_popularity,lastfm_listeners,lastfm_playcount)


def albumLookup(metadata, apihandle=None, con=None):
  #Get genres for album from lastfm, what.cd
  #Get popularities for album from spotify, lastfm, what.cd  
  login= apihandle is not None
  try:
    if con is not None and genreList == []:
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
    lastfm = [x for x in [lookup('lastfm','album',{'artist':x, 'album':metadata['album']}) for x in metadata['artists']] if 'album' in x][0]['album']
    try:
      lastfm_listeners = int(lastfm['listeners']) if lastfm['listeners']!='' else 0
      lastfm_playcount = int(lastfm['playcount']) if lastfm['playcount']!='' else 0
    except Exception:
      lastfm_listeners = 0
      lastfm_playcount = 0
    try:
      lastfm_genres = countToJSON(lookup('lastfm','albumtags',{'artist':metadata['artist'], 'album':metadata['album']})["toptags"]["tag"])
      maxGenre = max([float(y) for x,y in lastfm_genres.items()])
      lastfm_genres = dict(filter(lambda x:not genreRegex.match(x[0]), [((genreReplace.sub('.',x.lower().strip('.'))),(float(y)/maxGenre)) for x,y in lastfm_genres.items()]))
    except Exception:
      lastfm_genres = {}
  except Exception:
    lastfm_listeners = 0
    lastfm_playcount = 0
    lastfm_genres = {}
  spotify_popularity = 0
  tempArtistIndex = 0
  while spotify_popularity==0 and tempArtistIndex<len(metadata['artists']):
    try:
      spotify_arid,spotify_token = getSpotifyArtistToken(metadata['artists'][tempArtistIndex],credentials['spotify_client_id'],credentials['spotify_client_secret'])
      spotify_id = reduce((lambda x,y:x if x['name'].lower() == levi_misc(x['name'].lower(),y['name'].lower(),metadata['album'].lower()) else y), lookup('spotify','album',{'artistid':spotify_arid})['items'])['id']
      spotify_popularity = int(lookup('spotify','id',{'id':spotify_id, 'type':'albums'},None,{"Authorization": "Bearer "+spotify_token})['popularity'])
    except Exception:
      spotify_popularity=0
    tempArtistIndex+=1
  genres =  ([(x,y) for x,y in whatcd_genres.items() if x not in lastfm_genres]
          +[(x,(float(y)+float(whatcd_genres[x]))/2.0) for x,y in lastfm_genres.items() if x in whatcd_genres]
          +[(x,y) for x,y in lastfm_genres.items() if x not in whatcd_genres and x in genreList])
          # +[(x,y) for x,y in lastfm_genres.items() if x not in whatcd_genres])
  # for x,y in lastfm_genres.items():
  #   if x not in whatcd_genres:
  #     time.sleep(2)
  #     check =  apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(x,'.'))
  #     if check['status'] == 'success' and 'results' in check['response']:
  #       if 1000<sum(map(lambda z: z['totalSnatched'] if 'totalSnatched' in z else 0, check['response']['results'])):
  #         genres.append((x,y))
  genres = dict(genres)
  if login:
    pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  popularity = con.updateGeneralPopularity((spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches),'album')
  print("Popularity of album "+ metadata['album']+" is "+str(popularity))
  return Album(metadata['album'],metadata['path_to_album'],genres,spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches,popularity)
  


def artistLookup(artist, apihandle=None, sim=True, con =None):
  # query whatcd for genres and similar and popularity
  login=apihandle is not None
  # try:
  if con is not None and genreList == []:
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
    maxGenre =max([float(y) for x,y in whatcd_genres.items()])
    whatcd_genres = dict(filter(lambda x:not genreRegex.match(x[0]) and x[1]>0,[(genreReplace.sub('.',x.lower().strip('.')),(float(y)/maxGenre)) for x,y in whatcd_genres.items()]))
  except Exception:
    whatcd_genres = {}
  if sim:
    try:
      whatcd_similar = apihandle.request("similar_artists", id=whatcd_artist['id'], limit=25)
      if whatcd_similar is not None:
        whatcd_similar = countToJSON(whatcd_similar, 'score')
        maxSimilarity = float(max([float(y) for x,y in whatcd_similar.items()]))
        whatcd_similar = dict([(x,(float(y)/maxSimilarity)) for x,y in whatcd_similar.items()])
      else:
        whatcd_similar = {}
    except Exception:
      whatcd_similar = {}      
  # except Exception:
  #   whatcd_genres = {}
  #   whatcd_snatches = 0
  #   whatcd_seeders = 0
  #   whatcd_similar = {}
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
      maxGenre = max([float(y) for x,y in lastfm_genres.items()])
      lastfm_genres = dict(filter(lambda x:not genreRegex.match(x[0]) and x[1]>0,[(genreReplace.sub('.',x.lower().strip('.')),(float(y)/maxGenre)) for x,y in lastfm_genres.items()]))
    except Exception:
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
  genres =  ([(x,y) for x,y in whatcd_genres.items() if x not in lastfm_genres and y>0.1]
        +[(x,((float(y)+float(whatcd_genres[x]))/2.0)) for x,y in lastfm_genres.items() if x in whatcd_genres and (float(y)+float(whatcd_genres[x]))>0.2]
        +[(x,y) for x,y in lastfm_genres.items() if x not in whatcd_genres and x in genreList and y>0.1])
  genres = dict(genres)
  if sim:
    similar_artists = ([(x,y) for x,y in whatcd_similar.items() if x not in lastfm_similar and x!=artist]
          +[(x,(float(y)+float(whatcd_similar[x]))/2.0) for x,y in lastfm_similar.items() if x in whatcd_similar and x!=artist]
          +[(x,y) for x,y in lastfm_similar.items() if x not in whatcd_similar and x in artistList and x!= artist])
    # if len(similar_artists)<20:
    #   if len(lastfm_similar)>=(21-len(similar_artists)):
    #     tempSim = sorted(lastfm_similar.items(), key=lambda x:x[1])[:(21-len(similar_artists))]
    #   else:
    #     tempSim = sorted(lastfm_similar.items(), key=lambda x:x[1])
    #   for x,y in tempSim:
    #     if x not in whatcd_similar:
    #       time.sleep(2)
    #       check =  apihandle.request("artist",artistname=whatquote(x))
    #       if 'status' in check and check['status'] == 'success':
    #         similar_artists.append((unescape(check['response']['name']),float(y)))
    #         print((unescape(check['response']['name']))+" is similar to "+artist+" by "+str(y))
    similar_artists = dict(similar_artists)
  if login:
    pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  popularity = con.updateGeneralPopularity((spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches),'artist')
  print("Popularity of artist "+ artist+" is "+str(popularity))
  return Artist(artist, genres, similar_artists if sim else {}, spotify_popularity,lastfm_listeners,lastfm_playcount, whatcd_seeders,whatcd_snatches,popularity)