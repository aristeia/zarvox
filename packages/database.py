import sys,os, pg
sys.path.append("packages")
from lookup import *
from libzarv import *
from libzarvclasses import *
import cPickle as pickle
import whatapi


db = None
db_res = {}



def getArtistDB( artist, ret=False):
  global db,db_res
  try:
    res = db.query("SELECT * FROM artists WHERE artist = $1;", (artist.name)).getresult()
  except Exception, e:
    print("Error: cannot query artist in db\n"+str(e))
    exit(1)
  if len(res) == 0:
    try:
      db.query("INSERT INTO artists ( artist, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches) VALUES ($1, $2, $3, $4,$5, $6, $7);", (artist.name,artist.spotify_popularity,artist.lastfm_listeners,artist.lastfm_playcount,artist.whatcd_seeders,artist.whatcd_snatches))
      db_artist = db.query("SELECT * FROM artists WHERE artist = $1;", (artist.name)).getresult()[0]
    except Exception, e:
      print("Error: cannot insert artist in db\n"+str(e))
      exit(1)
  elif len(res)>1:
    print("Error: more than two results for artist query")
    exit(1)
  else:
    db.query("UPDATE artists SET spotify_popularity = $2, lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6 WHERE artist_id = $1;", (res[0][0],artist.spotify_popularity,artist.lastfm_listeners,artist.lastfm_playcount,artist.whatcd_seeders,artist.whatcd_snatches))
    db_artist = db.query("SELECT * FROM artists WHERE artist_id = $1;", (res[0][0])).getresult()[0]
  if ret:
    return [{ 'response':res[0] if len(res)>0 else None, 'select':db_artist}]
  db_res['artist'] = [{
    'response':res[0] if len(res)>0 else None, 
    'select':db_artist
    }]


def getAlbumDB(album):
  global db,db_res
  db_artistid = db_res['artist'][0]['select'][0]
  try:
    res = db.query("SELECT * FROM albums WHERE album = $1 AND artist_id = $2;", (album.name, db_artistid)).getresult()
  except Exception, e:
    print("Error: cannot query album in db\n"+str(e))
    exit(1)
  if len(res) == 0:
    try:
      db.query("INSERT INTO albums ( album, folder_path, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches, artist_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8);", (album.name,album.filepath,album.spotify_popularity,album.lastfm_listeners,album.lastfm_playcount,album.whatcd_seeders,album.whatcd_snatches,db_artistid)).getresult()
      db_album = db.query("SELECT * FROM albums WHERE album = $1 AND artist_id = $2;", (album.name, db_artistid)).getresult()[0]
    except Exception, e:
      print("Error: cannot insert album in db\n"+str(e))
      exit(1)
  elif len(res)>1:
    print("Error: more than one results for album query")
    exit(1)
  else:
    db.query("UPDATE albums SET spotify_popularity = $2,lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6, WHERE album_id = $1;", (res[0][0],album.spotify_popularity,album.lastfm_listeners,album.lastfm_playcount,album.whatcd_seeders,album.whatcd_snatches))
    db_album = db.query("SELECT * FROM albums WHERE album_id = $1;", (res[0][0])).getresult()[0]
  db_res['album'] = [{
    'response':res[0] if len(res)>0 else None, 
    'select':db_album
    }]

def getSongsDB(songs):
  global db,db_res
  results = []
  db_albumid = db_res['album'][0]['select'][0]
  for song in songs:
    try:
      res = db.query("SELECT * FROM songs WHERE song = $1 AND album_id = $2;", (song.name,db_albumid)).getresult()
    except Exception, e:
      print("Error: cannot query song in db\n"+str(e))
      exit(1)
    if len(res)==0:
      try:
        db.query("INSERT INTO songs ( song, filename, album_id, length,  explicit, spotify_popularity,lastfm_listeners,lastfm_playcount) VALUES ($1,$2,$3,$4,$5,$6,$7, $8);", (song.name,song.filename,db_albumid, song.length,song.explicit,song.spotify_popularity,song.lastfm_listeners,song.lastfm_playcount)).getresult()
        db_song = db.query("SELECT * FROM songs WHERE song = $1 AND album_id = $2;", (song.name, db_albumid)).getresult()[0]
      except Exception, e:
        print("Error: cannot insert song in db\n"+str(e))
        exit(1)
    elif len(res)>1:  
      print("Error: more than one results for song query")
      exit(1)
    else:
      db.query("UPDATE songs SET spotify_popularity =$2,lastfm_listeners = $3,lastfm_playcount = $4 WHERE song_id = $1;", (res[0][0],song.spotify_popularity,song.lastfm_listeners,song.lastfm_playcount))
      db_song = db.query("SELECT * FROM songs WHERE song_id = $1;", (res[0[0]])).getresult()[0]
    results.append({
    'response':res[0] if len(res)>0 else None, 
    'select':db_song
    })
  db_res['song'] = results


def getGenreDB(genres, apihandle=None, addOne=False):
  global db,db_res
  results = []
  login=(not apihandle)
  if login:
    credentials = getCreds()
    cookies = pickle.load(open('config/.cookies.dat', 'rb'))
    apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
  for genre in genres:
    db_genre = None
    try:
      res = db.query("SELECT * FROM genres WHERE genre = $1;", (genre)).getresult()
    except Exception, e:
      print("Error: cannot query genre in db\n"+str(e))
      exit(1)
    if len(res)==0:
      whatres = apihandle.request("browse",searchstr="",taglist=genre)['response']['results']
      snatched = sum(map(lambda x: x['totalSnatched'], whatres))
      #first check if exists
      if snatched>5000: #Enough to be worth using
        blacklist_query = db.query("SELECT * FROM genres_blacklist WHERE genre=$1;", (genre)).getresult()
        blacklist = blacklist_query[0] if len(blacklist_query)>0 else []
        if genre not in blacklist or (snatched > 12500 and len(blacklist)>2 and not blacklist[2]):
          try:
            if genre in blacklist:
              db.query("DELETE FROM genres_blacklist WHERE genre_id = $1;", (blacklist[0]))
            percentile = (lambda x:
              float(sum([1 for y in whatres if any([z in y['tags'] for z in x])] ))/float(len(whatres)))
            supergenre = reduce( lambda x1,x2,y1,y2: ((x1,x2) if x2>y2 else (y1,y2)), {
              'rock': percentile(['rock','metal','classic.rock','hard.rock','punk.rock','blues.rock','progressive.rock','black.metal','death.metal','hardcore.punk','hardcore','grunge','pop.rock']),
              'hip.hop': percentile(['rap','hip.hop','rhythm.and.blues','trip.hop','trap.rap','southern.rap','gangsta','gangsta.rap']),
              'electronic':percentile(['electronic','dub','ambient','dubstep','house','breaks','downtempo','techno','glitch','idm','edm','dance','electro','trance','midtempo','beats','grime']),
              'alternative':percentile(['alternative','indie','indie.rock','punk','emo','singer.songwriter','folk','dream.pop','shoegaze','synth.pop','post.punk','chillwave','kpop','jpop','ska','folk.rock','reggae','new.wave','ethereal','instrumental','surf.rock']),
              'specialty':percentile(['experimental','funk','blues','world.music','soul','psychedelic','art.rock','country','classical','baroque','minimalism','minimal','score','disco','avant.garde','math.rock','afrobeat','post.rock','noise','drone','jazz','dark.cabaret','neofolk','krautrock','improvisation','space.rock','free.jazz'])
            }.iteritems())[0]
            db.query("INSERT INTO genres ( genre, supergenre) VALUES ($1,$2);", (genre,supergenre))
            db_genre = db.query("SELECT * FROM genres WHERE genre = $1;", (genre)).getresult()[0]
          except Exception, e:
            print("Error: cannot insert genre "+genre+ " into db\n"+str(e))
            exit(1)
      else: #check if misspelling 
        other_genres = filter(lambda x: Levenshtein.ratio(x[0],genre)>0.875,db.query("SELECT genre FROM genres;").getresult())
        if len(other_genres)>0: #mispelling
          genre = reduce(lambda x,y: levi_misc(x,y,genre),other_genres)
          db_genre = db.query("SELECT * FROM genres WHERE genre = $1;", (genre)).getresult()[0]
        else: #add to blacklist
          db.query("INSERT INTO genres_blacklist (genre,permanent) VALUES ($1,$2);", (genre,False))
    elif len(res)>1:
      print("Error: more than one results for genre query")
      exit(1)
    else:
      db_genre = res[0]
    if db_genre:
      if addOne:
        try:
          #supergenre_albums = db.query("SELECT COUNT(*) FROM albums WHERE album_id IN (SELECT album_genres.album_id FROM albums_genres LEFT OUTER JOIN genres ON (album_genres.genre_id = genres.genre_id) WHERE genres.supergenre = $1); ", (db_genre[2]))
          subgenre_albums = db.query("SELECT COUNT(*) FROM albums_genres, genres WHERE album_genres.genre_id = genres.genre_id AND genres.genre = $1;", (genre))
          popularity =(subgenre_albums+1.0) / (1.0+(subgenre_albums/db_genre[3]))
          db.query("UPDATE genres SET popularity = $1 WHERE genre_id = $2;", (popularity, db_genre[0]))
          db_genre = db.query("SELECT * FROM genres WHERE genre_id = $1;", (db_genre[0])).getresult()[0]
        except Exception, e:
          print("Error: cannot update the popularity of "+genre+" in db\n"+str(e))
          exit(1)
      results.append({
      'response':res[0] if len(res)>0 else None, 
      'select':db_genre
      })
  if login:
    pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))
  db_res['genres'] = results

def getAlbumGenreDB(vals):
  global db,db_res
  results = []
  album = db_res['album'][0]['select']
  db_genres = map( lambda x: x['select'], db_res['album_genre'])
  for db_genre in db_genres:
    try:
      res = db.query("SELECT * FROM album_genres  WHERE album_id = $1 AND genre_id = $2;", (album[0],db_genre[0])).getresult()
    except Exception, e:
      print("Error: cannot query association between album "+album[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
      exit(1)
    if len(res)==0:
      try:
        db.query("INSERT INTO album_genres (album_id, genre_id, similarity) VALUES ($1,$2,$3);", (album[0],db_genre[0],vals[db_genre[1]]))
      except Exception, e:
        print("Error: cannot associate album "+album[1]+" with genre "+db_genre[1]+" in db\n"+str(e))
        exit(1)
    elif len(res)>1:
      print("Error: more than one results for album_genre association query")
      exit(1)
    else:
      try:
        db.query("UPDATE album_genres SET similarity = $3 WHERE album_id = $1 AND genre_id = $2;", (album[0],db_genre[0],vals[db_genre[1]]))
      except Exception, e:
        print("Error: cannot update association between album "+album[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
        exit(1)
    try:
      db_albumgenre = self.db.query("SELECT * FROM album_genres  WHERE album_id = $1 AND genre_id = $2;", (album[0],db_genre[0])).getresult()[0]
    except Exception, e:
      print("Error: cannot query association between album "+album[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
      exit(1)
    results.append({
    'response':res[0] if len(res)>0 else None, 
    'select':db_albumgenre
    })
  db_res['album_genres'] =  results


def getArtistGenreDB(vals):
  global db,db_res
  results = []
  artist = db_res['artist'][0]['select']
  db_genres = map( lambda x: x['select'], db_res['artist_genre'])
  for db_genre in db_genres:
    try:
      res = db.query("SELECT * FROM artist_genres  WHERE artist_id = $1 AND genre_id = $2;", (artist[0],db_genre[0])).getresult()
    except Exception, e:
      print("Error: cannot query association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
      exit(1)
    if len(res)==0:
      try:
        db.query("INSERT INTO artist_genres (artist_id, genre_id, similarity) VALUES ($1,$2,$3);", (artist[0],db_genre[0],vals[db_genre[1]]))
      except Exception, e:
        print("Error: cannot associate artist "+artist[1]+" with genre "+db_genre[1]+" in db\n"+str(e))
        exit(1)
    elif len(res)>1:
      print("Error: more than one results for artist_genre association query")
      exit(1)
    else:
      try:
        db.query("UPDATE artist_genres SET similarity = $3 WHERE artist_id = $1 AND genre_id = $2;", (artist[0],db_genre[0],vals[db_genre[1]]))
      except Exception, e:
        print("Error: cannot update association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
        exit(1)
    try:
      db_artistgenre = db.query("SELECT * FROM artist_genres  WHERE artist_id = $1 AND genre_id = $2;", (artist[0],db_genre[0])).getresult()[0]
    except Exception, e:
      print("Error: cannot query association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
      exit(1)
    results.append({
    'response':res[0] if len(res)>0 else None, 
    'select':db_artistgenre
    })
  db_res['artist_genres'] = results


def getSimilarArtistsDB( similar_artists,similar_to=db_res['artist'], ret=False):
  global db,db_res
  db_otherartists = []
  db_othersimilar = []
  results = []
  db_artist = similar_to[0]['select']
  for artist,val in similar_artists:
    other_obj = artistLookup(artist)
    db_otherartists.append(getArtistDB( other_obj, ret=True)[0])
    doubleAppend = (lambda x,y,z: 
      db_othersimilar.extend(x)
      db_otherartists.extend(y)
      db_othersimilar.extend(z))
    doubleAppend(getSimilarArtistsDB(other_obj.similar_artists, similar_to=[db_otherartists[-1]], ret=True))
    db_other = db_otherartists[-1]['select']
    if db_other[0]>db_artist[0]:
      artist1_id = db_other[0]
      artist2_id = db_artist[0]
    else:
      artist1_id = db_artist[0]
      artist2_id = db_other[0]
    try:
      res = db.query("SELECT * FROM similar_artists WHERE artist1_id = $1 and artist2_id = $2",(artist1_id,artist2_id)).getresult()
    except Exception, e:
      print("Error: cannot query association between artist "+artist+" and artist "+db_artist[1]+" in db\n"+str(e))
      exit(1)
    if len(res)==0:
      try:
        db.query("INSERT INTO similar_artists (artist1_id, artist2_id, similarity) VALUES ($1,$2,$3);", (artist1_id,artist2_id,val))
      except Exception, e:
        print("Error: cannot associate artist "+artist+" with artist "+db_artist[1]+" in db\n"+str(e))
        exit(1)
    elif len(res)>1:
      print("Error: more than one results for artist_genre association query")
      exit(1)
    else:
      try:
        db.query("UPDATE similar_artists SET similarity = $3 WHERE artist1_id = $1 and artist2_id = $2",(artist1_id,artist2_id,val))
      except Exception, e:
        print("Error: cannot update association between artist "+artist+" and artist "+db_artist[1]+" in db\n"+str(e))
        exit(1)
    try:
      db_similarartist = db.query("SELECT * FROM similar_artists WHERE artist1_id = $1 and artist2_id = $2",(artist1_id,artist2_id)).getresult()[0]
    except Exception, e:
      print("Error: cannot query association between artist "+artist+" and artist "+db_artist[1]+" in db\n"+str(e))
      exit(1)
    results.append({
    'response':res[0] if len(res)>0 else None, 
    'select':db_similarartist
    })
  if ret:
    return results, db_otherartists, db_othersimilar
  db_res['similar_artists'] = results
  db_res['other_artists'] = db_otherartists
  db_res['other_similar'] = db_othersimilar


def printRes():
  def getFieldsDB():
    global db
    fields = {}
    try:
      fields['artist'] = db.query("SELECT * FROM artists LIMIT 1").listfields()
      fields['album'] = db.query("SELECT * FROM albums LIMIT 1").listfields()
      fields['song'] = db.query("SELECT * FROM songs LIMIT 1").listfields()
      fields['genre'] = db.query("SELECT * FROM genres LIMIT 1").listfields()
      fields['album_genre'] = db.query("SELECT * FROM album_genres LIMIT 1").listfields()
      fields['artist_genre'] = db.query("SELECT * FROM artist_genres LIMIT 1").listfields()
      fields['similar_artist'] = db.query("SELECT * FROM similar_artists LIMIT 1").listfields()
    except Exception, e:
      print("Error: cannot check fields in db\n"+str(e))
      exit(1)
    return fields

  def changes(new, orignial, index):
    if orignial is None:
      return "(inserted)"
    elif len(original)>index and original[index] == new:
      return "(no changes)"
    return "(updated from "+original[index]+")"

  def printOneRes(name, res, fields):
    prepend=''
    if len(res)>1:
      print(name+":")
      prepend+='\t'
    for x in xrange(len(res)):
      print(prepend+name+" info for "+res[x]['select'][1])
      for y in xrange (len(res[x])):
        print(prepend+"\t"+fields[y]+":"+res[x]['select'][y] +" "+ changes(res[x]['select'][y], res[x]['results'],y ))
  global db_res
  fields = getFieldsDB()
  try:
    printOneRes("Artist",db_res['artist'][0],fields['artist'])
    printOneRes("Album",db_res['album'],fields['album'])
    printOneRes("Song",db_res['songs'],fields['song'])
    printOneRes("Genre",db_res['gendb_res'],fields['genre'])
    printOneRes("Album Genre",db_res['album_gendb_res'],fields['album_genre'])
    printOneRes("Artist Genre",db_res['artist_gendb_res'],fields['artist_genre'])
    printOneRes("Similar Artist",db_res['similar_artists'],fields['similar_artist'])
    printOneRes("Other Artist",db_res['other_artists'],fields['artist'])
    printOneRes("Other Similar Artists",db_res['other_similar'],fields['similar_artist'])
  except Exception, e:
    print("Error: problem accessing and printing results\n"+str(e))
    exit(1)

