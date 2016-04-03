---Test performence difference between hash and btree index

-- CREATE ROLE kups WITH SUPERUSER CREATEDB LOGIN ENCRYPTED PASSWORD 'fuck passwords';

CREATE DATABASE zarvox WITH OWNER kups;
\connect zarvox;
--- Once logged into the database

------ music stuff

--- ~15,000 max
--- 11 is the length of the word 'alternative'; set this to length of longest genre name
--- popularity is percent of listens of albums in supergenre with tag, updated at least once a week

CREATE TYPE genre_category AS ENUM ('specialty','loud rock','hip-hop','electronic','alternative');

CREATE TABLE genres (
	genre_id smallserial PRIMARY KEY
	, genre text NOT NULL UNIQUE
	, supergenre genre_category NOT NULL
	, popularity double precision
	---CHECK (genre_id NOT IN (SELECT b.genre_id FROM genres_blacklist b))
	CHECK (genre !~ '^\d*.$')
	);

--- The idea is that these are legitimently unhelpful genre names, not just/necessarily shitty genres or ambiguous genres
CREATE TABLE genres_blacklist (
	genre_id serial PRIMARY KEY
	, genre text NOT NULL UNIQUE
	, permanent boolean NOT NULL DEFAULT false
	---CHECK (genre_id NOT IN (SELECT b.genre_id FROM genres b))
	);
COPY genres_blacklist (genre, permanent) FROM '/home/jon/projects/zarvox/database/genreBlacklist.csv' WITH DELIMITER AS ',' CSV;

--- ~150,000 (15,000 x average number of connections per genre to another genre)
--- similarity taken from last.fm
--- probably don't need this
CREATE TABLE similar_genres (
	genre1_id smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, genre2_id smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity double precision NOT NULL DEFAULT 0
	, CONSTRAINT genre_genre_pkey PRIMARY KEY (genre1_id, genre2_id)
	, CONSTRAINT genre_order CHECK (genre1_id > genre2_id)
	);

--- ~50,000
CREATE TABLE artists (
	artist_id serial PRIMARY KEY
	, artist text NOT NULL UNIQUE
	, spotify_popularity integer NOT NULL DEFAULT 0
	, lastfm_listeners integer NOT NULL DEFAULT 0
	, lastfm_playcount integer NOT NULL DEFAULT 0
	, whatcd_seeders integer NOT NULL DEFAULT 0
	, whatcd_snatches integer NOT NULL DEFAULT 0
	, popularity double precision
    , pitchfork_rating smallint DEFAULT 0 NOT NULL
	, kups_playcount integer NOT NULL DEFAULT 0
	);
CREATE INDEX artist_ix ON artists USING hash (artist);

--- ~150,000 (conections between artists)
CREATE TABLE similar_artists (
	artist1_id integer REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, artist2_id integer REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity double precision NOT NULL DEFAULT 0
	, CONSTRAINT artist_artist_pkey PRIMARY KEY (artist1_id, artist2_id)
 	, CONSTRAINT artist_order CHECK (artist1_id > artist2_id)
	);
--CREATE INDEX artist_idx1 ON artists_artists USING hash (artist_id1);
--CREATE INDEX artist_idx2 ON artists_artists USING hash (artist_id2);


--- ~500,000 (ave number of genres per artist)
CREATE TABLE artist_genres (
	artist_id integer REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, genre_id smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity double precision NOT NULL DEFAULT 0.0
	, CONSTRAINT artist_genre_pkey PRIMARY KEY (artist_id,genre_id)
	);
--CREATE INDEX artist_idx1 ON artists_artists USING hash (artist_id1);
--CREATE INDEX artist_idx2 ON artists_artists USING hash (artist_id2);

--- ~100,000
CREATE TABLE albums (
	album_id serial PRIMARY KEY
	, album text NOT NULL
	, folder_path text NOT NULL DEFAULT ''
	, spotify_popularity integer NOT NULL DEFAULT 0
	, lastfm_listeners integer NOT NULL DEFAULT 0
	, lastfm_playcount integer NOT NULL DEFAULT 0
	, whatcd_seeders integer NOT NULL DEFAULT 0
	, whatcd_snatches integer NOT NULL DEFAULT 0
	-- , artist_id integer NOT NULL REFERENCES artists ON UPDATE CASCADE ON DELETE RESTRICT
	, popularity double precision
    , pitchfork_rating smallint DEFAULT 0 NOT NULL
	, kups_playcount integer NOT NULL DEFAULT 0
	);
CREATE INDEX album_ix ON albums USING hash (album);


--- ~400,000
CREATE TABLE album_genres (
	album_id integer REFERENCES albums (album_id) ON UPDATE CASCADE ON DELETE CASCADE
	, genre_id smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity double precision NOT NULL DEFAULT 0.0
	, CONSTRAINT album_genre_pkey PRIMARY KEY (album_id, genre_id)
	);
-- CREATE INDEX album_idx ON albums_genres USING hash (album_id);
-- CREATE INDEX genre_idx ON albums_genres USING hash (genre_id);

-- --- ~100,000 (one per albums)
CREATE TABLE artists_albums (
	album_id integer REFERENCES albums (album_id) ON UPDATE CASCADE ON DELETE CASCADE
	, artist_id smallint REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, CONSTRAINT artist_album_pkey PRIMARY KEY (artist_id,album_id)
	);
CREATE INDEX album_idx ON artists_albums USING hash (album_id);
CREATE INDEX artist_idx ON artists_albums USING hash (artist_id);


--- ~1,000,000
--- popularity based on:
--- spotify + C( log_x(lastfm plays) * (plays / listeners)^y) + C(log_x(whatcd seeds) * (C + seeds / snatches)^y)
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
	, popularity double precision
	, playcount integer NOT NULL DEFAULT 0
	, playlists integer NOT NULL DEFAULT 0
	, kups_playcount integer NOT NULL DEFAULT 0
	);
CREATE INDEX song_idx ON songs USING hash (song);
-- CREATE INDEX album_idx ON songs USING hash (album_id);



------ end of music stuff

------ liner stuff

CREATE TYPE liner_category AS ENUM ('liner','legal_id','underwriter','PSA');--,'etc.......');

--- ~1,000 entries
CREATE TABLE liners (
	liner_id serial PRIMARY KEY
	, liner text NOT NULL
	, file_path text NOT NULL
	, length smallint NOT NULL
	, type liner_category NOT NULL
	);

------ end of liner stuff

------ playlist stuff

--- ~20,000 entries
CREATE TABLE playlists (
	playlist_id integer PRIMARY KEY NOT NULL
	, genre genre_category NOT NULL
	, subgenre text NOT NULL
	, plays integer NOT NULL DEFAULT 0
	);
CREATE INDEX playlist_ix ON playlists USING hash (playlist_id);

--- ~300,000 entries (playlists x average num of audio files per)
CREATE TABLE playlist_song (
	playlist_id integer NOT NULL REFERENCES playlists (playlist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, song_id integer NOT NULL REFERENCES songs (song_id) ON UPDATE CASCADE ON DELETE CASCADE
	, interval smallint NOT NULL
	, CONSTRAINT playlist_song_pkey PRIMARY KEY (playlist_id,song_id)
	);
CREATE INDEX playlist_idx ON playlist_song USING hash (playlist_id);
CREATE INDEX song_id2x ON playlist_song USING hash (song_id);


CREATE FUNCTION getAlbumGenres(int) RETURNS TABLE(genre_id smallint, similarity double precision) AS $$
	SELECT genres.genre_id, (
		CASE 
		WHEN simtable.similarity is NULL THEN 0 
		ELSE simtable.similarity 
		END)
	FROM genres 
		LEFT OUTER JOIN (
			SELECT genre_id, similarity FROM album_genres WHERE album_id = $1) 
		AS simtable
	ON genres.genre_id = simtable.genre_id ORDER BY genres.genre_id
$$ LANGUAGE SQL;

CREATE FUNCTION getArtistGenres(int) RETURNS TABLE(genre_id smallint, similarity double precision) AS $$
	SELECT genres.genre_id, (
		CASE 
		WHEN simtable.similarity is NULL THEN 0 
		ELSE simtable.similarity 
		END)
	FROM genres 
		LEFT OUTER JOIN (
			SELECT genre_id, similarity FROM artist_genres WHERE artist_id = $1) 
		AS simtable
	ON genres.genre_id = simtable.genre_id ORDER BY genres.genre_id
$$ LANGUAGE SQL;


CREATE FUNCTION getArtistSimilar(int) RETURNS TABLE(artist_id int, similarity double precision) AS $$
	SELECT artists.artist_id, (
		CASE 
		WHEN simtable.similarity is NULL THEN 0 
		ELSE simtable.similarity 
		END)
	FROM artists 
		LEFT OUTER JOIN (
			SELECT artist2_id as artist_id, similarity FROM similar_artists WHERE artist1_id = $1
			UNION
			SELECT artist1_id as artist_id, similarity FROM similar_artists WHERE artist2_id = $1) 
		AS simtable
	ON artists.artist_id = simtable.artist_id ORDER BY artists.artist_id
$$ LANGUAGE SQL;

-- CREATE FUNCTION getAlbumGenresPivot() RETURNS TABLE(r1 int) AS $$
-- 	SELECT count(agenres.*) FROM albums, crosstab('
-- 		SELECT similarity FROM album_genres WHERE album_id = albums.album_id',
-- 		'SELECT g FROM album_genres WHERE album_id = albums.album_id'
-- 		) AS agenres 
-- $$ LANGUAGE SQL;
