import os,sys,whatapi,postgresql as pg
sys.path.append("packages")
from random import shuffle
from lookup import *
from libzarv import *
from urllib import parse
from html import unescape
from libzarvclasses import *
from database import databaseCon
from math import ceil,floor

#Download the top whatcd & lastfm & spotify albums' metadata via lookup
#Calc their downloadability and set that into db

def notBadArtist(group):
  return ('artist' in group 
    and group['artist'].lower()!='various artists')

def startup_tests(args, credentials):
  if len(args) != 2:
    print("Error: postprocessor received wrong number of args")
    exit(1)
  try:
    db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_password']+'@localhost/'+credentials['db_name'])
  except Exception as e:
    print("Error: cannot connect to database\n")
    print(e)
    exit(1)
  print("Zarvox database are online")
  try:
    pingtest(['whatcd'])
  except Exception:
    print(e)
    exit(1)
  print("Pingtest complete; sites are online")
  return db

def downloadGenreData(genre):
  global apihandle
  whatPages=[]
  popularity = (ceil(genre[1]*20) if genre[1] is not None else 0) + 1
  x=0
  print("Downloading "+str(popularity)+" for "+genre[0])
  while len(whatPages)<popularity:
    x+=1
    time.sleep(5)
    what = apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x),category='Music')
    while what['status'] != 'success':
      time.sleep(10)
      what = apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x),category='Music')
    whatPages+=what['response']['results']
  return processedGroups(whatPages[0:popularity])

def processedGroups(whatPages):
  global apihandle
  what_info=[]
  for group in whatPages:
    processedGroup = processData(group)
    if processedGroup != {}:
      what_info.append(processedGroup)
  return what_info

def processedTorsWithInfo(whatTors):
  global apihandle,con
  what_info=[]
  # query = con.db.prepare("SELECT * FROM artists WHERE artist = $1 LIMIT 1")
  for tor in whatTors:
    try:
      whatGroup = apihandle.request("torrentgroup",id=tor['groupId'])
      if whatGroup['status']=='success': 
        torGroup = getTorrentMetadata(whatGroup['response'])
        if torGroup != {}:
          what_info.append(torGroup)
    except Exception as e:
      print("Failed to get torrentgroup from what")
      print(e)
  print("Out of this group, "+str(len(what_info))+" good downloads")
  return [processInfo(x) for x in what_info]

def processData(group):
  if notBadArtist(group) and group['releaseType']!='Compilation':
    whatGroup = apihandle.request("torrentgroup",id=group['groupId'])
    if whatGroup['status']=='success':
      return getTorrentMetadata(whatGroup['response'])
  return {}

def processInfo(metadata):
  global apihandle,con
  res = {}
  artists = [artistLookup(x, apihandle, True, con) for x in metadata['artists']]
  res['artists'] = con.getArtistsDB(artists,True)
  print("Done with artists")
  album = albumLookup(metadata,apihandle,con)
  res['album'] = con.getAlbumDB( album,True,db_artistid=res['artists'][0]['select'][0])
  print("Done with album")

  res['artists_albums'] = con.getArtistAlbumDB(res['album'][0]['select'][0],True, [artist['select'][0] for artist in res['artists']])
  
  abgenres = con.getGenreDB( [x for x,_ in album.genres.items()], apihandle,'album_',True)
  argenres = con.getGenreDB( list(set([x for artist in artists for x,_ in artist.genres.items() ])), apihandle,'artist_',True)
  res['genre'] = abgenres+argenres
  album.genres = correctGenreNames(album.genres, abgenres)
  for artist in artists:
    artist.genres = correctGenreNames(artist.genres, argenres)
  print("Done with genres")

  res['album_genre'] = con.getAlbumGenreDB( album.genres, True,album=res['album'][0]['select'])
  res['artist_genre'] = [lst for artist, dbartist in zip(artists,res['artists']) for lst in con.getArtistGenreDB( artist.genres, True,artist=dbartist['select'])]
  
  print("Done with artist/album genres")
  res['similar_artist'], res['other_artist'], res['other_similar'] = [],[],[]
  for artist,dbartist in zip(artists,res['artists']):
    temp = con.getSimilarArtistsDB(artist.similar_artists, apihandle, dbartist['select'],True)
    res['similar_artist'].extend(temp[0])
    res['other_artist'].extend(temp[1])
    res['other_similar'].extend(temp[2])
  return res

def lookupAll(lookupType,conf,fields):
  global apihandle,con
  if lookupType == 'genre':
    lookupGenre(conf,fields)
  if len(lookupType)>8 and lookupType[:7] == 'whattop':
    lookupTopAll(conf,fields,int(lookupType[7:]))
  else:
    print("Error: didn't find a lookup type")
    exit(1)

def lookupGenre(conf,fields):
  global apihandle,con
  genres = [x for lst in con.db.prepare("SELECT genre,popularity FROM genres ORDER BY popularity DESC LIMIT 300").chunks() for x in lst]
  shuffle(genres)
  for genre in genres:
    for x in downloadGenreData(genre):
      con.printRes(processInfo(x),fields)

def lookupTopAll(conf,fields,n):
  global apihandle,con
  whatTop10 = apihandle.request("top10",limit=n)
  if whatTop10['status'] == 'success':
    for response in whatTop10['response'][::-1]:
      print("Downloading "+response["caption"])
      for result in processedTorsWithInfo(response['results']):
        con.printRes(result,fields)

def main():
  global apihandle,con
  credentials = getCreds()
  db = startup_tests(sys.argv,credentials)
  conf = getConfig()
  cookies = {'cookies':pickle.load(open('config/.cookies.dat', 'rb'))} if os.path.isfile('config/.cookies.dat') else {}
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], **cookies)
  con = databaseCon(db)
  fields = con.getFieldsDB()
  lookupAll(sys.argv[1],conf,fields)
  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))


if  __name__ == '__main__':
  main()

  