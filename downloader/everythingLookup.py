import os,sys,whatapi,postgresql as pg
sys.path.append("packages")
from random import shuffle
from lookup import *
from libzarv import *
from urllib import parse
from html import unescape
from libzarvclasses import *
from database import databaseCon

#Download the top whatcd & lastfm & spotify albums' metadata via lookup
#Calc their downloadability and set that into db

def startup_tests(credentials):
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


def main():
  credentials = getCreds()
  db = startup_tests(credentials)
  conf = getConfig()
  cookies = pickle.load(open('config/.cookies.dat', 'rb'))
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
  genres = list(db.prepare("SELECT genre,popularity FROM genres").chunks())[0]
  shuffle(genres)
  fields = {
    'album':db.prepare("SELECT * FROM albums LIMIT 1").column_names,
    'artist':db.prepare("SELECT * FROM artists LIMIT 1").column_names,
    'genre':db.prepare("SELECT * FROM genres LIMIT 1").column_names,
    'album_genre':db.prepare("SELECT * FROM album_genres LIMIT 1").column_names
    }
  con = databaseCon(db)
  for genre in genres:
    print("Downloading for "+genre[0])
    what_seeders=[]
    for x in range(1):
      for group in apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x+1))['response']['results']:
        if 'artist' in group:
          val = reduce(lambda x,y: compareTors(x,y),group['torrents'])
          val.update({'album':unescape(group['groupName']),'artist':unescape(group['artist'])})
          what_seeders.append(val)
    for x in what_seeders:
      metadata = {
        'artist':x['artist'],
        'album':x['album'],
        'whatid':x['torrentId'],
        'path_to_album':''
      }
      print("Done with init bs")
      artist = artistLookup(x['artist'])
      dbartist = con.getArtistDB(artist,True)
      print("got artist")
      album = albumLookup(metadata,apihandle,con)
      dbalbum = con.getAlbumDB( album,True,dbartist[0]['select'][0])
      print("got album")
      dbgenres = con.getGenreDB( [x for x,_ in album.genres.items()], apihandle,'album_',True)
      dbalbumgenres = con.getAlbumGenreDB( album.genres, True,dbalbum[0]['select'])
      con.printOneRes("Artist",dbartist,fields['artist'])
      con.printOneRes("Album",dbalbum,fields['album'])
      con.printOneRes("Genre",dbgenres,fields['genre'])
      con.printOneRes("Album Genre",dbalbumgenres,fields['album_genre'])
  

  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))


if  __name__ == '__main__':
  main()

  