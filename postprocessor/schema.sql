CREATE ROLE kups WITH SUPERUSER CREATEDB LOGIN ENCRYPTED PASSWORD 'fuck passwords';
CREATE DATABASE zarvox WITH OWNER kups;

# Once logged into the database

## music stuff

# ~15,000 max
# 11 is the length of the word 'alternative'; set this to length of longest genre name
# popularity is popularity with respect to others in genre taken from lastfm: log_x(listeners)
# similarity also taken from lastfm
CREATE TABLE genres (
	genre_id smallserial PRIMARY KEY
	, genre text NOT NULL UNIQUE
	, supergenre char(11) NOT NULL CHECK 
		(supergenre IN ('rock','electronic','alternative','specialty','hip-hop'))
	, popularity double precision NOT NULL DEFAULT 0
	, supergenre_similarity double precision NOT NULL DEFAULT 0.5
	);

# ~150,000 (15,000 x average number of connections per genre to another genre)
# similarity taken from last.fm
# probably don't need this
-- CREATE TABLE genres_genres (
-- 	genre_id1 smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
-- 	, genre_id2 smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
-- 	, similarity smallint NOT NULL DEFAULT 0
-- 	, CONSTRAINT genre_genre_pkey PRIMARY KEY (genre_id1, genre_id2)
-- 	, CONSTRAINT genre_order CHECK (genre_id1 > genre_id2)
-- 	);


# ~1,000,000
# popularity based on:
# spotify + C( log_x(lastfm plays) * (plays / listeners)^y) + C(log_x(whatcd seeds) * (C + seeds / snatches)^y)
CREATE TABLE songs (
	song_id serial PRIMARY KEY
	, song text NOT NULL
	, filename text NOT NULL
	, album_id integer NOT NULL
	, length smallint NOT NULL 
	, safe_harbor boolean NOT NULL
	, popularity double precision NOT NULL DEFAULT 0
	, playcount integer NOT NULL DEFAULT 0
	);

# ~100,000
CREATE TABLE albums (
	album_id serial PRIMARY KEY
	, album text NOT NULL
	, folder_path text NOT NULL
	, artist_id integer NOT NULL
	);

# ~400,000
CREATE TABLE albums_genres (
	album_id integer REFERENCES albums (album_id) ON UPDATE CASCADE ON DELETE CASCADE
	, genre_id smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, precision smallint NOT NULL DEFAULT 0
	, CONSTRAINT album_genre_pkey PRIMARY KEY (album_id, genre_id)
	);

# ~1,000,000 (one per song)
CREATE TABLE albums_songs (
	album_id integer REFERENCES albums (album_id) ON UPDATE CASCADE ON DELETE CASCADE
	, song_id smallint REFERENCES songs (song_id) ON UPDATE CASCADE ON DELETE CASCADE
	, CONSTRAINT album_song_pkey PRIMARY KEY (album_id, song_id)
	);

# ~50,000
CREATE TABLE artists (
	artist_id serial PRIMARY KEY
	, artist text NOT NULL
	);

# ~150,000 (conections between artists)
CREATE TABLE artists_artists (
	artist_id1 integer REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, artist_id2 integer REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity smallint NOT NULL DEFAULT 0
	, CONSTRAINT artist_artist_pkey PRIMARY KEY (artist_id1, artist_id2)
	);

# ~100,000 (one per albums)
CREATE TABLE artists_albums (
	album_id integer REFERENCES albums (album_id) ON UPDATE CASCADE ON DELETE CASCADE
	, artist_id smallint REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, CONSTRAINT artist_album_pkey PRIMARY KEY (artist_id,album_id)
	);

# ~500,000 (ave number of genres per artist)
CREATE TABLE artists_genres (
	genre_id integer REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, artist_id smallint REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, precision smallint NOT NULL DEFAULT 0
	, CONSTRAINT artist_genre_pkey PRIMARY KEY (artist_id,genre_id)
	);


## end of music stuff

## liner stuff

# ~1,000 entries
CREATE TABLE liners (
	liner_id serial PRIMARY KEY
	, liner text NOT NULL
	, file_path text NOT NULL
	, length smallint NOT NULL
	, type char(11) NOT NULL CHECK 
		(type IN ('liner','legal_id','underwriter','PSA','etc.......'))
	);

## end of liner stuff

## playlist stuff

# ~20,000 entries
CREATE TABLE playlists (
	playlist_id serial PRIMARY KEY
	, genre char(11) NOT NULL CHECK 
		(genre IN ('rock','electronic','alternative','specialty','hip-hop'))
	, subgenre text NOT NULL
	, transition_to char(11) NOT NULL CHECK 
		(transition_to IN ('rock','electronic','alternative','specialty','hip-hop'))
	, transition_from char(11) NOT NULL CHECK 
		(transition_from IN ('rock','electronic','alternative','specialty','hip-hop'))
	, plays integer NOT NULL DEFAULT 0
	, last_played date NOT NULL DEFAULT date('1969-04-17')
	);

# ~300,000 entries (playlists x average num of audio files per)
CREATE TABLE playlists_metadata (
	playlist_id serial REFERENCES playlists (playlist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, file_path text NOT NULL
	, interval smallint NOT NULL
	);