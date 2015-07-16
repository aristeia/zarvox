import sys,os,postgresql
sys.path.append("packages")
from lookup import *
from libzarv import *
from libzarvclasses import *
import pickle
import whatapi
from urllib import parse
from functools import reduce

class databaseCon:


  def __init__(self,d):
    self.db=d
    self.db_res = {
      'artist':None
    }

  def updateGenrePopularity(self,db_genreid):
    averageResults = (lambda l:
      reduce(lambda x,y:map(lambda i: x[i]+y[i],xrange(len(x))),l)/len(l))
    #supergenre_albums = self.db.query("SELECT spotify_popularity, lastfm_listeners, lastfm_playcount, whatcd_seeders, whatcd_snatches FROM albums WHERE album_id IN (SELECT album_genres.album_id FROM albums_genres LEFT OUTER JOIN genres ON (album_genres.genre_id = genres.genre_id) WHERE genres.supergenre = $1); ", (db_genre[2]))
    try:
      select_genre = self.db.prepare("SELECT albums.spotify_popularity, albums.lastfm_listeners, albums.lastfm_playcount, albums.whatcd_seeders, albums.whatcd_snatches FROM albums, album_genres WHERE album_genres.album_id = albums.album_id AND album_genres.genre_id = $1")
      subgenre_albums = list(select_genre.chunks(db_genreid))
      if len(subgenre_albums)<2:
        print("Exception: too few subgenres to calc popularity")
        return
      genrePopularity = popularity(averageResults(subgenre_albums))
      update_genre = self.db.prepare("UPDATE genres SET popularity = $1 WHERE genre_id = $2")
      update_genre(genrePopularity, db_genreid)
    except Exception:
      print("Error: couldnt update popularity of genre w/ id of "+db_genreid+'\n')
      exit(1)
    print("Updated with popularity of "+str(genrePopularity))

  def selectUpdateInsert(self,data, dtype, **kwargs):
    #kwargs is a dict with following keys:
    #selecting : select_stm, select_args, sargs
    #inserting : insert_stm, insert_args, iargs
    #updating : update_stm, update_args, uargs
    select_stm = self.db.prepare(kwargs['select_stm_str'])
    insert_stm = self.db.prepare(kwargs['insert_stm_str'])
    update_stm = self.db.prepare(kwargs['update_stm_str'])
    results = []
    for datum in data:
      try:
        res = list(select_stm.chunks(*[datum[x] for x in kwargs['select_args']]+(kwargs['sargs'] if 'sargs' in kwargs else [])))
      except Exception:
        print("Error: cannot select "+ dtype+" in db\n")
        exit(1)
      if len(res)==0:
        try:
          insert_stm.chunks(*[datum[x] for x in kwargs['insert_args']]+(kwargs['iargs'] if 'iargs' in kwargs else [])+([kwargs['vals'][datum[x]] for x in kwargs['viargs']] if 'viargs' in kwargs else []))
        except Exception:
          print("Error: cannot insert "+dtype+" into db\n")
          exit(1)
      elif len(res)>1:
        print("Error: more than one results for "+dtype+" select")
        exit(1)
      else:
        try:
          update_stm.chunks(*[datum[x] for x in kwargs['update_args']]+(kwargs['uargs'] if 'uargs' in kwargs else [])+([kwargs['vals'][datum[x]] for x in kwargs['viargs']] if 'viargs' in kwargs else []))
        except Exception:
          print("Error: cannot update "+dtype+" in db\n")
          exit(1)
      db_select = list(select_stm.chunks(*[datum[x] for x in kwargs['select_args']]+(kwargs['sargs'] if 'sargs' in kwargs else [])))[0][0]
      results.append({
        'response':res[0][0] if len(res)>0 else None, 
        'select':db_select
      })
    if kwargs['ret']:
      return results
    self.db_res[dtype] = results


  def getArtistDB(self, artist, ret=False):
    self.selectUpdateInsert(
      [artist.__dict__], 
      'artist',
      ret=ret,
      select_stm_str = "SELECT * FROM artists WHERE artist = $1",
      insert_stm_str = "INSERT INTO artists ( artist, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches) VALUES ($1, $2, $3, $4,$5, $6)",
      update_stm_str = "UPDATE artists SET spotify_popularity = $2, lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6 WHERE artist = $1",
      select_args = ['name'],
      insert_args = ['name','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches'],
      update_args = ['name','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches']
      )
  
  def getAlbumDB(self, album, ret=False, db_artistid=None):
    self.selectUpdateInsert(
      [album.__dict__], 
      'album',
      ret=ret,
      select_stm_str = "SELECT * FROM albums WHERE album = $1 AND artist_id = $2",
      insert_stm_str = "INSERT INTO albums ( album, folder_path, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches, artist_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
      update_stm_str = "UPDATE albums SET spotify_popularity = $2,lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6 WHERE album = $1",
      select_args = ['name'],
      sargs = [self.db_res['artist'][0]['select'][0] if db_artistid is None else db_artistid],
      insert_args = ['name','filepath','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches'],
      iargs = [self.db_res['artist'][0]['select'][0] if db_artistid is None else db_artistid],
      update_args = ['name','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches']
      )

  def getSongsDB(self, songs, ret=False, db_albumid=None):
    self.selectUpdateInsert(
      [song.__dict__ for song in songs], 
      'song',
      ret=ret,
      select_stm_str = "SELECT * FROM songs WHERE song = $1 AND album_id = $2",
      insert_stm_str = "INSERT INTO songs ( song, filename, album_id, length,  explicit, spotify_popularity,lastfm_listeners,lastfm_playcount) VALUES ($1,$2,$8,$3,$4,$5,$6, $7)",
      update_stm_str = "UPDATE songs SET explicit=$2, spotify_popularity =$3,lastfm_listeners = $4,lastfm_playcount = $5 WHERE song = $1",
      select_args = ['name'],
      sargs = [self.db_res['album'][0]['select'][0] if db_albumid is None else db_albumid],
      insert_args = ['name','filename','length','explicit','spotify_popularity','lastfm_listeners','lastfm_playcount'],
      iargs = [self.db_res['album'][0]['select'][0] if db_albumid is None else db_albumid],
      update_args = ['name','explicit','spotify_popularity','lastfm_listeners','lastfm_playcount']
      )


  def getGenreDB(self,genres, apihandle=None):
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
    for genre in genres:
      db_genre = None
      try:
        res = list(select_genre.chunks(genre))
      except Exception:
        print("Error: cannot query genre in db\n")
        exit(1)
      if len(res)==0:
        whatres = apihandle.request("browse",searchstr="",taglist=parse.quote(genre,'.'))['response']['results']
        snatched = sum(map(lambda x: x['totalSnatched'] if 'totalSnatched' in x else 0, whatres))
        #first check if exists
        if snatched>5000: #Enough to be worth using
          blacklist_query = list(select_blacklist.chunks(genre))
          blacklist = blacklist_query[0] if len(blacklist_query)>0 else []
          if genre not in blacklist or (snatched > 12500 and len(blacklist)>2 and not blacklist[2]):
            # try:
            if genre in blacklist:
              self.db.query("DELETE FROM genres_blacklist WHERE genre_id = $1;", (blacklist[0]))
            percentile = (lambda x:
              float(sum([1 for y in whatres if any([z in y['tags'] for z in x])] ))/float(len(whatres)))
            supergenre = reduce( lambda x,y: (x if x[1]>y[1] else y), {
              'rock': percentile(['rock','metal','classic.rock','hard.rock','punk.rock','blues.rock','progressive.rock','black.metal','death.metal','hardcore.punk','hardcore','grunge','pop.rock']),
              'hip-hop': percentile(['rap','hip.hop','rhythm.and.blues','trip.hop','trap.rap','southern.rap','gangsta','gangsta.rap']),
              'electronic':percentile(['electronic','dub','ambient','dubstep','house','breaks','downtempo','techno','glitch','idm','edm','dance','electro','trance','midtempo','beats','grime']),
              'alternative':percentile(['alternative','indie','indie.rock','punk','emo','singer.songwriter','folk','dream.pop','shoegaze','synth.pop','post.punk','chillwave','kpop','jpop','ska','folk.rock','reggae','new.wave','ethereal','instrumental','surf.rock']),
              'specialty':percentile(['experimental','funk','blues','world.music','soul','psychedelic','art.rock','country','classical','baroque','minimalism','minimal','score','disco','avant.garde','math.rock','afrobeat','post.rock','noise','drone','jazz','dark.cabaret','neofolk','krautrock','improvisation','space.rock','free.jazz'])
            }.items())[0]
            insert_genre(genre,supergenre)
            db_genre = list(select_genre.chunks(genre))[0][0]
            # except Exception:
            #   print("Error: cannot insert genre "+genre+ " into db\n")
            #   exit(1)
        else: #check if misspelling 
          other_genres = filter(lambda x: Levenshtein.ratio(x[0],genre)>0.875,self.db.prepare("SELECT genre FROM genres").chunks())
          if len(other_genres)>0: #mispelling
            genre = reduce(lambda x,y: levi_misc(x,y,genre),other_genres)
            db_genre = list(select_genre.chunks(genre))[0][0]
          else: #add to blacklist
            insert_blacklist(genre,False)
      elif len(res)>1:
        print("Error: more than one results for genre query")
        exit(1)
      else:
        db_genre = res[0][0]
      if db_genre:
        try:
          self.updateGenrePopularity(db_genre[0])
          db_genre = list(select_genre.chunks(genre))[0]
        except Exception:
          print("Error: cannot update the popularity of "+genre+" in db\n")
          exit(1)
        results.append({
        'response':res[0][0] if len(res)>0 else None, 
        'select':db_genre
        })
    if login:
      pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
    self.db_res['genres'] = results


  def getAlbumGenreDB(self, vals, ret=False, album=None):
    self.selectUpdateInsert(
      map( lambda x: x['select'], self.db_res['album_genre']), 
      'album_genres',
      ret=ret,
      vals=vals,
      select_stm_str = "SELECT * FROM album_genres  WHERE album_id = $2 AND genre_id = $1",
      insert_stm_str = "INSERT INTO album_genres (album_id, genre_id, similarity) VALUES ($3,$1,$2)",
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
    self.selectUpdateInsert(
      map( lambda x: x['select'], self.db_res['artist_genre']), 
      'album_genres',
      ret=ret,
      vals=vals,
      select_stm_str = "SELECT * FROM artist_genres  WHERE artist_id = $2 AND genre_id = $1",
      insert_stm_str = "INSERT INTO artist_genres (artist_id, genre_id, similarity) VALUES ($3,$1,$2)",
      update_stm_str = "UPDATE artist_genres SET similarity = $3 WHERE artist_id = $1 AND genre_id = $2",
      select_args = [0],
      sargs = [self.db_res['artist'][0]['select'][0] if artist is None else artist[0]],
      insert_args = [0],
      iargs = [self.db_res['artist'][0]['select'][0] if artist is None else artist[0]],
      viargs = [1],
      update_args = [0],
      uargs = [self.db_res['artist'][0]['select'][0] if artist is None else artist[0]],
      vuargs = [1],
      )


  def getSimilarArtistsDB(self, similar_artists,similar_to, ret=False):
    db_otherartists = []
    db_othersimilar = []
    results = []
    if not similar_to:
      similar_to=self.db_res['artist']
    db_artist = similar_to[0]['select']
    select_simartists = self.db.prepare("SELECT * FROM similar_artists WHERE artist1_id = $1 and artist2_id = $2")
    insert_simartists = self.db.prepare("INSERT INTO similar_artists (artist1_id, artist2_id, similarity) VALUES ($1,$2,$3)")
    update_simartists = self.db.prepare("UPDATE similar_artists SET similarity = $3 WHERE artist1_id = $1 and artist2_id = $2")
    for artist,val in similar_artists:
      other_obj = artistLookup(artist)
      db_otherartists.append(getArtistDB( other_obj, ret=True)[0])
      def doubleAppend (x,y,z): 
        db_othersimilar.extend(x)
        db_otherartists.extend(y)
        db_othersimilar.extend(z)
      doubleAppend(getSimilarArtistsDB(other_obj.similar_artists, similar_to=[db_otherartists[-1]], ret=True))
      db_other = db_otherartists[-1]['select']
      if db_other[0]>db_artist[0]:
        artist1_id = db_other[0]
        artist2_id = db_artist[0]
      else:
        artist1_id = db_artist[0]
        artist2_id = db_other[0]
      try:
        res = list(select_simartists.chunks(artist1_id,artist2_id))
      except Exception:
        print("Error: cannot query association between artist "+artist+" and artist "+db_artist[1]+" in db\n")
        exit(1)
      if len(res)==0:
        try:
          insert_simartists(artist1_id,artist2_id,val)
        except Exception:
          print("Error: cannot associate artist "+artist+" with artist "+db_artist[1]+" in db\n")
          exit(1)
      elif len(res)>1:
        print("Error: more than one results for artist_genre association query")
        exit(1)
      else:
        try:
          update_simartists(artist1_id,artist2_id,val)
        except Exception:
          print("Error: cannot update association between artist "+artist+" and artist "+db_artist[1]+" in db\n")
          exit(1)
      db_similarartist = list(select_simartists.chunks(artist1_id,artist2_id))[0][0]
      results.append({
      'response':res[0][0] if len(res)>0 else None, 
      'select':db_similarartist
      })
    if ret:
      return results, db_otherartists, db_othersimilar
    self.db_res['similar_artists'] = results
    self.db_res['other_artists'] = db_otherartists
    self.db_res['other_similar'] = db_othersimilar


  def printRes(self):
    def getFieldsDB():
      fields = {}
      try:
        fields['artist'] = self.db.prepare("SELECT * FROM artists LIMIT 1").first().column_names
        fields['album'] = self.db.prepare("SELECT * FROM albums LIMIT 1").first().column_names
        fields['song'] = self.db.prepare("SELECT * FROM songs LIMIT 1").first().column_names
        fields['genre'] = self.db.prepare("SELECT * FROM genres LIMIT 1").first().column_names
        fields['album_genre'] = self.db.prepare("SELECT * FROM album_genres LIMIT 1").first().column_names
        fields['artist_genre'] = self.db.prepare("SELECT * FROM artist_genres LIMIT 1").first().column_names
        fields['similar_artist'] = self.db.prepare("SELECT * FROM similar_artists LIMIT 1").first().column_names
      except Exception:
        print("Error: cannot check fields in db\n")
        exit(1)
      return fields

    def changes(new, orignial, index):
      if orignial is None:
        return "(inserted)"
      elif len(original)>index and original[index] == new:
        return "(no changes)"
      return "(updated from "+original[index]+")"

    def printOneRes(self,name, res, fields):
      prepend=''
      if len(res)>1:
        print(name+":")
        prepend+='\t'
      for x in xrange(len(res)):
        print(prepend+name+" info for "+res[x]['select'][1])
        for y in xrange (len(res[x])):
          print(prepend+"\t"+fields[y]+":"+res[x]['select'][y] +" "+ changes(res[x]['select'][y], res[x]['results'],y ))
    fields = self.getFieldsDB()
    try:
      self.printOneRes("Artist",self.db_res['artist'][0],fields['artist'])
      self.printOneRes("Album",self.db_res['album'],fields['album'])
      self.printOneRes("Song",self.db_res['songs'],fields['song'])
      self.printOneRes("Genre",self.db_res['genself.db_res'],fields['genre'])
      self.printOneRes("Album Genre",self.db_res['album_genself.db_res'],fields['album_genre'])
      self.printOneRes("Artist Genre",self.db_res['artist_genself.db_res'],fields['artist_genre'])
      self.printOneRes("Similar Artist",self.db_res['similar_artists'],fields['similar_artist'])
      self.printOneRes("Other Artist",self.db_res['other_artists'],fields['artist'])
      self.printOneRes("Other Similar Artists",self.db_res['other_similar'],fields['similar_artist'])
    except Exception:
      print("Error: problem accessing and printing results\n")
      exit(1)

