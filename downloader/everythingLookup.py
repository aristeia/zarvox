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

def downloadGenreData(genre):
  global apihandle
  whatPages=[]
  popularity = ceil(genre[1]*20)+1
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
    except Exception:
      print("Failed to get torrentgroup from what")
  print("Out of this group, ", str(len(what_info)), "good downloads")
  return [processInfo(x) for x in what_info]

def processData(group):
  if notBadArtist(group) and group['releaseType']!='Compilation':
    return getTorrentMetadata(group)
  return {}

def processInfo(metadata):
  global apihandle,con
  res = {}
  artist = artistLookup(metadata['artist'], apihandle, True, con)
  res['artist'] = con.getArtistDB(artist,True)
  print("Done with artist")
  album = albumLookup(metadata,apihandle,con)
  res['album'] = con.getAlbumDB( album,True,res['artist'][0]['select'][0])
  print("Done with album")
  
  abgenres = con.getGenreDB( [x for x,_ in album.genres.items()], apihandle,'album_',True)
  argenres = con.getGenreDB( [x for x,_ in artist.genres.items()], apihandle,'artist_',True)
  res['genre'] = abgenres+argenres
  album.genres = correctGenreNames(album.genres,abgenres)
  artist.genres = correctGenreNames(artist.genres,argenres)
  print("Done with genres")

  res['album_genre'] = con.getAlbumGenreDB( album.genres, True,res['album'][0]['select'])
  res['artist_genre'] = con.getArtistGenreDB( artist.genres, True,res['artist'][0]['select'])
  
  print("Done with artist/album genres")
  res['similar_artist'], res['other_artist'], res['other_similar'] = con.getSimilarArtistsDB(artist.similar_artists, apihandle, res['artist'][0]['select'],True)
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
  genres = list(con.db.prepare("SELECT genre,popularity FROM genres ORDER BY popularity DESC LIMIT 300").chunks())[0]
  shuffle(genres)
  print(genres)
  for genre in genres:
    for x in downloadGenreData(genre):
      con.printRes(processInfo(x),fields)

def lookupTopAll(conf,fields,n):
  global apihandle,con
  whatTop10 = apihandle.request("top10",limit=n)
  if whatTop10['status'] == 'success':
    for response in whatTop10['response']:
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

  