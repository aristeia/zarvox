import sys,os,postgresql,time
sys.path.append("packages")
from lookup import artistLookup
from libzarv import *
from libzarvclasses import *
import pickle
import whatapi
from urllib import parse
from functools import reduce
from numpy import float128, array as npar, subtract, isnan
from scipy.stats import norm, expon, kstest
from statistics import mean,median

class databaseCon:


  def __init__(self,d=None):
    if d is None:
      credentials = getCreds()
      d = postgresql.open('pq://'+credentials['db_user']+':'+credentials['db_password']+'@localhost/'+credentials['db_name'])
    self.db=d
    self.db_res = {
      'artist':None
    }

  cachedRVars = {
    'albums': {
      'sp':None,
      'll':None,
      'lp':None,
      'we':None,
      'ws':None,
      'pr':None,
      'kp':None
    },
    'artists': {
      'sp':None,
      'll':None,
      'lp':None,
      'we':None,
      'ws':None,
      'pr':None,
      'kp':None
    }
  }


  def getBestDistribution(self, vals):
    distribs = {
      'norm': [norm(*norm.fit(vals))],
      'expon': [expon(*expon.fit(npar(vals)))]
    }    
    bestDistrib = ('norm', 0)
    for distrib, info in distribs.items():
      info.append(kstest(info[0].rvs(size=3000), distrib)[0])
      if info[1]>bestDistrib[1]:
        bestDistrib = (distrib,info[1])
    distribs['expon'][0] = expon(*expon.fit(npar(vals)-distribs['expon'][0].args[0]))
    return distribs[bestDistrib[0]][0]



  def popularitySingle(self,tablename='albums', spotify_popularity=0,lastfm_listeners=0,lastfm_playcount=0,whatcd_seeders=0,whatcd_snatches=0,pitchfork_rating=0,kups_playcount=0,**lists):
    if 'lists' in lists:
      lists = lists['lists']
    def popularityMetric(metric, val, zero=False):
      if res[metric] is not None:
        if metric in lists:
          metrics = lists[metric]
        else:
          metrics = [x[0] for lst in self.db.prepare("SELECT "+names[metric]+" FROM "+tablename+('' if zero else ' WHERE '+names[metric]+'>0')+" ORDER BY 1;").chunks() for x in lst]
        if len(metrics)>0:
          if 'songs' in tablename and tablename not in self.cachedRVars:
            self.cachedRVars[tablename] = {}
          if metric not in self.cachedRVars[tablename] or self.cachedRVars[tablename][metric] is None:
            self.cachedRVars[tablename][metric] = self.getBestDistribution(metrics)
          metricf = self.cachedRVars[tablename][metric].cdf(val) #customIndex(metrics,val)/len(metrics)
          if isnan(metricf):
            metricf = 0.5
        else:
          metricf = 0
        denominator = float128(sum([y for y in res.values() if y is not None]))
        if denominator > 0:
          metricw = metricf*res[metric]/denominator
          resnew[metric] = metricw if not isnan(metricw) else 0
        else:
          resnew[metric] = 0
      else:
        resnew[metric] = 0
    names = {
      'sp':'spotify_popularity',
      'll':'lastfm_listeners',
      'lp':'lastfm_playcount',
      'we':'whatcd_seeders',
      'ws':'whatcd_snatches',
      'pr':'pitchfork_rating',
      'kp':'kups_playcount'
    }

    res = {
      'sp': None if spotify_popularity==0 else 0.10,
      'll': None if lastfm_listeners==0 else 0.05,
      'lp': None if lastfm_playcount==0 else 0.114765625,
      'we': None if whatcd_seeders==0 else 0.108359375,
      'ws': None if whatcd_snatches==0 else 0.026125,
      'pr': None if pitchfork_rating==0 else 0.24375,
      'kp': 0.375,
    }
    resnew = {}
    popularityMetric('sp',spotify_popularity)
    popularityMetric('ll',lastfm_listeners)
    popularityMetric('lp',lastfm_playcount)
    popularityMetric('we',whatcd_seeders)
    popularityMetric('ws',whatcd_snatches)
    popularityMetric('pr',pitchfork_rating)
    popularityMetric('kp',kups_playcount, zero=True)
    return sum([y for y in resnew.values()])


  def popularity(self,**both):
    def albumsCheck():
      return 'albums' in both and both['albums'] is not None and len(both['albums'])>4
    def artistsCheck():
      return 'artists' in both and both['artists'] is not None and len(both['artists'])>4
    def calcPop(label):
      if 'lists' not in both or label not in both['lists']:
        both['lists'][label] = {}
      ret=0
      totWeight = sum([float128(x[1]) for x in both[label] if not isnan(x[1]) and x[1]<=1 and x[1]>=0])
      for l in both[label]:
        temppop = float128(l[0])#self.popularitySingle(label,*(l[0:7]), lists = both['lists'][label])
        tempamp = float128(l[1]/totWeight)
        ret += (temppop if temppop<=1 and temppop>=0 and not isnan(temppop)  else 0) * (tempamp if not isnan(tempamp) else 0)
      return ret
    if albumsCheck() and artistsCheck():
      album = calcPop('albums')
      artist = calcPop('artists')
      if album>0 and artist>0:
        totalbums = list(self.db.prepare("SELECT COUNT(*) FROM albums;").chunks())[0][0][0]
        totartists = list(self.db.prepare("SELECT COUNT(*) FROM artists;").chunks())[0][0][0]
        print("For genre, album popularity is "+str(album)+" and artist is "+str(artist))
        return (((totalbums / float128(totalbums+totartists))*album) + 
          ((totartists / float128(totalbums+totartists))*artist))
      elif album>0:
        print("arr err")
        return album
      else:
        print("alb err")
        return artist
    elif albumsCheck():
      return calcPop('albums')
    elif artistsCheck() :
      return calcPop('artists')
    else:
      print("Error: received no data to calc popularity of")
      return 0

  def updateGeneralPopularity(self,item,itemtype):
    return self.popularitySingle(itemtype+'s',*item)


  def updateGenrePopularity(self,genre):
    def getAlbums():
      return {'pop': [x[0] for x in list(self.db.prepare("SELECT popularity FROM albums WHERE popularity>0 ORDER BY 1").chunks())[0]]}
    def getArtists():
      return {'pop': [x[0] for x in list(self.db.prepare("SELECT popularity FROM artists WHERE popularity>0 ORDER BY 1").chunks())[0]]}
    try:
      album_sel = self.db.prepare(
        "SELECT albums.popularity, album_genres.similarity FROM albums, album_genres WHERE album_genres.album_id = albums.album_id AND album_genres.genre_id = $1")
      artist_sel = self.db.prepare(
        "SELECT artists.popularity, artist_genres.similarity FROM artists, artist_genres WHERE artist_genres.artist_id = artists.artist_id AND artist_genres.genre_id = $1")
      update_pop = self.db.prepare("UPDATE genres SET popularity = $1 WHERE genre_id=$2")
      albums = list(album_sel.chunks(genre[0]))
      artists = list(artist_sel.chunks(genre[0]))
      albums = albums[0] if len(albums)>0 else None
      artists = artists[0] if len(artists)>0 else None
      print("Updating "+genre[1])
      pop=self.popularity(
          albums=albums,
          artists=artists,
          lists = {'albums': getAlbums() if albums is not None else None, 'artists': getArtists() if artists is not None else None }
        )
      update_pop(pop, genre[0])
    except Exception as e:
      handleError(e,"Error: couldnt update popularity of genre "+genre[1])
    print("Updated "+genre[1]+" with popularity of "+str(pop))


  def updateGenreSimilarity(self,genre1, genre2):
    sim_query = lambda x: self.db.prepare("SELECT 1-AVG(ABS({0}_genres.similarity-agg_table.similarity)) as genreProd FROM {0}_genres INNER JOIN {0}_genres as agg_table ON agg_table.{0}_id = {0}_genres.{0}_id and agg_table.genre_id = $2 WHERE {0}_genres.genre_id = $1".format(x))
    agg_query = lambda x: self.db.prepare("SELECT AVG(agg.genreCount) from (SELECT COUNT(*) as genreCount FROM {0} GROUP BY $1) as agg".format(x))
    weights = {}
    total = 0
    for typeOfSim in ['artist','album']:
      weights[typeOfSim] = sum([float(x[0]) for lst in agg_query(typeOfSim+'s').chunks(typeOfSim+'_id') for x in lst])
      total += weights[typeOfSim]
    double_mval = 2 * mean(weights.values()) / total
    similarity = 0
    for typeOfSim,weight in weights.items():
      weight = double_mval - (weight / total)
      value = sum([x[0] if x[0] is not None and x[0]<=1 and x[0]>=0 and not isnan(x[0]) else 0 for lst in sim_query(typeOfSim).chunks(genre1,genre2) for x in lst])
      # print(typeOfSim,weight,value)
      similarity+=value*weight
    # print("total similarity of "+str(genre1)+" and "+str(genre2)+" is "+str(similarity))
    self.getSimilarGenresDB(genre1, genre2, similarity)
    return similarity


  def selectUpdateInsert(self,data, dtype, **kwargs):
    #kwargs is a dict with following keys:
    #selecting : select_stm, select_args, sargs
    #inserting : insert_stm, insert_args, iargs
    #updating : update_stm, update_args, uargs
    select_stm = self.db.prepare(kwargs['select_stm_str'])
    insert_stm = self.db.prepare(kwargs['insert_stm_str'])
    if 'update_stm_str' in kwargs:
      update_stm = self.db.prepare(kwargs['update_stm_str'])
    results = []
    for datum in data:
      try:
        res = list(select_stm.chunks(*[datum[x] for x in kwargs['select_args']]+(kwargs['sargs'] if 'sargs' in kwargs else [])))
      except Exception as e:
        handleError(e,"Error: cannot select "+ dtype+" in db\n")
      if len(res)==0:
        try:
          insert_stm.chunks(*[datum[x] for x in kwargs['insert_args']]+(kwargs['iargs'] if 'iargs' in kwargs else [])+([kwargs['vals'][datum[x]] for x in kwargs['viargs']] if 'viargs' in kwargs else []))
        except Exception as e:
          handleError(e,"Error: cannot insert "+dtype+" into db.\nArgs were the following:")
          print(*[datum[x] for x in kwargs['insert_args']]+(kwargs['iargs'] if 'iargs' in kwargs else [])+([kwargs['vals'][datum[x]] for x in kwargs['viargs']] if 'viargs' in kwargs else []), file=sys.stderr)
      elif len(res)>1:
        print("Error: more than one results for "+dtype+" select")
      else:
        try:
          if 'update_stm_str' in kwargs:
            update_stm.chunks(*[datum[x] for x in kwargs['update_args']]+(kwargs['uargs'] if 'uargs' in kwargs else [])+([kwargs['vals'][datum[x]] for x in kwargs['viargs']] if 'viargs' in kwargs else []))
        except Exception as e:
          handleError(e,"Error: cannot update "+dtype+" in db")
      db_select = list(select_stm.chunks(*[datum[x] for x in kwargs['select_args']]+(kwargs['sargs'] if 'sargs' in kwargs else [])))[0][0]
      results.append({
        'response':res[0][0] if len(res)>0 else None, 
        'select':db_select
      })
    if kwargs['ret']:
      return results
    self.db_res[dtype] = results


  def getArtistsDB(self, artists, ret=False):
    return self.selectUpdateInsert(
      [artist.__dict__ for artist in artists], 
      'artist',
      ret=ret,
      select_stm_str = "SELECT * FROM artists WHERE artist = $1",
      insert_stm_str = "INSERT INTO artists ( artist, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches,pitchfork_rating,kups_playcount,popularity) VALUES ($1, $2, $3, $4,$5, $6,$7,$8,$9)",
      update_stm_str = "UPDATE artists SET spotify_popularity = $2, lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6,pitchfork_rating = $7, kups_playcount = $8, popularity=$9 WHERE artist = $1",
      select_args = ['name'],
      insert_args = ['name','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches','pitchfork_rating','kups_playcount','popularity'],
      update_args = ['name','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches','pitchfork_rating','kups_playcount','popularity']
      )
  
  def getAlbumDB(self, album, ret=False, db_artistid=None):
    return self.selectUpdateInsert(
      [album.__dict__], 
      'album',
      ret=ret,
      select_stm_str = "SELECT * FROM albums LEFT OUTER JOIN artists_albums on artists_albums.album_id = albums.album_id WHERE albums.album = $1 and artists_albums.artist_id = $2 or artists_albums.artist_id is null",
      insert_stm_str = "INSERT INTO albums ( album, folder_path, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches,pitchfork_rating, kups_playcount, popularity) VALUES ($1, $2, $3, $4, $5, $6, $7, $8,$9, $10)",
      update_stm_str = ("UPDATE albums SET spotify_popularity = $2,lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6,pitchfork_rating = $7, kups_playcount = $8, popularity=$9"
        +(", folder_path = $10" if len(album.filepath)>0 else "")
        +" WHERE album = $1"),
      select_args = ['name'],
      sargs = [self.db_res['artist'][0]['select'][0] if db_artistid is None else db_artistid],
      insert_args = ['name','filepath','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches','pitchfork_rating','kups_playcount','popularity'],
      iargs = [],
      uargs = ([album.filepath] if len(album.filepath)>0 else []),
      update_args = ['name','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches','pitchfork_rating','kups_playcount','popularity']
      )
  
  def getArtistAlbumDB(self, album_id, ret=False, artists_ids=[]):
    return self.selectUpdateInsert(
      [[album_id,artist_id] for artist_id in artists_ids], 
      'artist_album',
      ret=ret,
      select_stm_str = "SELECT * FROM artists_albums WHERE album_id = $1 AND artist_id = $2",
      insert_stm_str = "INSERT INTO artists_albums ( album_id, artist_id) VALUES ($1, $2)",
      # update_stm_str = "UPDATE artists_albums WHERE album = $1",
      select_args = [0,1],
      #sargs = artist_album,
      insert_args = [0,1],
      #iargs = artist_album,
      # update_args = ['album_id','artist_id']
      )

  def getSongsDB(self, songs, ret=False, db_albumid=None):
    return self.selectUpdateInsert(
      [song.__dict__ for song in songs], 
      'song',
      ret=ret,
      select_stm_str = "SELECT * FROM songs WHERE song = $1 AND album_id = $2",
      insert_stm_str = "INSERT INTO songs ( song, filename, length,  explicit, spotify_popularity,lastfm_listeners,lastfm_playcount,kups_playcount, album_id) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)",
      update_stm_str = ("UPDATE songs SET explicit=$2, spotify_popularity =$3,lastfm_listeners = $4,lastfm_playcount = $5,kups_playcount = $6"
      +(", filename = $7" if max([len(song.filename) for song in songs])>0 else "")
        +" WHERE song = $1"),
      select_args = ['name'],
      sargs = [self.db_res['album'][0]['select'][0] if db_albumid is None else db_albumid],
      insert_args = ['name','filename','length','explicit','spotify_popularity','lastfm_listeners','lastfm_playcount','kups_playcount'],
      iargs = [self.db_res['album'][0]['select'][0] if db_albumid is None else db_albumid],
      update_args = (['name','explicit','spotify_popularity','lastfm_listeners','lastfm_playcount','kups_playcount']
      + (['filename'] if max([len(song.filename) for song in songs])>0 else []))
    )

  def getSongsPopDB(self, songs, ret=False, db_albumid=None):
    return self.selectUpdateInsert(
      [song.__dict__ for song in songs], 
      'song',
      ret=ret,
      select_stm_str = "SELECT * FROM songs WHERE song = $1 AND album_id = $2",
      insert_stm_str = "INSERT INTO songs ( song, filename, length,  explicit, spotify_popularity,lastfm_listeners,lastfm_playcount,kups_playcount,popularity, album_id) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
      update_stm_str = "UPDATE songs SET explicit=$2, spotify_popularity =$3,lastfm_listeners = $4,lastfm_playcount = $5,kups_playcount = $6,popularity = $7 WHERE song = $1",
      select_args = ['name'],
      sargs = [self.db_res['album'][0]['select'][0] if db_albumid is None else db_albumid],
      insert_args = ['name','filename','length','explicit','spotify_popularity','lastfm_listeners','lastfm_playcount','kups_playcount','popularity'],
      iargs = [self.db_res['album'][0]['select'][0] if db_albumid is None else db_albumid],
      update_args = ['name','explicit','spotify_popularity','lastfm_listeners','lastfm_playcount','kups_playcount','popularity']
      )


  def getGenreDB(self,genres, apihandle=None,genreParent = '', ret=False):
    results = []
    login=(not apihandle)
    if login:
      credentials = getCreds()
      cookies = pickle.load(open('config/.cookies.dat', 'rb'))
      apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
    select_genre = self.db.prepare("SELECT * FROM genres WHERE genre = $1")
    insert_genre = self.db.prepare("INSERT INTO genres ( genre, supergenre) VALUES ($1,$2)")
    select_blacklist = self.db.prepare("SELECT * FROM genres_blacklist WHERE genre=$1") 
    insert_blacklist = self.db.prepare("INSERT INTO genres_blacklist (genre,permanent) VALUES ($1,$2)")
    update_blacklist = self.db.prepare("UPDATE genres_blacklist SET permanent=True WHERE genre=$1")
    select_supergenre = self.db.prepare("SELECT * FROM genres WHERE supergenre = $1 ORDER BY popularity DESC LIMIT 50")
    for genre in genres:
      db_genre = None
      try:
        res = list(select_genre.chunks(genre))
      except Exception as e:
        handleError(e,"Error: cannot query genre in db")
      if len(res)==0:
        #first check if exists
        blacklist = [x for lst in list(select_blacklist.chunks(genre)) for x in lst]
        if len(blacklist)==0 or not blacklist[0][2]: #Enough to be worth using
          what=apihandle.request("browse",searchstr="",taglist=parse.quote(genre,'.'),order_by='snatched')
          while what['status'] != 'success':
            what=apihandle.request("browse",searchstr="",taglist=parse.quote(genre,'.'),order_by='snatched')
          whatres = what['response']['results']
          snatched = sum(map(lambda x: x['totalSnatched'] if 'totalSnatched' in x else 0, whatres))
          print("Genre "+genre+" has "+str(snatched)+" snatches")
          if snatched>1000 and (genre not in list(map(lambda x:x[1],blacklist)) or (snatched > 10000 and len(blacklist)>0)):
            try:
              if genre in list(map(lambda x:x[1],blacklist)):
                del_blacklist = self.db.prepare("DELETE FROM genres_blacklist WHERE genre_id = $1")
                del_blacklist(blacklist[0][0])
              percentile = (lambda x:
                float(sum([1 for y in whatres if any([z in y['tags'] for z in x])] ))/float(len(whatres)))
              # rock = list(select_supergenre.chunks("rock"))
              # hiphop = list(select_supergenre.chunks("hip.hop"))
              # electronic = list(select_supergenre.chunks("electronic"))
              # alternative = list(select_supergenre.chunks("alternative"))
              # specialty = list(select_supergenre.chunks("specialty"))
              supergenre = reduce( lambda x,y: (x if x[1]>y[1] else y), {
                'loud rock': percentile(['rock','metal','classic.rock','hard.rock','punk.rock','blues.rock','progressive.rock','black.metal','death.metal','hardcore.punk','hardcore','grunge','pop.rock','math.rock']),
                'hip-hop': percentile(['rap','hip.hop','rhythm.and.blues','trip.hop','trap.rap','southern.rap','gangsta','gangsta.rap']),
                'electronic':percentile(['electronic','dub','ambient','dubstep','house','breaks','downtempo','techno','glitch','idm','edm','dance','electro','trance','midtempo','beats','grime','folktronica']),
                'alternative':percentile(['alternative','indie','indie.rock','punk','emo','singer.songwriter','folk','dream.pop','shoegaze','synth.pop','post.punk','chillwave','kpop','jpop','ska','folk.rock','reggae','new.wave','ethereal','instrumental','surf.rock']),
                'specialty':percentile(['experimental','funk','blues','world.music','soul','psychedelic','art.rock','country','classical','baroque','minimalism','minimal','score','disco','avant.garde','afrobeat','post.rock','noise','drone','jazz','dark.cabaret','neofolk','krautrock','improvisation','space.rock','free.jazz'])
              }.items())[0]
              insert_genre(genre,supergenre)
              db_genre = list(select_genre.chunks(genre))[0][0]
            except Exception as e:
              handleError(e,"Error: cannot insert genre "+genre+" into db")
          else:
            print("Genre "+genre+" temporarily in blacklist, won't be changed")
            if snatched < 1000:
              update_blacklist(genre)
              print("Now is permanently in blacklist due to low snatches")
        elif genre not in list(map(lambda x:x[1],blacklist)): #check if misspelling 
          genres = list(self.db.prepare("SELECT genre FROM genres").chunks())
          if len(genres)>0:
            other_genres = list(filter((lambda x: Levenshtein.ratio(x[0],genre)>0.875),genres[0]))
            if len(other_genres)>0:
              ogenre = genre
              genre = reduce(lambda x,y: levi_misc(x,y,genre),map(lambda x:x[0],other_genres))
              db_genre = list(select_genre.chunks(genre))[0][0]
              print("Genre "+ogenre+" is a misspelling of "+db_genre[1])
            else: #add to blacklist
              insert_blacklist(genre,False)
          else: #add to blacklist
            insert_blacklist(genre,False)
        else:
          print("Genre "+genre+" permanently in blacklist, won't be changed")
      elif len(res)>1:
        print("Error: more than one results for genre query",file=sys.stderr)
      else:
        db_genre = res[0][0]
      if db_genre:
        try:
          db_genre = list(select_genre.chunks(genre))[0][0]
        except Exception as e:
          handleError(e,"Error: cannot update the popularity of "+genre+" in db")
        results.append({
        'response':res[0][0] if len(res)>0 else None, 
        'select':db_genre
        })
    if login:
      pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
    self.db_res[genreParent+'genre'] = results
    if ret:
      return results
    self.db_res['genre'] = (self.db_res['genre'] if 'genre' in self.db_res else []) + results


  def getAlbumGenreDB(self, vals, ret=False, album=None):
    return self.selectUpdateInsert(
      map( lambda x: x['select'], self.db_res['album_genre']), 
      'album_genre',
      ret=ret,
      vals=vals,
      select_stm_str = "SELECT * FROM album_genres  WHERE album_id = $2 AND genre_id = $1",
      insert_stm_str = "INSERT INTO album_genres (album_id, genre_id, similarity) VALUES ($2,$1,$3)",
      update_stm_str = "UPDATE album_genres SET similarity = $3 WHERE album_id = $1 AND genre_id = $2",
      select_args = [0],
      sargs = [self.db_res['album'][0]['select'][0] if album is None else album[0]],
      insert_args = [0],
      iargs = [self.db_res['album'][0]['select'][0] if album is None else album[0]],
      viargs = [1],
      update_args = [0],
      uargs = [self.db_res['album'][0]['select'][0] if album is None else album[0]],
      vuargs = [1],
      )

  def getArtistGenreDB(self, vals, ret=False, artist=None):
    return self.selectUpdateInsert(
      map( lambda x: x['select'], self.db_res['artist_genre']), 
      'artist_genre',
      ret=ret,
      vals=vals,
      select_stm_str = "SELECT * FROM artist_genres  WHERE artist_id = $2 AND genre_id = $1",
      insert_stm_str = "INSERT INTO artist_genres (artist_id, genre_id, similarity) VALUES ($2,$1,$3)",
      update_stm_str = "UPDATE artist_genres SET similarity = $3 WHERE artist_id = $1 AND genre_id = $2",
      select_args = [0],
      sargs = [self.db_res['artist'][0]['select'][0] if artist is None else artist[0]],
      insert_args= [0],
      iargs = [self.db_res['artist'][0]['select'][0] if artist is None else artist[0]],
      viargs = [1],
      update_args = [0],
      uargs = [self.db_res['artist'][0]['select'][0] if artist is None else artist[0]],
      vuargs = [1],
      )


  def getSimilarArtistsDB(self, similar_artists,apihandle=None,db_artist=None, ret=False):
    db_othersimilar = []
    def doubleAppend (x,y,z): 
      db_othersimilar.extend(x)
      db_otherartists.extend(y)
      db_othersimilar.extend(z)
    results = []
    if db_artist is None:
      db_artist = self.db_res['artist'][0]['select']
    print("Called similar artists for "+str(db_artist[1]))
    select_simartists = self.db.prepare("SELECT * FROM similar_artists WHERE artist1_id = $1 and artist2_id = $2")
    insert_simartists = self.db.prepare("INSERT INTO similar_artists (artist1_id, artist2_id, similarity) VALUES ($1,$2,$3)")
    update_simartists = self.db.prepare("UPDATE similar_artists SET similarity = $3 WHERE artist1_id = $1 and artist2_id = $2")
    artistsObjs = []
    for artist in similar_artists.keys():
      try:
        artistsObjs.append(artistLookup(artist,apihandle, False,self))
      except Exception as e:
        handleError(e,"Similar artists err")
    db_otherartists = self.getArtistsDB(artistsObjs, ret=True)
    i=-1
    for artist,val in similar_artists.items():
      i+=1      
      # if db_otherartists[-1]['response'] is None:
      #   doubleAppend(*self.getSimilarArtistsDB(other_obj.similar_artists, apihandle, similar_to=[db_otherartists[-1]], ret=True))
      db_other = db_otherartists[i]['select']
      if db_other[0] == db_artist[0]:
        print("Warning: tried to insert similar artists for the same one; skipping")
      else:
        if db_other[0]>db_artist[0]:
          artist1_id = db_other[0]
          artist2_id = db_artist[0]
        else:
          artist1_id = db_artist[0]
          artist2_id = db_other[0]
        try:
          res = list(select_simartists.chunks(artist1_id,artist2_id))
        except Exception as e:
          handleError(e,"Error: cannot query association between artist "+artist+" and artist "+db_artist[1]+" in db")
        print('similarity:',str(artist1_id),str(artist2_id),str(val))
        if len(res)==0:
          try:
            insert_simartists(artist1_id,artist2_id,val)
          except Exception as e:
            handleError(e,"Error: cannot associate artist "+artist+" with artist "+db_artist[1]+" in db")
        elif len(res)>1:
          print("Error: more than one results for artist_genre association query")
        else:
          try:
            update_simartists(artist1_id,artist2_id,val)
          except Exception as e:
            handleError(e,"Error: cannot update association between artist "+artist+" and artist "+db_artist[1]+" in db")
        db_similarartist = list(select_simartists.chunks(artist1_id,artist2_id))[0][0]
        results.append({
        'response':res[0][0] if len(res)>0 else None, 
        'select':db_similarartist
        })
    if ret:
      return (results,db_otherartists, db_othersimilar)
    self.db_res['similar_artist'] = results
    self.db_res['other_artist'] = db_otherartists
    self.db_res['other_similar'] = db_othersimilar

  def getSimilarGenresDB(self, genre1, genre2, similarity, ret=False):
    return self.selectUpdateInsert(
      [[genre1, genre2, similarity]], 
      'similar_genre',
      ret=ret,
      select_stm_str = "SELECT * FROM similar_genres WHERE genre1_id = $1 and genre2_id = $2",
      insert_stm_str = "INSERT INTO similar_genres (genre1_id, genre2_id, similarity) VALUES ($1,$2,$3)",
      update_stm_str = "UPDATE similar_genres SET similarity = $3 WHERE genre1_id = $1 and genre2_id = $2",
      select_args = [0,1],
      insert_args= [0,1,2],
      update_args = [0,1,2]
      )
  
  def getPlaylistDB(self, playlist, ret=False):
    return self.selectUpdateInsert(
      [playlist], 
      'playlist',
      ret=ret,
      select_stm_str = "SELECT * FROM playlists WHERE playlist_id=$1",
      insert_stm_str = "INSERT INTO playlists ( playlist_id, genre, subgenre, plays) VALUES ($1, $2, $3, $4)",
      update_stm_str = "UPDATE playlists SET plays = $1 where playlist_id=$2",
      select_args = ['playlist_id'],
      insert_args = ['playlist_id', 'genre', 'subgenre', 'plays'],
      update_args = ['plays','playlist_id']
      )

  def getPlaylistSongsDB(self, songs, ret=False, db_playlist_id=None):
    return self.selectUpdateInsert(
      [(songs[i], i) for i in range(len(songs))], 
      'playlist_song',
      ret=ret,
      select_stm_str = "SELECT * FROM playlist_song WHERE playlist_id=$3 AND song_id=$1 AND interval=$2",
      insert_stm_str = "INSERT INTO playlist_song ( song_id, interval, playlist_id) VALUES ($1, $2, $3)",
      update_stm_str = "",
      select_args = [0,1],
      sargs = [self.db_res['playlist'][0]['select'][0] if db_playlist_id is None else db_playlist_id],
      insert_args = [0,1],
      iargs = [self.db_res['playlist'][0]['select'][0] if db_playlist_id is None else db_playlist_id],
      update_args = []
      )


  def changes(self,new, original, index):
    if original is None:
      return "(inserted)"
    elif len(original)>index and Levenshtein.ratio(str(original[index]),new)>0.875:
      return "(no changes)"
    return "(updated from "+str(original[index])+")"

  def printOneRes(self,name, res, fields):
    prepend=''
    if len(res)>1:
      print(name+":")
      prepend+='\t'
    for x in range(len(res)):
      print(prepend+name+" info for "+str(res[x]['select'][1]))
      for y in range(len(fields)):
        print(prepend+"\t"+fields[y]+":"+str(res[x]['select'][y]) +" "+ self.changes(str(res[x]['select'][y]), res[x]['response'],y ))

  def getFieldsDB(self):
    fields = {}
    try:
      fields['artists'] = self.db.prepare("SELECT * FROM artists LIMIT 1").column_names
      fields['album'] = self.db.prepare("SELECT * FROM albums LIMIT 1").column_names
      fields['song'] = self.db.prepare("SELECT * FROM songs LIMIT 1").column_names
      fields['genre'] = self.db.prepare("SELECT * FROM genres LIMIT 1").column_names
      fields['album_genre'] = self.db.prepare("SELECT * FROM album_genres LIMIT 1").column_names
      fields['artist_genre'] = self.db.prepare("SELECT * FROM artist_genres LIMIT 1").column_names
      fields['similar_artist'] = self.db.prepare("SELECT * FROM similar_artists LIMIT 1").column_names
      fields['artists_albums'] = self.db.prepare("SELECT * FROM artists_albums LIMIT 1").column_names
      fields['other_artist'] = fields['artists']
      fields['other_similar'] = fields['similar_artist']
    except Exception as e:
      handleError(e,"Error querying db for fields")
    return fields

  def printRes(self,res=None, fields=None):
    if res is None:
      res = self.db_res
    if type(res) is dict and len(res)>0:
      if fields is None:
        fields = self.getFieldsDB()
      for x,y in res.items():
        try:
          self.printOneRes(x.replace('_',' '), y, fields[x])
        except Exception as e:
          handleError(e,"Error: problem accessing and printing results")

