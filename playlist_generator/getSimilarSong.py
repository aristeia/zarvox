import numpy as np, sys,os, postgresql as pg, bisect
sys.path.extend(os.listdir(os.getcwd()))
from random import random 
from math import ceil,floor, sqrt, pow
from libzarv import *
from statistics import mean
from bisect import insort
from scipy.stats import expon, norm

def startup_tests():
  #Check sys.argv for id_to_album
  #if len(sys.argv) != 2:
  #  raise RuntimeError("Error: postprocessor received wrong number of args")
  #  exit(1)
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
  
  def __init__(self, db):
    conf = getConfig()
    self.selectAlbum = db.prepare("SELECT albums.album_id,albums.album,artists.artist,artists.artist_id, albums.folder_path FROM albums INNER JOIN artists_albums ON artists_albums.album_id = albums.album_id INNER JOIN artists on artists.artist_id = artists_albums.artist_id WHERE albums.album_id = $1")
    self.acceptableAlbums = db.prepare('''SELECT DISTINCT temp.* FROM
      (SELECT albums.album_id FROM albums 
      INNER JOIN album_genres ON albums.album_id = album_genres.album_id 
      INNER JOIN genres ON genres.genre_id = album_genres.genre_id 
      WHERE album_genres.similarity > 0.5 AND genres.supergenre = $1
      UNION
      SELECT albums.album_id FROM albums
      INNER JOIN artists_albums ON albums.album_id = artists_albums.album_id 
      INNER JOIN artist_genres ON artists_albums.artist_id = artist_genres.artist_id
      INNER JOIN genres ON genres.genre_id = artist_genres.genre_id
      WHERE artist_genres.similarity > 0.75 AND genres.supergenre = $1) AS temp''')
    self.selectTopGenres = db.prepare("SELECT genres.genre, album_genres.similarity, genres.popularity, genres.genre_id from genres INNER JOIN album_genres on album_genres.genre_id = genres.genre_id WHERE album_genres.album_id = $1 ORDER BY 2 DESC, 3 DESC")
    self.getAlbumGenre = db.prepare("SELECT genre_id, similarity FROM album_genres WHERE album_id= $1")
    self.getArtistGenre = db.prepare("SELECT genre_id, similarity FROM artist_genres WHERE artist_id= $1")
    self.getGenrePop = db.prepare("SELECT 1-genres.popularity FROM genres WHERE genre_id= $1")
    self.getCurrentArtists = db.prepare("SELECT artist_id FROM artists_albums WHERE album_id = $1")
    self.getAlbumsArtists =  db.prepare(
      "SELECT albums.album_id, albums.popularity, albums.playcount, artists.artist_id, artists.popularity, artists.playcount FROM artists_albums INNER JOIN artists ON artists.artist_id = artists_albums.artist_id INNER JOIN albums on albums.album_id=artists_albums.album_id"
      +(" WHERE SUBSTRING(albums.folder_path,1,1) = '/' and albums.album_id IN (select songs.album_id from songs where SUBSTRING(songs.filename,1,1) = '/')" if conf['production'] else "")
      +(" AND albums.playcount>0" if conf['playlistRepeats'] else ""))
    self.totalAlbums = sum([int(x[0]) for lst in db.prepare("SELECT COUNT(*) FROM albums").chunks() for x in lst])
    self.genres_sim = db.prepare("SELECT similarity FROM similar_genres where genre1_id=$1 and genre2_id=$2")
    self.artists_sim = db.prepare("SELECT similarity FROM similar_artists where artist1_id=$1 and artist2_id=$2")
    self.genreName = db.prepare("SELECT genre from genres where genre_id = $1")
    self.percentile = float(conf['percentile'])
    self.totalPlaylists = sum([int(x[0]) for lst in db.prepare("SELECT COUNT(*) FROM playlists").chunks() for x in lst])
    if self.percentile < (self.totalAlbums**(-1)):
      self.percentile = self.totalAlbums**(-1)
    self.sensitivity = conf['sensitivity']
    self.album_history = []
    self.artist_history = []
    self.albums = {}
    self.artists = {}
    self.genres = {}
    self.genre_pop_rvar = None
    self.albums_pop_rvar = None
    self.artists_pop_rvar = None
    print("Going to pick things from top "+str(ceil(self.percentile*self.totalAlbums))+" albums")


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
      return max(pow(0.925, (len(history)-1-i)), 0.375)

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
    things[thing1]['sim'][thing2] = sum([percentValidation(x) 
      for lst in thing_sim(thing1,thing2) 
      for x in lst])
    return things[thing1]['sim'][thing2]

  def closeness(self, obj1_id, obj2_id, tpe):
    try:
      category = eval('self.'+tpe+'s')
    except Exception as e:
      print(e)
      return 0
    if 'genres_vals' not in category[obj2_id]:
      category[obj2_id]['genres_vals'] = sum(category[obj2_id]['genres'].values())
    if len(category[obj1_id]['genres']) == 0:
      return 0
    elif category[obj2_id]['genres_vals'] == 0:
      return 1
    ingenres = [(key,val) for key,val in category[obj1_id]['genres'].items() if key in category[obj2_id]['genres']]
    outgenres = [(key,self.genres[key][tpe+'_mean']/2.5) for key in category[obj2_id]['genres'].keys() if key not in ingenres]
    total=0
    for key,val in ingenres+outgenres:
      total+=(1-abs(val-category[obj2_id]['genres'][key]))*category[obj2_id]['genres'][key]#*float(self.genre_pop_rvar.cdf(self.genres[key]['pop']))
    # for key,val in outgenres:
    #   total+=(1-abs(val-this[key]))*self.albums[this]['genres'][key]#*self.genre_pop_rvar.cdf(self.genre_pops[key])
      '''closenessGenres = []
      for key2, val2 in other.items():
        closenessGenres.append((self.querySim('genres', key1, key2), val2, key2))
      sim, val, key = max(closenessGenres)
      if sim>0:
        # print("Out of "+(','.join([x[0][0] for lst in map(self.genreName.chunks, other.keys()) for x in lst] ))+', '+str(list(self.genreName.chunks(key))[0][0][0])+' is closest to '+str(list(self.genreName.chunks(key1))[0][0][0]))
        total += (1-min(abs(val1-val)/sim, 1))*genres[key1]*self.genre_pop_rvar.cdf(self.genre_pops[key1])'''
    return (total/category[obj2_id]['genres_vals'])#/genres_pops

  def fillAlbumsArtistsCache(self, album_id, filterGenre = ''):
    album_artists = []
    if filterGenre != '':
      acceptable = [x[0] for lst in self.acceptableAlbums.chunks(filterGenre) for x in lst]
    for lst in self.getAlbumsArtists.chunks():
      for album, albumpop, albumplays, artist, artistpop, artistplays in lst:
        if album in acceptable:
          if album not in self.albums:
            self.albums[album] = {
              'pop':albumpop, 
              'plays':albumplays, 
              'artists':[artist],
              'genres': dict([(x[0],percentValidation(x[1])) for lst in self.getAlbumGenre.chunks(album) for x in lst])
            }
            for k in self.albums[album]['genres']:
              if k not in self.genres:
                self.genres[k] = {}
                self.genres[k]['sim'] = {}
              if 'pop' not in self.genres[k]:
                self.genres[k]['pop'] = sum([float(x) for lst in self.getGenrePop(k) for x in lst if x is not None])
              if 'album_mean' not in self.genres[k]:
                lst = [al['genres'][k] for al in self.albums.values() if k in al['genres']]
                if len(lst)>0:
                  self.genres[k]['album_mean'] = mean(lst)
                else:
                  self.genres[k]['album_mean'] = 0
          else:
            self.albums[album]['artists'].append(artist)
          if artist not in self.artists:
            self.artists[artist] = {}
            self.artists[artist]['sim'] = {}
          self.artists[artist]['pop'] = artistpop
          self.artists[artist]['plays'] = artistplays
          if album_id == album:
            album_artists.append(artist)
    return album_artists


  def getNextAlbum(self,album_id):
    # artist_ids = [x[0] for lst in self.getCurrentArtists.chunks(album_id) for x in lst]
    if len(self.albums) == 0 or len(self.artists) == 0:
      album_artists = self.fillAlbumsArtistsCache(album_id)
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
    # print("Got all of current album information from database")


    #figure out how close its genres are to current album's genres
    # album_genres = dict([x for lst in self.getAlbumGenre.chunks(album_id) for x in lst if x[1]>0])
    # for album in self.albums.keys():
    #   self.albums[album]['genres'] = dict([(x[0],percentValidation(x[1])) for lst in self.getAlbumGenre.chunks(album) for x in lst])
    self.albums[album_id]['genres_vals'] = sum(self.albums[album_id]['genres'].values())
    
    # print("Got all of possible album information from database")


    #figure out how close its genres are to current artists genres
    mean_sim_rvar = []
    for y in self.artists.keys():
      self.artists[y]['genres'] = dict([x for lst in self.getArtistGenre.chunks(y) for x in lst if x[1]>0])
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

    for artist in album_artists:
      self.artists[artist]['genres_vals'] = sum(self.artists[artist]['genres'].values())
      for k in self.artists[artist]['genres'].keys():
        if k not in self.genres:
          self.genres[k] = {}
          self.genres[k]['sim'] = {}
        if 'pop' not in self.genres[k]:
          self.genres[k]['pop'] = sum([float(x) for lst in self.getGenrePop(k) for x in lst if x is not None])
        if 'artist_mean' not in self.genres[k]:
          lst = [self.artists[a]['genres'][k] for a in self.artists.keys() if k in self.artists[a]['genres']]
          if len(lst)>0:
            self.genres[k]['artist_mean'] = mean(lst)
          else:
            self.genres[k]['artist_mean'] = 0

   # print("Got all of possible artist information from database")
    

    self.genre_pop_rvar = norm(*norm.fit([val['pop'] for val in self.genres.values()]))
    for artist in album_artists:
      self.artists[artist]['genres_pop']  = sum([self.genre_pop_rvar.cdf(self.genres[x]['pop']) for x in self.artists[artist]['genres'].keys()])
    self.albums[album_id]['genres_pop'] = sum([self.genre_pop_rvar.cdf(self.genres[x]['pop']) for x in self.albums[album_id]['genres'].keys()])

    for things in [self.albums, self.artists]:
      for thing in things.keys():
        things[thing]['quality'] = 0

    for otherAlbum,vals in self.albums.items():
      for currentAlbum in self.album_history:
        if currentAlbum != otherAlbum:
          self.albums[otherAlbum]['quality'] += self.closeness(
            otherAlbum, 
            currentAlbum,
            'album') * self.calcMediaWeight('album', currentAlbum)
      for otherArtist in self.albums[otherAlbum]['artists']:
        if self.artists[otherArtist]['quality'] == 0:
          for currentArtist in self.artist_history:
            if currentArtist != otherArtist:
              self.artists[otherArtist]['quality'] += self.closeness(
                otherArtist,
                currentArtist, 
                'artist') * self.calcMediaWeight('artist', currentArtist)
    # print("Processed all of possible album/artist information from database")

    album_pop_max = percentValidation(
      self.albums_pop_rvar.cdf(
        mean([
          self.albums[album]['pop']
          for album in self.album_history]))**(-1))
    artist_pop_max = percentValidation(
      self.artists_pop_rvar.cdf(
        mean([
          self.artists[artist]['pop']
          for artist in self.artist_history]))**(-1))

    albums_query = []
    for album,vals in self.albums.items():
      if (album not in self.album_history[-min(10, len(self.album_history)):]
        and all([artist not in self.artist_history[-min(5, len(self.artist_history)):] for artist in vals['artists']])):
        self.albums[album]['quality'] = (
          (self.sensitivity["albumGenreSimilarity"]*self.calcMediaWeight('album',album)*vals['quality'])
          +self.sensitivity["artistGenreSimilarity"]*mean([(self.calcMediaWeight('artist',ar)*self.artists[ar]['quality']) for ar in vals['artists']])
          +self.sensitivity["artistSimilarity"]*mean([percentValidation(mean_sim_rvar.cdf(self.artists[ar]['mean_sim'])) for ar in vals['artists']])
          +self.sensitivity["albumPopularity"]*max(1, album_pop_max*vals['pop'])
          +self.sensitivity["artistPopularity"]*mean([max(1, artist_pop_max*self.artists[ar]['pop']) for ar in vals['artists']]))
        if self.totalPlaylists > 0:
          self.albums[album]['quality'] *= (1 - (mean([self.albums[album]['plays'],
            sum([self.artists[ar]['plays'] for ar in vals['artists']])]) / self.totalPlaylists)) ** ceil(self.totalPlaylists/10)
        insort(albums_query,(self.albums[album]['quality'],album))

    for i in range(0,len(albums_query)-1-floor(self.percentile*self.totalAlbums)):
      albums_query.pop(0)

    rvar = norm(*norm.fit([x[0] for x in albums_query if x[0]>0]))

    albums_query = [(x[1],sqrt(rvar.cdf(x[0]))) for x in albums_query]

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
          multiplied by their pop on a expon capped at current
        (2) pop as a float of how good on expon capped at current pop at 1
        (3) genres via a sim with
          NOT WORKING: (3a)pop as a 1-float of how good on expon
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


  def printAlbumInfo(self, album_id):
    res = [item for lst in self.selectAlbum.chunks(album_id) for item in lst]
    artists, album = ','.join([r[2] for r in res]), res[0][1]
    genres = [x[0] for lst in self.selectTopGenres.chunks(album_id) for x in lst]
    print('>>> '+artists + ' - ' + album+' <<<')
    print('    Top Genres: '+(', '.join(genres[:min(3,len(genres))])))
    return album, [r[2] for r in res], res[0][-1]


  def blacklistAlbum(self, album_id):
    if album_id in self.album_history:
      self.album_history.remove(album_id)
      if album_id in self.albums:
        for artist_id in self.albums[album_id]['artists']:
          if artist_id in self.artist_history:
            if all([artist_id not in self.albums[album]['artists'] for album in self.album_history]):
              self.artist_history.remove(artist_id)
    if album_id in self.albums:
      self.albums.pop(album_id)


def main():
  db = startup_tests()
  current_playlist = playlistBuilder(db)
  album_id = int(sys.argv[1])
  current_playlist.printAlbumInfo(album_id)

  for track in range(12):
    album_id = current_playlist.getNextAlbum(album_id)
    current_playlist.printAlbumInfo(album_id)

   
    



if  __name__ == '__main__':
  main()
