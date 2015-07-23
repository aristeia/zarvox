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
  genres = list(db.prepare("SELECT genre,popularity FROM genres ORDER BY popularity DESC LIMIT 300").chunks())[0]
  shuffle(genres)
  con = databaseCon(db)
  fields = con.getFieldsDB()
  for genre in genres:
    what_seeders=[]
    popularity = ceil(genre[1]*20)+1
    print("Downloading "+str(popularity)+" for "+genre[0])
    index=0
    for x in range(ceil(popularity/50)):
      time.sleep(5)
      what =apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x+1),category='Music')
      while what['status'] != 'success':
        time.sleep(10)
        what=apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x+1),category='Music')
      for group in what['response']['results']:
        if 'artist' in group and group['artist'].lower()!='various artists' and group['releaseType']!='Compilation':
          val = reduce(lambda x,y: compareTors(x,y),group['torrents'])
          partists = [y['name'] for y in val['artists'] if y['name'].lower() in group['artist'].lower()]
          if len(partists) == 1:
            a=partists[0]
          else:
            try:
              newGroup = apihandle.request("torrentgroup",id=group['groupId'])['response']['group']
              partists = [art['name'] for (y,z) in newGroup['musicInfo'].items() for art in z if art['name'].lower() in group['artist'].lower()]
            except Exception:
              index=popularity
              break
            if len(partists)>0:
              a=sorted(partists)[0]
            else:
              index=popularity
              break
          print(group['artist'].lower(),a)
          val.update({
            'album':unescape(group['groupName']),
            'artist':unescape(a)
            })
          what_seeders.append(val)
          index+=1
        if index == popularity:
          break
      if index == popularity:
        break
    for x in what_seeders:
      metadata = {
        'artist':x['artist'],
        'album':x['album'],
        'whatid':x['torrentId'],
        'path_to_album':''
      }
      res = {}
      artist = artistLookup(x['artist'], con)
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

      con.printRes(res,fields)
  

  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))


if  __name__ == '__main__':
  main()

  