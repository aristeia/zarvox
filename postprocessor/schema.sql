CREATE ROLE kups WITH SUPERUSER CREATEDB LOGIN ENCRYPTED PASSWORD 'fuck passwords';
CREATE DATABASE zarvox WITH OWNER kups;

# Once logged into the database

## music stuff

# ~15,000 max
CREATE TABLE genres (
	genre_id smallserial PRIMARY KEY
	, genre text NOT NULL UNIQUE
	, supergenre char(11) NOT NULL CHECK 
		(supergenre IN ('rock','electronic','alternative','specialty','hip-hop'))
		# 11 is the length of the word 'alternative'; set this to length of longest genre name
	, popularity double precision NOT NULL DEFAULT 0
	);

# ~150,000 (15,000 x average number of connections per genre to another genre)
CREATE TABLE genres_genres (
	genre_id1 smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, genre_id2 smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity smallint NOT NULL DEFAULT 0
	, CONSTRAINT genre_genre_pkey PRIMARY KEY (genre_id1, genre_id2)
	, CONSTRAINT genre_order CHECK (genre_id1 > genre_id2)
	);


# ~1,000,000
CREATE TABLE songs (
	song_id serial PRIMARY KEY
	, song text NOT NULL
	, filename text NOT NULL
	, album_id integer NOT NULL
	, length smallint NOT NULL #in seconds
	, safe_harbor boolean NOT NULL
	, playable boolean NOT NULL #check these datatypes out
	, popularity double precision NOT NULL DEFAULT 0
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
	, precision smallint NOT NULL DEFAULT 8
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


## end of music stuff

## liner stuff

# ~1,000 entries
CREATE TABLE liners (
	liner_id serial PRIMARY KEY
	, liner text NOT NULL
	, file_path text NOT NULL
	, length smallint NOT NULL #in seconds
	, type char(11) NOT NULL CHECK 
		(type IN ('liner','legal_id','underwriter','PSA','etc.......'))
		# 11 is the length of the word 'alternative'; set this to length of longest genre name
	);

## end of liner stuff

## playlist stuff

# ~20,000 entries
CREATE TABLE playlists (
	playlist_id serial PRIMARY KEY
	, genre char(11) NOT NULL CHECK 
		(genre IN ('rock','electronic','alternative','specialty','hip-hop'))
		# 11 is the length of the word 'alternative'; set this to length of longest genre name
	, subgenre text NOT NULL DEFAULT genre
	, transition_to char(11) NOT NULL CHECK 
		(transition_to IN ('rock','electronic','alternative','specialty','hip-hop'))
		# 11 is the length of the word 'alternative'; set this to length of longest genre name
	, transition_from char(11) NOT NULL CHECK 
		(transition_from IN ('rock','electronic','alternative','specialty','hip-hop'))
		# 11 is the length of the word 'alternative'; set this to length of longest genre name
	, plays integer NOT NULL DEFAULT 0
	, last_played date NOT NULL DEFAULT 0# Fix this
	);

# ~300,000 entries (playlists x average num of audio files per)
CREATE TABLE playlists_metadata (
	playlist_id serial REFERENCES playlists (playlist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, file_path text NOT NULL
	, interval smallint NOT NULL
	);








