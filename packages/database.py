import sys,os,postgresql,time
sys.path.append("packages")
from lookup import artistLookup
from libzarv import *
from libzarvclasses import *
import pickle
import whatapi
from urllib import parse
from functools import reduce
from numpy import float128

class databaseCon:


  def __init__(self,d=None):
    if d is None:
      credentials = getCreds()
      d = postgresql.open('pq://'+credentials['db_user']+':'+credentials['db_password']+'@localhost/'+credentials['db_name'])
    self.db=d
    self.db_res = {
      'artist':None
    }

  def popularitySingle(self,tablename='albums', spotify_popularity=0,lastfm_listeners=0,lastfm_playcount=0,whatcd_seeders=0,whatcd_snatches=0,**lists):
    def customIndex(lst,item):
      if item in lst:
        return float128(lst.index(item))
      elif item<min(lst):
        return float128(0)
      else:
        temp = max([x for x in range(len(lst)) if lst[x]<item])
        if temp==(len(lst)-1):
          return float128(len(lst))
        return float128(temp+(float128((item-lst[temp]))/(lst[temp+1]-lst[temp])))
    def popularityMetric(metric, val):
      if res[metric] is not None:
        if metric in lists:
          metrics = lists[metric]
        else:
          metrics = [x[0] for lst in self.db.prepare("SELECT "+names[metric]+" FROM "+tablename+" ORDER BY 1;").chunks() for x in lst]
        if len(metrics)>0:
          metricf = customIndex(metrics,val)/len(metrics)
        else:
          metricf = 1.0
        metricw = metricf*(res[metric]/float128(sum([y for _,y in res.items() if y is not None])))
        resnew[metric] = metricw
      else:
        resnew[metric] = 0
    names = {
      'sp':'spotify_popularity',
      'll':'lastfm_listeners',
      'lp':'lastfm_playcount',
      'we':'whatcd_seeders',
      'ws':'whatcd_snatches'
    }

    res = {
      'sp': None if spotify_popularity==0 else 0.375,
      'll': None if lastfm_listeners==0 else 0.0875,
      'lp': None if lastfm_playcount==0 else 0.225,
      'we': None if whatcd_seeders==0 else 0.2,
      'ws': None if whatcd_snatches==0 else 0.1125
    }
    resnew = {}
    popularityMetric('sp',spotify_popularity)
    popularityMetric('ll',lastfm_listeners)
    popularityMetric('lp',lastfm_playcount)
    popularityMetric('we',whatcd_seeders)
    popularityMetric('ws',whatcd_snatches)
    return sum([y for x,y in resnew.items()])


  def popularity(self,**both):
    def albumsCheck():
      return 'albums' in both and both['albums'] is not None and len(both['albums'])>4
    def artistsCheck():
      return 'artists' in both and both['artists'] is not None and len(both['artists'])>4
    def calcPop(label):
      if 'lists' not in both or label not in both['lists']:
        both['lists'][label] = {}
      ret=0
      totWeight = sum([float(x[5]) for x in both[label]])
      for l in both[label]:
        ret += self.popularitySingle(label,*(l[0:5]), lists = both['lists'][label])*float128(l[5]/totWeight)
      return ret
    if albumsCheck() and artistsCheck():
      album = calcPop('albums')
      artist = calcPop('artists')
      totalbums = list(self.db.prepare("SELECT COUNT(*) FROM albums;").chunks())[0][0][0]
      totartists = list(self.db.prepare("SELECT COUNT(*) FROM artists;").chunks())[0][0][0]
      print("Album popularity is "+str(album)+' '+str(totalbums)+"and artist is "+str(artist)+' '+str(totartists))
      return (((totalbums / float128(totalbums+totartists))*album) + 
        ((totartists / float128(totalbums+totartists))*artist))
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
      return ({
            'sp': [x[0] for x in list(self.db.prepare("SELECT spotify_popularity FROM albums ORDER BY 1;").chunks())[0]],
            'lp': [x[0] for x in list(self.db.prepare("SELECT lastfm_listeners FROM albums ORDER BY 1;").chunks())[0]],
            'll': [x[0] for x in list(self.db.prepare("SELECT lastfm_playcount FROM albums ORDER BY 1;").chunks())[0]],
            'we': [x[0] for x in list(self.db.prepare("SELECT whatcd_seeders FROM albums ORDER BY 1;").chunks())[0]],
            'ws': [x[0] for x in list(self.db.prepare("SELECT whatcd_snatches FROM albums ORDER BY 1;").chunks())[0]]
          })
    def getArtists():
      return ({
            'sp': [x[0] for x in list(self.db.prepare("SELECT spotify_popularity FROM artists ORDER BY 1;").chunks())[0]],
            'lp': [x[0] for x in list(self.db.prepare("SELECT lastfm_listeners FROM artists ORDER BY 1;").chunks())[0]],
            'll': [x[0] for x in list(self.db.prepare("SELECT lastfm_playcount FROM artists ORDER BY 1;").chunks())[0]],
            'we': [x[0] for x in list(self.db.prepare("SELECT whatcd_seeders FROM artists ORDER BY 1;").chunks())[0]],
            'ws': [x[0] for x in list(self.db.prepare("SELECT whatcd_snatches FROM artists ORDER BY 1;").chunks())[0]]
          })
    # try:
    album_sel = self.db.prepare("SELECT albums.spotify_popularity, albums.lastfm_listeners, albums.lastfm_playcount, albums.whatcd_seeders, albums.whatcd_snatches, album_genres.similarity FROM albums, album_genres WHERE album_genres.album_id = albums.album_id AND album_genres.genre_id = $1")
    artist_sel = self.db.prepare("SELECT artists.spotify_popularity, artists.lastfm_listeners, artists.lastfm_playcount, artists.whatcd_seeders, artists.whatcd_snatches, artist_genres.similarity FROM artists, artist_genres WHERE artist_genres.artist_id = artists.artist_id AND artist_genres.genre_id = $1")
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
    # except Exception:
    #   print("Error: couldnt update popularity of genre "+genre[1]+'\n')
    #   exit(1)
    print("Updated "+genre[1]+" with popularity of "+str(pop))

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
        print("Error: cannot select "+ dtype+" in db\n")
        print(e)
        exit(1)
      if len(res)==0:
        # try:
        insert_stm.chunks(*[datum[x] for x in kwargs['insert_args']]+(kwargs['iargs'] if 'iargs' in kwargs else [])+([kwargs['vals'][datum[x]] for x in kwargs['viargs']] if 'viargs' in kwargs else []))
        # except Exception:
        #   print("Error: cannot insert "+dtype+" into db\n")
        #   exit(1)
      elif len(res)>1:
        print("Error: more than one results for "+dtype+" select")
        exit(1)
      else:
        # try:
        if 'update_stm_str' in kwargs:
          update_stm.chunks(*[datum[x] for x in kwargs['update_args']]+(kwargs['uargs'] if 'uargs' in kwargs else [])+([kwargs['vals'][datum[x]] for x in kwargs['viargs']] if 'viargs' in kwargs else []))
        # except Exception:
        #   print("Error: cannot update "+dtype+" in db\n")
        #   exit(1)
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
      insert_stm_str = "INSERT INTO artists ( artist, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches,popularity) VALUES ($1, $2, $3, $4,$5, $6,$7)",
      update_stm_str = "UPDATE artists SET spotify_popularity = $2, lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6, popularity=$7 WHERE artist = $1",
      select_args = ['name'],
      insert_args = ['name','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches','popularity'],
      update_args = ['name','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches','popularity']
      )
  
  def getAlbumDB(self, album, ret=False, db_artistid=None):
    return self.selectUpdateInsert(
      [album.__dict__], 
      'album',
      ret=ret,
      select_stm_str = "SELECT * FROM albums LEFT OUTER JOIN artists_albums on artists_albums.album_id = albums.album_id WHERE albums.album = $1 and artists_albums.artist_id = $2 or artists_albums.artist_id is null",
      insert_stm_str = "INSERT INTO albums ( album, folder_path, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches, popularity) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
      update_stm_str = "UPDATE albums SET spotify_popularity = $2,lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6,popularity=$7 WHERE album = $1",
      select_args = ['name'],
      sargs = [self.db_res['artist'][0]['select'][0] if db_artistid is None else db_artistid],
      insert_args = ['name','filepath','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches','popularity'],
      iargs = [],#[self.db_res['artist'][0]['select'][0] if db_artistid is None else db_artistid],
      update_args = ['name','spotify_popularity','lastfm_listeners','lastfm_playcount','whatcd_seeders','whatcd_snatches','popularity']
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
      insert_stm_str = "INSERT INTO songs ( song, filename, album_id, length,  explicit, spotify_popularity,lastfm_listeners,lastfm_playcount) VALUES ($1,$2,$8,$3,$4,$5,$6, $7)",
      update_stm_str = "UPDATE songs SET explicit=$2, spotify_popularity =$3,lastfm_listeners = $4,lastfm_playcount = $5 WHERE song = $1",
      select_args = ['name'],
      sargs = [self.db_res['album'][0]['select'][0] if db_albumid is None else db_albumid],
      insert_args = ['name','filename','length','explicit','spotify_popularity','lastfm_listeners','lastfm_playcount'],
      iargs = [self.db_res['album'][0]['select'][0] if db_albumid is None else db_albumid],
      update_args = ['name','explicit','spotify_popularity','lastfm_listeners','lastfm_playcount']
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
    select_supergenre = self.db.prepare("SELECT * FROM genres WHERE supergenre = $1 ORDER BY popularity DESC LIMIT 50")
    for genre in genres:
      db_genre = None
      # try:
      res = list(select_genre.chunks(genre))
      # except Exception:
      #   print("Error: cannot query genre in db\n")
      #   exit(1)
      if len(res)==0:
        what =apihandle.request("browse",searchstr="",taglist=parse.quote(genre,'.'),order_by='snatched')
        while what['status'] != 'success':
          time.sleep(10)
          what=apihandle.request("browse",searchstr="",taglist=parse.quote(genre,'.'),order_by='snatched')
        whatres = what['response']['results']
        snatched = sum(map(lambda x: x['totalSnatched'] if 'totalSnatched' in x else 0, whatres))
        print("Genre "+genre+" has "+str(snatched)+" snatches")
        #first check if exists
        blacklist = [x for lst in list(select_blacklist.chunks(genre)) for x in lst]
        if snatched>10000: #Enough to be worth using
          if genre not in list(map(lambda x:x[1],blacklist)) or (snatched > 10000 and len(blacklist)>0 and not blacklist[0][2]):
            # try:
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
            # except Exception:
            #   print("Error: cannot insert genre "+genre+ " into db\n")
            #   exit(1)
          else:
            print("Exception: genre "+genre+" in blacklist, won't be changed")
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
          print("Exception: genre "+genre+" in blacklist, won't be changed")
      elif len(res)>1:
        print("Error: more than one results for genre query")
        exit(1)
      else:
        db_genre = res[0][0]
      if db_genre:
        # try:
        #   self.updateGenrePopularity(db_genre)
        #   db_genre = list(select_genre.chunks(genre))[0][0]
        # except Exception:
        #   print("Error: cannot update the popularity of "+genre+" in db\n")
        #   exit(1)
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
    db_otherartists = []
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
    for artist,val in similar_artists.items():
      time.sleep(5)
      other_obj = artistLookup(artist,apihandle, False,self)
      db_otherartists.append(self.getArtistDB( other_obj, ret=True)[0])
      # if db_otherartists[-1]['response'] is None:
      #   doubleAppend(*self.getSimilarArtistsDB(other_obj.similar_artists, apihandle, similar_to=[db_otherartists[-1]], ret=True))
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
        # try:
        print('similarity:',str(artist1_id),str(artist2_id),str(val))
        insert_simartists(artist1_id,artist2_id,val)
        # except Exception:
        #   print("Error: cannot associate artist "+artist+" with artist "+db_artist[1]+" in db\n")
        #   exit(1)
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
      return (results, db_otherartists, db_othersimilar)
    self.db_res['similar_artist'] = results
    self.db_res['other_artist'] = db_otherartists
    self.db_res['other_similar'] = db_othersimilar


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
    # try:
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
    # except Exception:
      
    #   exit(1)
    return fields

  def printRes(self,res=None, fields=None):
    if fields is None:
      fields = self.getFieldsDB()
    if res is None:
      res = self.db_res
    for x,y in res.items():
      # try:
      self.printOneRes(x.replace('_',' '), y, fields[x])
      # except Exception:
      #   print("Error: problem accessing and printing results\n")
      #   exit(1)

