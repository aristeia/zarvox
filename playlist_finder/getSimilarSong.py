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


def closeness(other, genres, genres_vals):
  tot_genres = sum(list(other.values()))
  if len(other) == 0 or tot_genres == 0:
    return 0
  ingenres = [(key,val) for key,val in other.items() if key in genres]
  outgenres = [(key,val) for key,val in other.items() if key not in genres]
  total = sum([(1-(val-genres[key]))*genres[key]
            for key,val in ingenres])
  # for key1,val1 in genres.items():
  #   if key1 not in ingenres:
  #     thisGenreList = []
  #     for key2, val2 in other.items():
  #       thisGenreList.append(self.queryGenreSim(key1, key2) * val2)
  #     total += (1-(sum(thisGenreList) / tot_genres))*genres[key1]
  return total/genres_vals


def getitem(albums_query):
  mysum = 0
  breakpoints = [] 
  for res in albums_query:
    mysum += res[2]
    breakpoints.append(mysum)
  score = random() * mysum
  i = bisect.bisect(breakpoints, score)
  return albums_query[i] 


class playlistBuilder:

  album_history = []
  artist_history = []
  genre_sim = {}
  
  def __init__(self,db):
    self.selectAlbum = db.prepare("SELECT albums.album_id,albums.album,artists.artist FROM albums LEFT JOIN artists_albums ON artists_albums.album_id = albums.album_id LEFT JOIN artists on artists.artist_id = artists_albums.artist_id WHERE albums.album_id = $1")
    self.selectTopGenres = db.prepare("SELECT genres.genre, album_genres.similarity from genres LEFT JOIN album_genres on album_genres.genre_id = genres.genre_id WHERE album_genres.album_id = $1 ORDER BY 2 DESC LIMIT 3")
    self.getAlbumGenre = db.prepare("SELECT * FROM getAlbumGenres($1)")
    self.getArtistGenre = db.prepare("SELECT * FROM getArtistGenres($1)")
    self.getCurrentArtists = db.prepare("SELECT artist_id FROM artists_albums WHERE album_id = $1")
    self.getAlbums =  db.prepare("SELECT album_id, artist_id FROM artists_albums")
    self.totalAlbums = sum([int(x[0]) for lst in db.prepare("SELECT COUNT(*) FROM albums").chunks() for x in lst])
    self.genre_sim_stm = db.prepare("SELECT similarity FROM similar_genres where genre_id1=$1 and genre_id2=$2")
    print("Going to pick things from top "+str(round(0.01*self.totalAlbums))+" albums")

  def weighArtistAlbum(artist, album):
    return 1.0-(((2.0*album)+artist)/3.0)

  def calcMediaWeight(self, type, type_id):
    try:
      history = eval('self.'+type+'_history')
    except Exception as e:
      print(e)
      return 0
    if type_id not in history:
      return 1
    else:
      i = history.index(type_id)
      return max(0.5 - (2** (-len(history)+1+i)), 0)

  def queryGenreSim(self,genre1, genre2):
    if genre2 > genre1:
      temp = genre1
      genre1 = genre2
      genre2 = temp
    if genre1 in self.genre_sim:
      if genre2 in self.genre_sim[genre1]:
        return self.genre_sim[genre1][genre2]
    else:
      self.genre_sim[genre1] = {}
    self.genre_sim[genre1][genre2] = sum([x if x is not None else 0 for lst in self.genre_sim_stm(genre1,genre2) for x in lst])
    return self.genre_sim[genre1][genre2]


  def getNextAlbum(self,album_id):
    artist_ids = [x[0] for lst in self.getCurrentArtists.chunks(album_id) for x in lst]
    
    album_list = [x for lst in self.getAlbums.chunks() for x in lst if x[1] not in artist_ids]
    artist_list = list(set(x[1] for x in album_list))

    #figure out how close its genres are to current album's genres
    album_genres = dict([x for lst in self.getAlbumGenre.chunks(album_id) for x in lst])
    album_genres_vals = sum(album_genres.values())
    albums_query = [[ album_pair[0], 
                      dict([x for lst in self.getAlbumGenre.chunks(album_pair[0]) for x in lst if x[0] in album_genres]), 
                      album_pair[1]]
                    for album_pair in album_list]
    # album_genres_means = dict([(k, mean([al[1][k] for al in albums_query if k in al[1]])) for k in album_genres.keys()])
    # albumCloseness = (lambda x:
    #   sum(
    #     [(1-(x[key]-album_genres[key]))*album_genres[key]
    #     for key in x.keys() 
    #     if key in album_genres]
    #     +[(1-(val-album_genres[key]))*album_genres[key]
    #     for key, val in album_genres_means.items()
    #     if key not in x])
    #   /album_genres_vals)

    
    #figure out how close its genres are to current artists genres
    artists_genres = [dict([x for lst in self.getArtistGenre.chunks(artist_id) for x in lst]) for artist_id in artist_ids ]
    artist_genres = dict()
    for key in set([k for d in artists_genres for k in d.keys()]):
      artist_genres[key] = mean([v for d in artists_genres for k,v in d.items() if k==key])
    artist_query = dict([(y, dict([x for lst in self.getArtistGenre.chunks(y) for x in lst if x[0] in artist_genres])) for y in artist_list])
    # artist_genres_means = dict([(k, mean([ar[k] for ar in artist_query.values() if k in ar])) for k in artist_genres.keys()])
    artist_genres_vals = sum(artist_genres.values())
    # artistCloseness = (lambda x:
    #   sum(
    #     [(1-(x[key]-artist_genres[key])**2)*artist_genres[key]
    #     for key in x.keys() 
    #     if key in artist_genres]
    #     +[(1-(val-artist_genres[key])**2)*artist_genres[key]
    #     for key, val in artist_genres_means.items()
    #     if key not in x])
    #   /artist_genres_vals)

    # for key in artist_query.keys():
    #   artist_query[key] = artistCloseness(key)
    
    for lst in albums_query:
      lst[1] = closeness(lst[1], album_genres, album_genres_vals)
      if type(artist_query[lst[2]]) is dict:
        artist_query[lst[2]] = closeness(artist_query[lst[2]], artist_genres, artist_genres_vals)
      lst.append(artist_query[lst[2]])

    albums_query = [
      ( x[0],
        x[2],
        (len(album_genres)*self.calcMediaWeight('album',x[0])*x[1])
          +(len(artist_genres)*self.calcMediaWeight('artist',x[2])*x[3])) 
      for x in albums_query] 

    albums_query.sort(key=lambda x:x[2], reverse=True)

    rvar = norm(*norm.fit([x[2] for x in albums_query if x[2]>0]))

    albums_query = [(x[0],x[1],rvar.cdf(x[2])) for x in albums_query[0:ceil(len(albums_query)/round(0.01*self.totalAlbums))]]

    next_album = getitem(albums_query)
    self.album_history.append(next_album[0])
    self.artist_history.append(next_album[1])

    print("Picked an album with "+str(round(next_album[2]*100/mysum,4))+"% likelyhood")

    return next_album

  def calcDistribFunct():
    '''
    Consider our data:

    artists have genres via a sim relation, pop, sim, albums with linear relation
    albums have genres via a sim relation, pop, sim (potentially through genres)
    genres have pop and sim

    Only two types of float comparable data are pop and sim.
    Essentially, we want to quantify a TOTAL sim through the relational sims
      qualified by pop.


    My notes say to calc (1) sim and (2) pop 
      for (1) genres, (2) albums, and (3) artists.
    I think we should flip genres the other dimensional axis because axes
      should reflect linear relation, hence calc:
        (1) sim (just for artists) as a float of how close to current
          multiplied by their pop on a chi2 capped at current
        (2) pop as a float of how good on chi2 capped at current pop at 1
        (3) genres via a sim with
          (3a)pop as a 1-float of how good on chi2
          (3b)adherence as a float of how close 
          for each genre in current and other, 
            take difference in adh,
            return 1-result as product with adh and pop
          else, for each genre in current not in other
            average for each genre in other,
            do normal procedure multiplied by sim to current genre.
      for 
        (1) albums
        (2) artists
      For all sim/pop products, make sure that pop is < sim
      
    '''
    return 0


  def printAlbumInfo(self,album_id):
    res = [str(x) for lst in self.selectAlbum.chunks(album_id) for item in lst for x in item]

    print(' - '.join(res))
    print('    Top Genres: '+(', '.join([x[0] for lst in self.selectTopGenres.chunks(album_id) for x in lst])))



def main():
  db = startup_tests()
  current_playlist = playlistBuilder(db)
  album_id = int(sys.argv[1])
  current_playlist.printAlbumInfo(album_id)

  for track in range(12):
    album_id, artist_id, val = current_playlist.getNextAlbum(album_id)
    current_playlist.printAlbumInfo(album_id)

   
    



if  __name__ == '__main__':
  main()