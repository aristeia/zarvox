import sys,os,json
sys.path.append("packages")
import whatapi
from libzarv import *
from libzarvclasses import *

apihandle = None
metadata = {
  'album':None,
  'artist':None
}

#song is pseudo-songobj, having attr for name and duration
def songLookup(song,path, album=metadata['album'],artist=metadata['artist']):
  #Get explicitness for each song
  global metadata
  
  #see which one (x,y) is closer in similarity to third arg, weighted towards song name correctness and artist correctness
  #does error checking
  def levi_spotify_song(x,y, s):
    if not (x['name'] and x['album'] and x['album']['name'] and x['artists'] and x['artists'] != [] and x['artists'][0]['name']):
      return y
    elif not (y['name'] and y['album'] and y['album']['name'] and y['artists'] and y['artists'] != [] and y['artists'][0]['name']):
      return x
    else:
      lx = (Levenshtein.ratio(x['album']['name'].lower(),metadata['album'].lower())+2*Levenshtein.ratio(x['artists'][0]['name'].lower(),metadata['artist'].lower())+4*Levenshtein.ratio(x['name'].lower(),s))
      ly = (Levenshtein.ratio(y['album']['name'].lower(),metadata['album'].lower())+2*Levenshtein.ratio(y['artists'][0]['name'].lower(),metadata['artist'].lower())+4*Levenshtein.ratio(y['name'].lower(),s))
      return y if ly>lx else x

  try:
    spotify_id = reduce(lambda x,y:levi_spotify_song(x.lower(),y.lower(),song.name.lower()), lookup('spotify','song',{'artist':artist,'album':album, 'song':song.name})['tracks']['items'])
    spotify = lookup('spotify','id',{'id':spotify_id, 'type':'songs'})
    spotify_popularity = spotify['popularity']
    lyricsLookup = str(lookup('lyrics','song',{'artist':artist, 'song':song.name})['query']['pages'])
    if sometest_for_success_of_lyrics:
      explicit = is_explicit(lyricsLookup.split('lyrics>')[1])
    else:
      explicit = spotify['explicit']
    lastfm = lookup('lastfm','song',{'artist':artist, 'song':song.name})
    lastfm_listeners = lastfm['listeners']
    lastfm_playcount = lastfm['playcount']
  except Exception, e:
    print("Error: cannot get all song metadata\n"+str(e))
    exit(1)
  return Song(song.name,path,song.duration,explicit,spotify_popularity,lastfm_listeners,lastfm_playcount)

def albumLookup(album=metadata['album'],artist=metadata['artist']):
  #Get genres for album from lastfm, what.cd
  #Get popularities for album from spotify, lastfm, what.cd
  global metadata, apihandle
  try:
    lastfm = lookup('lastfm','album',{'artist':metadata['artist'], 'album':metadata['album']})['album']
    lastfm_listeners = lastfm['listeners']
    lastfm_playcount = lastfm['playcount']
    lastfm_genres = countToJSON(map(lambda x: {'name':self.tag.sub('.',x['name']),'count':x['count']},lookup('lastfm','albumtags',{'artist':metadata['artist'], 'album':metadata['album']})["toptags"]["tag"]))
    spotify_id = reduce(lambda x,y:levi_misc(x['name'].lower(),y['name'].lower(),song.album.lower()), lookup('spotify','album',{'artist':metadata['artist'],'album':metadata['album']})['albums']['items'])
    spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'albums'})['popularity']
    login=(not apihandle)
    if login:
      credentials = getCreds()
      cookies = pickle.load(open('config/.cookies.dat', 'rb'))
      apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
    whatcd_artist = apihandle.request("artist", artistname=metadata['artist'])["response"]
    whatcd_album = filter(lambda x: x['torrent']['id']==metadata['whatid'],whatcd_artist["torrentgroup"])[0]
    whatcd_genres = countToJSON(map(lambda x: {'name': self.tag.sub('.',x['name']),'count':x['count']}, whatcd_album["tags"]))
    whatcd_snatches = reduce(lambda x,y: {"snatched":(x["snatched"]+y["snatched"])},whatcd_album["torrents"])["snatched"]
    whatcd_seeders = reduce(lambda x,y: {"seeders":(x["seeders"]+y["seeders"])},whatcd_album["torrents"])["seeders"]
    genres = dict([(x,50) for x in whatcd_genres if x not in lastfm_genres]+lastfm_genres.items())
  except Exception, e:
    print("Error: cannot get all album metadata\n"+str(e))
    exit(1)
  if login:
    pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  return Album(metadata['album'].lower(),metadata['path'],genres,spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches)


def artistLookup(artist = metadata['artist']):
  # query whatcd for genres and similar and popularity
  global metadata,apihandle
  try:
    login=(not apihandle)
    if login:
      credentials = getCreds()
      cookies = pickle.load(open('config/.cookies.dat', 'rb'))
      apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
    whatcd_artist = apihandle.request("artist", artistname=artist)["response"]
    whatcd_similar = countToJSON(apihandle.request("similar_artists", id=whatcd_artist["response"]['id']), 'score')
    whatcd_seeders = whatcd_artist["statistics"]["numSeeders"]
    whatcd_snatches = whatcd_artist["statistics"]["numSnatches"]
    whatcd_genres = countToJSON(map(lambda x: {'name':self.tag.sub('.',x['name']),'count':x['count']}, whatcd_artist["tags"]))
    # query lastfm for popularity and genres and similar
    lastfm = lookup('lastfm','artist',{'artist':artist})['artist']
    lastfm_listeners = lastfm['listeners']
    lastfm_playcount = lastfm['playcount']
    lastfm_genres = countToJSON(map(lambda x: {'name':self.tag.sub('.',x['name']),'count':x['count']},lookup('lastfm','artisttags',{'artist':artist})["toptags"]["tag"]))
    lastfm_similar = countToJSON(lookup('lastfm','artistsimilar',{'artist':artist})["similarartists"]["artist"], "match")
    # query spotify for popularity
    spotify_id = reduce(lambda x,y:levi_misc(x['name'].lower(),y['name'].lower(),artist.lower()), lookup('spotify','artist',{'artist':artist})['artists']['items'])
    spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'artist'})['popularity']
    genres = dict([(x,y) for x,y in whatcd_genres if x not in lastfm_genres]+lastfm_genres.items())
  except Exception, e:
    print("Error: cannot get all artist metadata\n"+str(e))
    exit(1) 
  if login:
    pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  return Artist(artist, genres, similar_artists, spotify_popularity,lastfm_listeners,lastfm_playcount, whatcd_snatches, whatcd_seeders)

