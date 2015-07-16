def getArtistDB(self, artist, ret=False):
  select_artist = self.db.prepare("SELECT * FROM artists WHERE artist = $1")
  try:
    res = list(select_artist.chunks(artist.name))
  except Exception:
    print("Error: cannot query artist in db\n")
    exit(1)
  if len(res) == 0:
    try:
      insert_artist = self.db.prepare("INSERT INTO artists ( artist, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches) VALUES ($1, $2, $3, $4,$5, $6)")
      insert_artist(artist.name,artist.spotify_popularity,artist.lastfm_listeners,artist.lastfm_playcount,artist.whatcd_seeders,artist.whatcd_snatches)
    except Exception:
      print("Error: cannot insert artist in db\n")
      exit(1)
  elif len(res)>1:
    print("Error: more than two results for artist query")
    exit(1)
  else:
    update_artist = self.db.prepare("UPDATE artists SET spotify_popularity = $2, lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6 WHERE artist_id = $1")
    update_artist(res[0][0][0],artist.spotify_popularity,artist.lastfm_listeners,artist.lastfm_playcount,artist.whatcd_seeders,artist.whatcd_snatches)
  db_artist = list(select_artist.chunks(artist.name))[0][0]
  if ret:
    return [{ 'response':res[0] if len(res)>0 else None, 'select':db_artist}]
  self.db_res['artist'] = [{
    'response':res[0][0] if len(res)>0 else None, 
    'select':db_artist
    }]


def getAlbumDB(self,album, db_artistid=None):
  db_artistid = self.db_res['artist'][0]['select'][0] if db_artistid is None else db_artistid
  print(db_artistid)
  select_album = self.db.prepare("SELECT * FROM albums WHERE album = $1 AND artist_id = $2")
  try:
    res = list(select_album.chunks(album.name, db_artistid))
  except Exception:
    print("Error: cannot query album in db\n")
    exit(1)
  if len(res) == 0:
    try:
      insert_album = self.db.prepare("INSERT INTO albums ( album, folder_path, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches, artist_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)")
      insert_album(album.name,album.filepath,album.spotify_popularity,album.lastfm_listeners,album.lastfm_playcount,album.whatcd_seeders,album.whatcd_snatches,db_artistid)
    except Exception:
      print("Error: cannot insert album in db\n")
      exit(1)
  elif len(res)>1:
    print("Error: more than one results for album query")
    exit(1)
  else:
    update_album = self.db.prepare("UPDATE albums SET spotify_popularity = $2,lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6 WHERE album = $1")
    update_album(album.name,album.spotify_popularity,album.lastfm_listeners,album.lastfm_playcount,album.whatcd_seeders,album.whatcd_snatches)
  db_album = list(select_album.chunks(album.name, db_artistid))[0][0]
  self.db_res['album'] = [{
    'response':res[0][0] if len(res)>0 else None, 
    'select':db_album
    }]

def getSongsDB(self,songs):
  results = []
  db_albumid = self.db_res['album'][0]['select'][0]
  select_song = self.db.prepare("SELECT * FROM songs WHERE song = $1 AND album_id = $2")
  insert_song = self.db.prepare("INSERT INTO songs ( song, filename, album_id, length,  explicit, spotify_popularity,lastfm_listeners,lastfm_playcount) VALUES ($1,$2,$3,$4,$5,$6,$7, $8)")
  update_song = self.db.prepare("UPDATE songs SET explicit=$2, spotify_popularity =$3,lastfm_listeners = $4,lastfm_playcount = $5 WHERE song = $1")
  for song in songs:
    try:
      res = list(select_song.chunks(song.name,db_albumid))
    except Exception:
      print("Error: cannot query song in db\n")
      exit(1)
    if len(res)==0:
      try:
        insert_song(song.name,song.filename,db_albumid, song.length,song.explicit,song.spotify_popularity,song.lastfm_listeners,song.lastfm_playcount)
      except Exception:
        print("Error: cannot insert song in db\n")
        exit(1)
    elif len(res)>1:  
      print("Error: more than one results for song query")
      exit(1)
    else:
      update_song(song.name,song.explicit,song.spotify_popularity,song.lastfm_listeners,song.lastfm_playcount)
    db_song = list(select_song.chunks(song.name,db_albumid))[0][0]
    results.append({
    'response':res[0][0] if len(res)>0 else None, 
    'select':db_song
    })
  self.db_res['song'] = results

def getAlbumGenreDB(self,vals):
  results = []
  album = self.db_res['album'][0]['select']
  db_genres = map( lambda x: x['select'], self.db_res['album_genre'])
  select_albumgenres = self.db.prepare("SELECT * FROM album_genres  WHERE album_id = $1 AND genre_id = $2")
  insert_albumgenres = self.db.prepare("INSERT INTO album_genres (album_id, genre_id, similarity) VALUES ($1,$2,$3)")
  update_albumgenres = self.db.preprare("UPDATE album_genres SET similarity = $3 WHERE album_id = $1 AND genre_id = $2")
  for db_genre in db_genres:
    try:
      res = list(select_albumgenres.chunks(album[0],db_genre[0]))
    except Exception:
      print("Error: cannot query association between album "+album[1]+" and genre "+db_genre[1]+" in db\n")
      exit(1)
    if len(res)==0:
      try:
        insert_albumgenres(album[0],db_genre[0],vals[db_genre[1]])
      except Exception:
        print("Error: cannot associate album "+album[1]+" with genre "+db_genre[1]+" in db\n")
        exit(1)
    elif len(res)>1:
      print("Error: more than one results for album_genre association query")
      exit(1)
    else:
      try:
        update_albumgenres(album[0],db_genre[0],vals[db_genre[1]])
      except Exception:
        print("Error: cannot update association between album "+album[1]+" and genre "+db_genre[1]+" in db\n")
        exit(1)
    db_albumgenre = list(select_albumgenres.chunks(album[0],db_genre[0]))[0][0]
    results.append({
      'response':res[0][0] if len(res)>0 else None, 
      'select':db_albumgenre
    })
  self.db_res['album_genres'] = results


def getArtistGenreDB(self,vals):
  results = []
  artist = self.db_res['artist'][0]['select']
  db_genres = map( lambda x: x['select'], self.db_res['artist_genre'])
  select_artistgenre = self.db.prepare("SELECT * FROM artist_genres  WHERE artist_id = $1 AND genre_id = $2")
  insert_artistgenre = self.db.prepare("INSERT INTO artist_genres (artist_id, genre_id, similarity) VALUES ($1,$2,$3)")
  update_artistgenres = self.db.prepare("UPDATE artist_genres SET similarity = $3 WHERE artist_id = $1 AND genre_id = $2")
  for db_genre in db_genres:
    try:
      res = list(select_artistgenre.chunks(artist[0],db_genre[0]))
    except Exception:
      print("Error: cannot query association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n")
      exit(1)
    if len(res)==0:
      try:
        insert_artistgenre(artist[0],db_genre[0],vals[db_genre[1]])
      except Exception:
        print("Error: cannot associate artist "+artist[1]+" with genre "+db_genre[1]+" in db\n")
        exit(1)
    elif len(res)>1:
      print("Error: more than one results for artist_genre association query")
      exit(1)
    else:
      try:
        update_artistgenres(artist[0],db_genre[0],vals[db_genre[1]])
      except Exception:
        print("Error: cannot update association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n")
        exit(1)
    db_artistgenre = list(select_artistgenre.chunks(artist[0],db_genre[0]))[0][0]
    results.append({
    'response':res[0][0] if len(res)>0 else None, 
    'select':db_artistgenre
    })
  self.db_res['artist_genres'] = results
