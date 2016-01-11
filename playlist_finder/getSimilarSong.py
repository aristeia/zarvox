import numpy as np, sys,os, postgresql as pg, bisect
from random import random 
from math import ceil,floor, sqrt
sys.path.append("packages")
from libzarv import *
from statistics import mean
from bisect import insort
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



def getitem(albums_query):
  mysum = 0
  breakpoints = [] 
  for res in albums_query:
    mysum += res[0]
    breakpoints.append(mysum)
  score = random() * mysum
  i = bisect.bisect(breakpoints, score)
  return albums_query[i] 


class playlistBuilder:

  album_history = []
  artist_history = []
  albums = {}
  artists = {}
  genres = {}
  genre_pop_rvar = None
  albums_pop_rvar = None
  artists_pop_rvar = None
  
  def __init__(self, db, percentile):
    self.selectAlbum = db.prepare("SELECT albums.album_id,albums.album,artists.artist FROM albums LEFT JOIN artists_albums ON artists_albums.album_id = albums.album_id LEFT JOIN artists on artists.artist_id = artists_albums.artist_id WHERE albums.album_id = $1")
    self.selectTopGenres = db.prepare("SELECT genres.genre, album_genres.similarity from genres LEFT JOIN album_genres on album_genres.genre_id = genres.genre_id WHERE album_genres.album_id = $1 ORDER BY 2 DESC LIMIT 3")
    self.getAlbumGenre = db.prepare("SELECT genre_id, similarity FROM album_genres WHERE album_id= $1")
    self.getArtistGenre = db.prepare("SELECT genre_id, similarity FROM artist_genres WHERE artist_id= $1")
    self.getGenrePop = db.prepare("SELECT 1-genres.popularity FROM genres WHERE genre_id= $1")
    self.getCurrentArtists = db.prepare("SELECT artist_id FROM artists_albums WHERE album_id = $1")
    self.getAlbumsArtists =  db.prepare("SELECT albums.album_id, albums.popularity, artists.artist_id, artists.popularity FROM artists_albums LEFT JOIN artists ON artists.artist_id = artists_albums.artist_id LEFT JOIN albums on albums.album_id=artists_albums.album_id")
    self.totalAlbums = sum([int(x[0]) for lst in db.prepare("SELECT COUNT(*) FROM albums").chunks() for x in lst])
    self.genres_sim = db.prepare("SELECT similarity FROM similar_genres where genre1_id=$1 and genre2_id=$2")
    self.artists_sim = db.prepare("SELECT similarity FROM similar_artists where artist1_id=$1 and artist2_id=$2")
    self.genreName = db.prepare("SELECT genre from genres where genre_id = $1")
    self.percentile = percentile
    print("Going to pick things from top "+str(round(percentile*self.totalAlbums))+" albums")

  def weighArtistAlbum(artist, album):
    return 1.0-(((2.0*album)+artist)/3.0)

  def calcMediaWeight(self, tpe, type_id):
    try:
      history = eval('self.'+tpe+'_history')
    except Exception as e:
      print(e)
      return 0
    if type_id not in history:
      return 1
    else:
      i = history.index(type_id)
      return max(0.5 - (2** (-len(history)+1+i)), 0)

  def querySim(self,things_str, thing1, thing2):
    things = eval('self.'+things_str)
    thing_sim = eval('self.'+things_str+'_sim')
    if thing2 > thing1:
      temp = thing1
      thing1 = thing2
      thing2 = temp
    if thing1 in things:
      if thing2 in things[thing1]['sim']:
        return things[thing1]['sim'][thing2]
    else:
      things[thing1] = {}
      things[thing1]['sim'] = {}
    things[thing1]['sim'][thing2] = sum([x if x is not None else 0 for lst in thing_sim(thing1,thing2) for x in lst])
    return things[thing1]['sim'][thing2]

  def closeness(self, other, this, genres_vals, genres_pops, means):
    tot_genres = sum(list(other.values()))
    if len(other) == 0 or tot_genres == 0:
      return 0
    ingenres = [(key,val) for key,val in other.items() if key in this]
    outgenres = [(key,means[key]) for key in this.keys() if key not in ingenres]
    total=0
    for key,val in ingenres+outgenres:
      total+=(1-abs(val-this[key]))*this[key]#*self.genre_pop_rvar.cdf(self.genre_pops[key])
    # for key,val in outgenres:
    #   total+=(1-abs(val-this[key]))*self.albums[this]['genres'][key]#*self.genre_pop_rvar.cdf(self.genre_pops[key])
      '''closenessGenres = []
      for key2, val2 in other.items():
        closenessGenres.append((self.querySim('genres', key1, key2), val2, key2))
      sim, val, key = max(closenessGenres)
      if sim>0:
        # print("Out of "+(','.join([x[0][0] for lst in map(self.genreName.chunks, other.keys()) for x in lst] ))+', '+str(list(self.genreName.chunks(key))[0][0][0])+' is closest to '+str(list(self.genreName.chunks(key1))[0][0][0]))
        total += (1-min(abs(val1-val)/sim, 1))*genres[key1]*self.genre_pop_rvar.cdf(self.genre_pops[key1])'''

    return (total/genres_vals)#/genres_pops


  def getNextAlbum(self,album_id):
    artist_ids = [x[0] for lst in self.getCurrentArtists.chunks(album_id) for x in lst]
    album_artists = []
    if len(self.albums) == 0 or len(self.artists) == 0:
      for lst in self.getAlbumsArtists.chunks():
        for album, albumpop, artist, artistpop in lst:
          if album not in self.albums:
            self.albums[album] = {
              'pop':albumpop, 
              'artists':[artist]
            }
          else:
            self.albums[album]['artists'].append(artist)
          if artist not in self.artists:
            self.artists[artist] = {}
            self.artists[artist]['sim'] = {}
          self.artists[artist]['pop'] = artistpop
          if album_id == album:
            album_artists.append(artist)
    else:
      album_artists = self.albums[album_id]['artists'][:]

    self.album_history.append(album_id)
    for x in album_artists:
      self.artist_history.append(x)

    if self.albums_pop_rvar is None:
      self.albums_pop_rvar = norm(*norm.fit([x['pop'] for x in self.albums.values()]))
    if self.artists_pop_rvar is None:
      self.artists_pop_rvar = norm(*norm.fit([x['pop'] for x in self.artists.values()]))
    
    if len(album_artists)==0:
      print("Error: no album found")
      exit(1)

    album_pop_max = self.albums_pop_rvar.cdf(self.albums[album_id]['pop'])**(-1)
    artist_pop_max = self.artists_pop_rvar.cdf(max([self.artists[x]['pop'] for x in album_artists]))**(-1)

    # print("Got all of current album information from database")


    #figure out how close its genres are to current album's genres
    # album_genres = dict([x for lst in self.getAlbumGenre.chunks(album_id) for x in lst if x[1]>0])
    for album in self.albums.keys():
      self.albums[album]['genres'] = dict([x for lst in self.getAlbumGenre.chunks(album) for x in lst if x[1]>0])
    album_genres_vals = sum(self.albums[album_id]['genres'].values())
    
    for key in self.albums[album_id]['genres']:
      if key not in self.genres:
        self.genres[key] = {}
        self.genres[key]['sim'] = {}
        self.genres[key]['pop'] = sum([x for lst in self.getGenrePop(key) for x in lst if x is not None])

    album_genres_means = {}
    for k in self.albums[album_id]['genres']:
      lst = [al['genres'][k] for al in self.albums.values() if k in al['genres']]
      if len(lst)>0:
        album_genres_means[k] = mean(lst)
      else:
        album_genres_means[k] = 0
    # print("Got all of possible album information from database")


    #figure out how close its genres are to current artists genres
    artists_genres = []
    mean_sim_rvar = []
    for y in self.artists.keys():
      self.artists[y]['genres'] = dict([x for lst in self.getArtistGenre.chunks(y) for x in lst if x[1]>0])
      if y in album_artists:
        artists_genres.extend(list(self.artists[y]['genres'].keys()))
      for this_artist in album_artists:
        other_sim = []
        if this_artist != y:
          other_sim.append(self.querySim('artists', y, this_artist))
        if len(other_sim) > 0:
          self.artists[y]['mean_sim'] = mean(other_sim)
        else:
          self.artists[y]['mean_sim'] = 0
        mean_sim_rvar.append(self.artists[y]['mean_sim'])
    mean_sim_rvar = norm(*norm.fit(mean_sim_rvar))
    artist_genres = {}
    for key in set(artists_genres):
      artist_genres[key] = mean([self.artists[a]['genres'][key] for a in album_artists if key in self.artists[a]['genres']])
    
    artist_genres_vals = sum(artist_genres.values())
    
    artist_genres_means = {}
    for k in artist_genres.keys():
      lst = [self.artists[a]['genres'][key] for a in self.artists.keys() if key in self.artists[a]['genres']]
      if len(lst)>0:
        artist_genres_means[k] = mean(lst)
      else:
        artist_genres_means[k] = 0

    for key in artist_genres.keys():
      if key not in self.genres:
        self.genres[key] = {}
        self.genres[key]['sim'] = {}
        self.genres[key]['pop'] = sum([x for lst in self.getGenrePop(key) for x in lst if x is not None])
    # print("Got all of possible artist information from database")
    

    self.genre_pop_rvar = norm(*norm.fit([val['pop'] for val in self.genres.values()]))
    artist_genres_pops = sum([self.genre_pop_rvar.cdf(self.genres[x]['pop']) for x in artist_genres.keys()])
    album_genres_pops = sum([self.genre_pop_rvar.cdf(self.genres[x]['pop']) for x in self.albums[album_id]['genres']])


    for album,vals in self.albums.items():
      self.albums[album]['quality'] = self.closeness(
        self.albums[album]['genres'], 
        self.albums[album_id]['genres'], 
        album_genres_vals, album_genres_pops, album_genres_means)
      for artist in self.albums[album]['artists']:
        if 'quality' not in self.artists[artist]:
          quality = []
          for tempartist in self.albums[album_id]['artists']:
            quality.append(
              self.closeness(
                self.artists[artist]['genres'], 
                self.artists[tempartist]['genres'], 
                artist_genres_vals, artist_genres_pops, artist_genres_means))
          self.artists[artist]['quality'] = mean(quality)
    # print("Processed all of possible album/artist information from database")

    totalGenres = len(self.albums[album_id]['genres'])+len(artist_genres)
    albumWeight, artistWeight = len(artist_genres)/totalGenres, len(self.albums[album_id]['genres'])/totalGenres

    albums_query = []
    for album,vals in self.albums.items():
      self.albums[album]['quality'] = (
          (albumWeight*self.calcMediaWeight('album',album)*vals['quality'])
          +mean([(artistWeight*self.calcMediaWeight('artist',ar)*self.artists[ar]['quality']) for ar in vals['artists']])
          +mean([mean_sim_rvar.cdf(self.artists[ar]['mean_sim']) for ar in vals['artists']])
          + 0.25*max(1, album_pop_max*vals['pop'])
          + 0.25*mean([max(1, artist_pop_max*self.artists[ar]['pop']) for ar in vals['artists']]))
      insort(albums_query,(self.albums[album]['quality'],album))

    for i in range(0,len(albums_query)-1-floor(self.percentile*self.totalAlbums)):
      albums_query.pop(0)

    rvar = norm(*norm.fit([x[0] for x in albums_query if x[0]>0]))

    albums_query = [(x[1],sqrt(rvar.cdf(x[0]))) for x in albums_query]

    print("Here are possibilities left:")
    for album in albums_query:
      print(album[1])
      self.printAlbumInfo(album[0])

    next_album = getitem(albums_query)

    return next_album[0]

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
          NOT WORKING: (3a)pop as a 1-float of how good on chi2
          (3b)adherence as a float of how close 
          for each genre in current and other, 
            take difference in adh,
            return 1-result as product with adh and pop
          NOT WORKING: else, for each genre in current not in other
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
  current_playlist = playlistBuilder(db, 0.0025)
  album_id = int(sys.argv[1])
  current_playlist.printAlbumInfo(album_id)

  for track in range(12):
    album_id = current_playlist.getNextAlbum(album_id)
    print("done")
    current_playlist.printAlbumInfo(album_id)

   
    



if  __name__ == '__main__':
  main()
