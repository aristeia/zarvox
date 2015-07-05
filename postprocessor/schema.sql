#Test performence difference between hash and btree index

CREATE ROLE kups WITH SUPERUSER CREATEDB LOGIN ENCRYPTED PASSWORD 'fuck passwords';
CREATE DATABASE zarvox WITH OWNER kups;

# Once logged into the database

## music stuff

# ~15,000 max
# 11 is the length of the word 'alternative'; set this to length of longest genre name
# popularity is percent of listens of albums in supergenre with tag, updated at least once a week

CREATE TYPE genre_category AS ENUM ('specialty','rock','hip-hop','electronic','alternative');

CREATE TABLE genres (
	genre_id smallserial PRIMARY KEY
	, genre text NOT NULL UNIQUE
	, supergenre genre_category NOT NULL
	, popularity integer NOT NULL DEFAULT 0
	CHECK genre_id NOT IN (SELECT b.genre_id from genres_blacklist b)
	);

CREATE TABLE genres_blacklist (
	genre_id smallserial PRIMARY KEY
	, genre text NOT NULL UNIQUE
	, permanent boolean NOT NULL DEFAULT false
	CHECK genre_id NOT IN (SELECT b.genre_id from genres b)
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
	, album_id integer NOT NULL REFERENCES albums ON UPDATE CASCADE ON DELETE RESTRICT
	, length smallint NOT NULL 
	, explicit boolean NOT NULL
	, spotify_popularity integer NOT NULL DEFAULT 0
	, lastfm_listeners integer NOT NULL DEFAULT 0
	, lastfm_playcount integer NOT NULL DEFAULT 0
	, popularity double precision NOT NULL DEFAULT 0
	, playcount integer NOT NULL DEFAULT 0
	, playlists integer NOT NULL DEFAULT 0
	);
CREATE INDEX song_ix ON songs USING hash (song);
CREATE INDEX album_idx ON songs USING hash (album_id);

# ~100,000
CREATE TABLE albums (
	album_id serial PRIMARY KEY
	, album text NOT NULL
	, folder_path text NOT NULL
	, spotify_popularity integer NOT NULL DEFAULT 0
	, lastfm_listeners integer NOT NULL DEFAULT 0
	, lastfm_playcount integer NOT NULL DEFAULT 0
	, whatcd_seeders integer NOT NULL DEFAULT 0
	, whatcd_snatches integer NOT NULL DEFAULT 0
	, artist_id integer NOT NULL REFERENCES artists ON UPDATE CASCADE ON DELETE RESTRICT
	);
CREATE INDEX album_ix ON albums USING hash (album);
CREATE INDEX artist_idx ON albums USING hash (artist_id);


# ~400,000
CREATE TABLE album_genres (
	album_id integer REFERENCES albums (album_id) ON UPDATE CASCADE ON DELETE CASCADE
	, genre_id smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity smallint NOT NULL DEFAULT 0
	, CONSTRAINT album_genre_pkey PRIMARY KEY (album_id, genre_id)
	);
--CREATE INDEX album_idx ON albums_genres USING hash (album_id);
--CREATE INDEX genre_idx ON albums_genres USING hash (genre_id);

# ~50,000
CREATE TABLE artists (
	artist_id serial PRIMARY KEY
	, artist text NOT NULL UNIQUE
	, spotify_popularity integer NOT NULL DEFAULT 0
	, lastfm_listeners integer NOT NULL DEFAULT 0
	, lastfm_playcount integer NOT NULL DEFAULT 0
	, whatcd_seeders integer NOT NULL DEFAULT 0
	, whatcd_snatches integer NOT NULL DEFAULT 0
	);
CREATE INDEX artist_ix ON artists USING hash (artist);

# ~150,000 (conections between artists)
CREATE TABLE similar_artists (
	artist1_id integer REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, artist2_id integer REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity smallint NOT NULL DEFAULT 0
	, CONSTRAINT artist_artist_pkey PRIMARY KEY (artist1_id, artist2_id)
 	, CONSTRAINT artist_order CHECK (artist1_id > artist2_id)
	);
--CREATE INDEX artist_idx1 ON artists_artists USING hash (artist_id1);
--CREATE INDEX artist_idx2 ON artists_artists USING hash (artist_id2);

-- # ~100,000 (one per albums)
-- CREATE TABLE artists_albums (
-- 	album_id integer REFERENCES albums (album_id) ON UPDATE CASCADE ON DELETE CASCADE
-- 	, artist_id smallint REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
-- 	, CONSTRAINT artist_album_pkey PRIMARY KEY (artist_id,album_id)
-- 	);

# ~500,000 (ave number of genres per artist)
CREATE TABLE artist_genres (
	artist_id smallint REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, genre_id integer REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity smallint NOT NULL DEFAULT 0
	, CONSTRAINT artist_genre_pkey PRIMARY KEY (artist_id,genre_id)
	);
--CREATE INDEX artist_idx1 ON artists_artists USING hash (artist_id1);
--CREATE INDEX artist_idx2 ON artists_artists USING hash (artist_id2);


## end of music stuff

## liner stuff

CREATE TYPE liner_category AS ENUM ('liner','legal_id','underwriter','PSA','etc.......');

# ~1,000 entries
CREATE TABLE liners (
	liner_id serial PRIMARY KEY
	, liner text NOT NULL
	, file_path text NOT NULL
	, length smallint NOT NULL
	, type liner_category NOT NULL
	);

## end of liner stuff

## playlist stuff

# ~20,000 entries
CREATE TABLE playlists (
	playlist_id serial PRIMARY KEY
	, genre genre_category NOT NULL
	, subgenre text NOT NULL
	, transition_to genre_category #maybe not null?
	, transition_from genre_category #maybe not null?
	, plays integer NOT NULL DEFAULT 0
	, last_played date NOT NULL DEFAULT date('1969-04-17')
	);

# ~300,000 entries (playlists x average num of audio files per)
CREATE TABLE playlists_metadata (
	playlist_id serial REFERENCES playlists (playlist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, file_path text NOT NULL
	, interval smallint NOT NULL
	, CONSTRAINT playlist_pkey PRIMARY KEY (playlist_id)
	);