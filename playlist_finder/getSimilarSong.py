import numpy as np, sys,os, postgresql as pg, bisect
from random import random 
from math import ceil
sys.path.append("packages")
from libzarv import *
from statistics import mean
from scipy.stats import chi2, norm

def startup_tests():
  #Check sys.argv for id_to_album
  if len(sys.argv) != 2:
    print("Error: postprocessor received wrong number of args")
    exit(1)
  try:
    credentials = getCreds()
    db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_password']+'@localhost/'+credentials['db_name'])
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
  selectAlbum = db.prepare("SELECT albums.album_id,albums.album,artists.artist FROM albums LEFT JOIN artists_albums ON artists_albums.album_id = albums.album_id LEFT JOIN artists on artists.artist_id = artists_albums.artist_id WHERE albums.album_id = $1")
  selectGenres = db.prepare("SELECT genres.genre, album_genres.similarity from genres LEFT JOIN album_genres on album_genres.genre_id = genres.genre_id WHERE album_genres.album_id = $1 ORDER BY 2 DESC LIMIT 3")
  for track in range(10):
    res = [str(x) for lst in db.prepare("SELECT albums.album_id,albums.album,artists.artist FROM albums LEFT JOIN artists_albums ON artists_albums.album_id = albums.album_id LEFT JOIN artists on artists.artist_id = artists_albums.artist_id WHERE albums.album_id = $1").chunks(album_id) for item in lst for x in item]

    print(' - '.join(res))
    print('    Top Genres: '+(', '.join([x[0] for lst in db.prepare("SELECT genres.genre, album_genres.similarity from genres LEFT JOIN album_genres on album_genres.genre_id = genres.genre_id WHERE album_genres.album_id = $1 ORDER BY 2 DESC LIMIT 3").chunks(album_id) for x in lst])))

    artist_ids = [x[0] for lst in db.prepare("SELECT artist_id FROM artists_albums WHERE album_id = $1").chunks(album_id) for x in lst]
    
    album_list = [x for lst in db.prepare("SELECT album_id, artist_id FROM artists_albums ORDER BY album_id").chunks() for x in lst if x[1] not in artist_ids]
    artist_list = list(set(x[1] for x in album_list))

    getAlbumGenre = db.prepare("SELECT * FROM getAlbumGenres($1)")
    getArtistGenre = db.prepare("SELECT * FROM getArtistGenres($1)")
    
    #figure out how close its genres are to current album's genres
    album_genres = dict([x for lst in getAlbumGenre.chunks(album_id) for x in lst])
    album_genres_vals = sum(album_genres.values())
    albums_query = [[ album_pair[0], 
                      dict([x for lst in getAlbumGenre.chunks(album_pair[0]) for x in lst if x[0] in album_genres]), 
                      album_pair[1]]
                    for album_pair in album_list]
    album_genres_means = dict([(k, mean([al[1][k] for al in albums_query if k in al[1]])) for k in album_genres.keys()])
    albumCloseness = (lambda x:
      sum(
        [(1-(x[key]-album_genres[key])**2)*album_genres[key]
        for key in x.keys() 
        if key in album_genres]
        +[(1-(val-album_genres[key])**2)*album_genres[key]
        for key, val in album_genres_means.items()
        if key not in x])
      /album_genres_vals)
    
    #figure out how close its genres are to current artists genres
    artists_genres = [dict([x for lst in getArtistGenre.chunks(artist_id) for x in lst]) for artist_id in artist_ids ]
    artist_genres = dict()
    for key in set([k for d in artists_genres for k in d.keys()]):
      artist_genres[key] = mean([v for d in artists_genres for k,v in d.items() if k==key])
    artist_query = dict([(y, dict([x for lst in getArtistGenre.chunks(y) for x in lst if x[0] in artist_genres])) for y in artist_list])
    artist_genres_means = dict([(k, mean([ar[k] for ar in artist_query.values() if k in ar])) for k in artist_genres.keys()])
    artist_genres_vals = sum(artist_genres.values())
    artistCloseness = (lambda x:
      sum(
        [(1-(x[key]-artist_genres[key])**2)*artist_genres[key]
        for key in x.keys() 
        if key in artist_genres]
        +[(1-(val-artist_genres[key])**2)*artist_genres[key]
        for key, val in artist_genres_means.items()
        if key not in x])
      /artist_genres_vals)

    # for key in artist_query.keys():
    #   artist_query[key] = artistCloseness(key)
    
    for lst in albums_query:
      lst[1] = albumCloseness(lst[1])
      if type(artist_query[lst[2]]) is dict:
        artist_query[lst[2]] = artistCloseness(artist_query[lst[2]])
      lst.append(artist_query[lst[2]])

    albumsMax = max([x[1] for x in albums_query])
    artistsMax = max([x[3] for x in albums_query])
   
    albums_query = [(x[0],(len(album_genres)*x[1])+(len(artist_genres)*x[3])) for x in albums_query] 

    albums_query.sort(key=lambda x:x[1], reverse=True)
    albums_query = albums_query[0:ceil(len(albums_query)/50.0)]

    mysum = 0
    breakpoints = [] 
    for res in albums_query:
        mysum += res[1]
        breakpoints.append(mysum)

    def getitem():
        score = random() * breakpoints[-1]
        i = bisect.bisect(breakpoints, score)
        return albums_query[i] 

    album_id = getitem()[0]
    



if  __name__ == '__main__':
  main()