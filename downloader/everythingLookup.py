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

def startup_tests(args, credentials):
  if len(args) != 2:
    print("Error: postprocessor received wrong number of args")
    exit(1)
  try:
    db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_passwd']+'@localhost/'+credentials['db_name'])
  except Exception:
    print("Error: cannot connect to database\n")
    exit(1)
  print("Zarvox database are online")
  try:
    pingtest(['whatcd'])
  except Exception:
    print(e)
    exit(1)
  print("Pingtest complete; sites are online")
  return db

def downloadGenreData(genre, apihandle):
  whatPages=[]
  popularity = ceil(genre[1]*20)+1
  x=0
  print("Downloading "+str(popularity)+" for "+genre[0])
  while len(whatPages)<popularity:
    x+=1
    time.sleep(5)
    what =apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x),category='Music')
    while what['status'] != 'success':
      time.sleep(10)
      what=apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x),category='Music')
    whatPages+=what['response']['results']
  return processedGroups(whatPages[0:popularity])

def processedGroups(whatPages):
  what_info=[]
  for group in whatPages:
      processedGroup = processData(group)
      if processedGroup != {}:
        what_info.append(processedGroup)
  return what_info

def processData(group):
  if 'artist' in group and group['artist'].lower()!='various artists' and group['releaseType']!='Compilation':
    val = reduce(lambda x,y: compareTors(x,y),group['torrents'])
    artists = [y['name'] for y in val['artists'] if y['name'].lower() in group['artist'].lower()]
    if len(artists) == 1:
      a=artists[0]
    else:
      try:
        newGroup = apihandle.request("torrentgroup",id=group['groupId'])['response']['group']
        artists = [art['name'] for (y,z) in newGroup['musicInfo'].items() for art in z if art['name'].lower() in group['artist'].lower()]
        a=sorted(artists)[0]
      except Exception:
        return {}
    val.update({
      'album':unescape(group['groupName']),
      'artist':unescape(a)
      })
    return val
  return {}

def processInfo(item,con, apihandle):
  metadata = {
    'artist':item['artist'],
    'album':item['album'],
    'whatid':item['torrentId'],
    'path_to_album':''
  }
  res = {}
  artist = artistLookup(item['artist'], apihandle, True, con)
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

def lookupAll(lookupType,conf,apihandle,con,fields):
  if lookupType == 'genre':
    lookupGenre(conf,apihandle,con,fields)
  if len(lookupType)>8 and lookupType[:7] == 'whattop':
    print('wer')
    lookupTopAll(conf,apihandle,con,fields,int(lookupType[7:]))

def lookupGenre(conf,apihandle,con,fields):
  genres = [('samba',0.585190449716531)]#list(con.db.prepare("SELECT genre,popularity FROM genres ORDER BY popularity DESC LIMIT 300").chunks())[0]
  shuffle(genres)
  for genre in genres:
    for x in downloadGenreData(genre,apihandle):
      con.printRes(processInfo(x,con,apihandle),fields)

def lookupTopAll(conf,apihandle,con,fields,n):
  whatTop10 = apihandle.request("top10",limit=n)
  if whatTop10['status'] == 'success':
    for response in whatTop10['response']:
      con.printRes(processInfo(processedGroups(response['results']),con, apihandle),fields)

def main():
  credentials = getCreds()
  db = startup_tests(sys.argv,credentials)
  conf = getConfig()
  cookies = pickle.load(open('config/.cookies.dat', 'rb'))
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
  con = databaseCon(db)
  fields = con.getFieldsDB()
  lookupAll(sys.argv[1],conf,apihandle,con,fields)
  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))


if  __name__ == '__main__':
  main()

  