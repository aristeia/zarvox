import numpy as np, sys,os, postgresql as pg, bisect
from random import random 
from math import ceil
sys.path.append("packages")
from libzarv import *

def startup_tests():
  #Check sys.argv for path_to_album
  if len(sys.argv) != 2:
    print("Error: postprocessor received wrong number of args")
    exit(1)
  try:
    credentials = getCreds()
    db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_passwd']+'@localhost/'+credentials['db_name'])
  except Exception:
    print("Error: cannot connect to database\n")
    exit(1)
  print("Zarvox database are online")
  return db


def weighArtistAlbum(artist, album):
  return 1.0-(((2.0*album)+artist)/3.0)

def main():
  db = startup_tests()
  
  album_id = int(sys.argv[1])
  artist_id = list(db.prepare("SELECT artist_id FROM ALBUMS WHERE album_id = $1").chunks(album_id))[0][0][0]
  
  album_list = list(db.prepare("SELECT album_id, artist_id FROM albums WHERE artist_id != $1 ORDER BY album_id").chunks(artist_id))[0]
  artist_list = []
  [artist_list.append(x[1]) for x in album_list if x[1] not in artist_list]

  getAlbumGenre = db.prepare("SELECT similarity FROM getAlbumGenres($1)")
  getArtistGenre = db.prepare("SELECT similarity FROM getArtistGenres($1)")
  
  album_genres = [x[0] for x in list(getAlbumGenre.chunks(album_id))[0]]
  albumCloseness = (lambda x:
    sum([abs(a-b) for a,b in zip(album_genres,x)]))
  
  artist_genres = [x[0] for x in list(getArtistGenre.chunks(artist_id))[0]]
  artistCloseness = (lambda x:
    sum([abs(a-b) for a,b in zip(artist_genres,x)]))
  
  albums_query = [( album_pair[0], 
    albumCloseness([x[0] for x in list(getAlbumGenre.chunks(album_pair[0]))[0]]), 
    album_pair[1]) 
  for album_pair in album_list]

  artist_list = dict([(y, artistCloseness([x[0] for x in list(getArtistGenre.chunks(y))[0]])) for y in artist_list])
  albums_query = [(a,b,artist_list[c]) for a,b,c in albums_query]

  albumsMax = max([x[1] for x in albums_query])
  artistsMax = max([x[2] for x in albums_query])
 
  albums_query = [(x[0],weighArtistAlbum((x[2])/artistsMax, (x[1])/albumsMax )) for x in albums_query] 

  albums_query.sort(key=lambda x:x[1], reverse=True)
  albums_query = albums_query[0:ceil(len(albums_query)/50.0)]
  print(albums_query)
  mysum = 0
  breakpoints = [] 
  for res in albums_query:
      mysum += res[1]
      breakpoints.append(mysum)

  def getitem():
      score = random() * breakpoints[-1]
      i = bisect.bisect(breakpoints, score)
      return albums_query[i] 

  print(list(db.prepare("SELECT album_id,album FROM albums WHERE album_id = $1").chunks(getitem()[0]))[0][0])



if  __name__ == '__main__':
  main()