--
-- NOTE:
--
-- File paths need to be edited. Search for $$PATH$$ and
-- replace it with the path to the directory containing
-- the extracted a files.
--
--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

ALTER TABLE ONLY public.songs DROP CONSTRAINT songs_album_id_fkey;
ALTER TABLE ONLY public.similar_artists DROP CONSTRAINT similar_artists_artist2_id_fkey;
ALTER TABLE ONLY public.similar_artists DROP CONSTRAINT similar_artists_artist1_id_fkey;
ALTER TABLE ONLY public.playlists_metadata DROP CONSTRAINT playlists_metadata_playlist_id_fkey;
ALTER TABLE ONLY public.artist_genres DROP CONSTRAINT artist_genres_genre_id_fkey;
ALTER TABLE ONLY public.artist_genres DROP CONSTRAINT artist_genres_artist_id_fkey;
ALTER TABLE ONLY public.albums DROP CONSTRAINT albums_artist_id_fkey;
ALTER TABLE ONLY public.album_genres DROP CONSTRAINT album_genres_genre_id_fkey;
ALTER TABLE ONLY public.album_genres DROP CONSTRAINT album_genres_album_id_fkey;
DROP INDEX public.song_ix;
DROP INDEX public.artist_ix;
DROP INDEX public.artist_idx;
DROP INDEX public.album_ix;
DROP INDEX public.album_idx;
ALTER TABLE ONLY public.songs DROP CONSTRAINT songs_pkey;
ALTER TABLE ONLY public.playlists DROP CONSTRAINT playlists_pkey;
ALTER TABLE ONLY public.playlists_metadata DROP CONSTRAINT playlist_pkey;
ALTER TABLE ONLY public.liners DROP CONSTRAINT liners_pkey;
ALTER TABLE ONLY public.genres DROP CONSTRAINT genres_pkey;
ALTER TABLE ONLY public.genres DROP CONSTRAINT genres_genre_key;
ALTER TABLE ONLY public.genres_blacklist DROP CONSTRAINT genres_blacklist_pkey;
ALTER TABLE ONLY public.genres_blacklist DROP CONSTRAINT genres_blacklist_genre_key;
ALTER TABLE ONLY public.artists DROP CONSTRAINT artists_pkey;
ALTER TABLE ONLY public.artists DROP CONSTRAINT artists_artist_key;
ALTER TABLE ONLY public.artist_genres DROP CONSTRAINT artist_genre_pkey;
ALTER TABLE ONLY public.similar_artists DROP CONSTRAINT artist_artist_pkey;
ALTER TABLE ONLY public.albums DROP CONSTRAINT albums_pkey;
ALTER TABLE ONLY public.album_genres DROP CONSTRAINT album_genre_pkey;
ALTER TABLE public.songs ALTER COLUMN song_id DROP DEFAULT;
ALTER TABLE public.playlists_metadata ALTER COLUMN playlist_id DROP DEFAULT;
ALTER TABLE public.playlists ALTER COLUMN playlist_id DROP DEFAULT;
ALTER TABLE public.liners ALTER COLUMN liner_id DROP DEFAULT;
ALTER TABLE public.genres_blacklist ALTER COLUMN genre_id DROP DEFAULT;
ALTER TABLE public.genres ALTER COLUMN genre_id DROP DEFAULT;
ALTER TABLE public.artists ALTER COLUMN artist_id DROP DEFAULT;
ALTER TABLE public.albums ALTER COLUMN album_id DROP DEFAULT;
DROP SEQUENCE public.songs_song_id_seq;
DROP TABLE public.songs;
DROP TABLE public.similar_artists;
DROP SEQUENCE public.playlists_playlist_id_seq;
DROP SEQUENCE public.playlists_metadata_playlist_id_seq;
DROP TABLE public.playlists_metadata;
DROP TABLE public.playlists;
DROP SEQUENCE public.liners_liner_id_seq;
DROP TABLE public.liners;
DROP SEQUENCE public.genres_genre_id_seq;
DROP SEQUENCE public.genres_blacklist_genre_id_seq;
DROP TABLE public.genres_blacklist;
DROP TABLE public.genres;
DROP SEQUENCE public.artists_artist_id_seq;
DROP TABLE public.artists;
DROP TABLE public.artist_genres;
DROP SEQUENCE public.albums_album_id_seq;
DROP TABLE public.albums;
DROP TABLE public.album_genres;
DROP TYPE public.liner_category;
DROP TYPE public.genre_category;
DROP EXTENSION plpgsql;
DROP SCHEMA public;
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: jon
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO jon;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: jon
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: genre_category; Type: TYPE; Schema: public; Owner: jon
--
---Test performence difference between hash and btree index

CREATE ROLE kups WITH SUPERUSER CREATEDB LOGIN ENCRYPTED PASSWORD 'fuck passwords';

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
	, popularity double precision[]
	---CHECK (genre_id NOT IN (SELECT b.genre_id FROM genres_blacklist b))
	CHECK (genre !~ '^\d*.$')
	);

--- The idea is that these are legitimently unhelpful genre names, not just/necessarily shitty genres or ambiguous genres
CREATE TABLE genres_blacklist (
	genre_id smallserial PRIMARY KEY
	, genre text NOT NULL UNIQUE
	, permanent boolean NOT NULL DEFAULT false
	---CHECK (genre_id NOT IN (SELECT b.genre_id FROM genres b))
	);
COPY genres_blacklist (genre, permanent) FROM '/Users/jon/projects/zarvox/postprocessor/genres_blacklist.csv' WITH DELIMITER AS ',' CSV;

--- ~150,000 (15,000 x average number of connections per genre to another genre)
--- similarity taken from last.fm
--- probably don't need this
CREATE TABLE genres_genres (
	genre_id1 smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, genre_id2 smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity smallint NOT NULL DEFAULT 0
	, CONSTRAINT genre_genre_pkey PRIMARY KEY (genre_id1, genre_id2)
	, CONSTRAINT genre_order CHECK (genre_id1 > genre_id2)
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
	, popularity double precision[]
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

-- --- ~100,000 (one per albums)
-- CREATE TABLE artists_albums (
-- 	album_id integer REFERENCES albums (album_id) ON UPDATE CASCADE ON DELETE CASCADE
-- 	, artist_id smallint REFERENCES artists (artist_id) ON UPDATE CASCADE ON DELETE CASCADE
-- 	, CONSTRAINT artist_album_pkey PRIMARY KEY (artist_id,album_id)
-- 	);

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
	, artist_id integer NOT NULL REFERENCES artists ON UPDATE CASCADE ON DELETE RESTRICT
	, popularity double precision[]
	);
CREATE INDEX album_ix ON albums USING hash (album);
CREATE INDEX artist_idx ON albums USING hash (artist_id);


--- ~400,000
CREATE TABLE album_genres (
	album_id integer REFERENCES albums (album_id) ON UPDATE CASCADE ON DELETE CASCADE
	, genre_id smallint REFERENCES genres (genre_id) ON UPDATE CASCADE ON DELETE CASCADE
	, similarity double precision NOT NULL DEFAULT 0.0
	, CONSTRAINT album_genre_pkey PRIMARY KEY (album_id, genre_id)
	);
--CREATE INDEX album_idx ON albums_genres USING hash (album_id);
--CREATE INDEX genre_idx ON albums_genres USING hash (genre_id);



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
	, popularity double precision[]
	, playcount integer NOT NULL DEFAULT 0
	, playlists integer NOT NULL DEFAULT 0
	);
CREATE INDEX song_ix ON songs USING hash (song);
CREATE INDEX album_idx ON songs USING hash (album_id);



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
	playlist_id serial PRIMARY KEY
	, genre genre_category NOT NULL
	, subgenre text NOT NULL
	, transition_to genre_category ---maybe not null?
	, transition_from genre_category ---maybe not null?
	, plays integer NOT NULL DEFAULT 0
	, last_played date NOT NULL DEFAULT date('1969-04-17')
	);

--- ~300,000 entries (playlists x average num of audio files per)
CREATE TABLE playlists_metadata (
	playlist_id serial REFERENCES playlists (playlist_id) ON UPDATE CASCADE ON DELETE CASCADE
	, file_path text NOT NULL
	, interval smallint NOT NULL
	, CONSTRAINT playlist_pkey PRIMARY KEY (playlist_id)
	);


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

--
-- Data for Name: album_genres; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY album_genres (album_id, genre_id, similarity) FROM stdin;
\.
COPY album_genres (album_id, genre_id, similarity) FROM '$$PATH$$/2409.dat';

--
-- Data for Name: albums; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY albums (album_id, album, folder_path, spotify_popularity, lastfm_listeners, lastfm_playcount, whatcd_seeders, whatcd_snatches, artist_id, downloadability) FROM stdin;
\.
COPY albums (album_id, album, folder_path, spotify_popularity, lastfm_listeners, lastfm_playcount, whatcd_seeders, whatcd_snatches, artist_id, downloadability) FROM '$$PATH$$/2408.dat';

--
-- Name: albums_album_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jon
--

SELECT pg_catalog.setval('albums_album_id_seq', 1104, true);


--
-- Data for Name: artist_genres; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY artist_genres (artist_id, genre_id, similarity) FROM stdin;
\.
COPY artist_genres (artist_id, genre_id, similarity) FROM '$$PATH$$/2406.dat';

--
-- Data for Name: artists; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY artists (artist_id, artist, spotify_popularity, lastfm_listeners, lastfm_playcount, whatcd_seeders, whatcd_snatches) FROM stdin;
\.
COPY artists (artist_id, artist, spotify_popularity, lastfm_listeners, lastfm_playcount, whatcd_seeders, whatcd_snatches) FROM '$$PATH$$/2404.dat';

--
-- Name: artists_artist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jon
--

SELECT pg_catalog.setval('artists_artist_id_seq', 3840, true);


--
-- Data for Name: genres; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY genres (genre_id, genre, supergenre, popularity) FROM stdin;
\.
COPY genres (genre_id, genre, supergenre, popularity) FROM '$$PATH$$/2402.dat';

--
-- Data for Name: genres_blacklist; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY genres_blacklist (genre_id, genre, permanent) FROM stdin;
\.
COPY genres_blacklist (genre_id, genre, permanent) FROM '$$PATH$$/2419.dat';

--
-- Name: genres_blacklist_genre_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jon
--

SELECT pg_catalog.setval('genres_blacklist_genre_id_seq', 4222, true);


--
-- Name: genres_genre_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jon
--

SELECT pg_catalog.setval('genres_genre_id_seq', 860, true);


--
-- Data for Name: liners; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY liners (liner_id, liner, file_path, length, type) FROM stdin;
\.
COPY liners (liner_id, liner, file_path, length, type) FROM '$$PATH$$/2413.dat';

--
-- Name: liners_liner_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jon
--

SELECT pg_catalog.setval('liners_liner_id_seq', 1, false);


--
-- Data for Name: playlists; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY playlists (playlist_id, genre, subgenre, transition_to, transition_from, plays, last_played) FROM stdin;
\.
COPY playlists (playlist_id, genre, subgenre, transition_to, transition_from, plays, last_played) FROM '$$PATH$$/2415.dat';

--
-- Data for Name: playlists_metadata; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY playlists_metadata (playlist_id, file_path, "interval") FROM stdin;
\.
COPY playlists_metadata (playlist_id, file_path, "interval") FROM '$$PATH$$/2417.dat';

--
-- Name: playlists_metadata_playlist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jon
--

SELECT pg_catalog.setval('playlists_metadata_playlist_id_seq', 1, false);


--
-- Name: playlists_playlist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jon
--

SELECT pg_catalog.setval('playlists_playlist_id_seq', 1, false);


--
-- Data for Name: similar_artists; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY similar_artists (artist1_id, artist2_id, similarity) FROM stdin;
\.
COPY similar_artists (artist1_id, artist2_id, similarity) FROM '$$PATH$$/2405.dat';

--
-- Data for Name: songs; Type: TABLE DATA; Schema: public; Owner: jon
--

COPY songs (song_id, song, filename, album_id, length, explicit, spotify_popularity, lastfm_listeners, lastfm_playcount, popularity, playcount, playlists) FROM stdin;
\.
COPY songs (song_id, song, filename, album_id, length, explicit, spotify_popularity, lastfm_listeners, lastfm_playcount, popularity, playcount, playlists) FROM '$$PATH$$/2411.dat';

--
-- Name: songs_song_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jon
--

SELECT pg_catalog.setval('songs_song_id_seq', 17, true);


--
-- Name: album_genre_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY album_genres
    ADD CONSTRAINT album_genre_pkey PRIMARY KEY (album_id, genre_id);


--
-- Name: albums_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY albums
    ADD CONSTRAINT albums_pkey PRIMARY KEY (album_id);


--
-- Name: artist_artist_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY similar_artists
    ADD CONSTRAINT artist_artist_pkey PRIMARY KEY (artist1_id, artist2_id);


--
-- Name: artist_genre_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY artist_genres
    ADD CONSTRAINT artist_genre_pkey PRIMARY KEY (artist_id, genre_id);


--
-- Name: artists_artist_key; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY artists
    ADD CONSTRAINT artists_artist_key UNIQUE (artist);


--
-- Name: artists_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY artists
    ADD CONSTRAINT artists_pkey PRIMARY KEY (artist_id);


--
-- Name: genres_blacklist_genre_key; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY genres_blacklist
    ADD CONSTRAINT genres_blacklist_genre_key UNIQUE (genre);


--
-- Name: genres_blacklist_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY genres_blacklist
    ADD CONSTRAINT genres_blacklist_pkey PRIMARY KEY (genre_id);


--
-- Name: genres_genre_key; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY genres
    ADD CONSTRAINT genres_genre_key UNIQUE (genre);


--
-- Name: genres_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY genres
    ADD CONSTRAINT genres_pkey PRIMARY KEY (genre_id);


--
-- Name: liners_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY liners
    ADD CONSTRAINT liners_pkey PRIMARY KEY (liner_id);


--
-- Name: playlist_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY playlists_metadata
    ADD CONSTRAINT playlist_pkey PRIMARY KEY (playlist_id);


--
-- Name: playlists_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY playlists
    ADD CONSTRAINT playlists_pkey PRIMARY KEY (playlist_id);


--
-- Name: songs_pkey; Type: CONSTRAINT; Schema: public; Owner: jon; Tablespace: 
--

ALTER TABLE ONLY songs
    ADD CONSTRAINT songs_pkey PRIMARY KEY (song_id);


--
-- Name: album_idx; Type: INDEX; Schema: public; Owner: jon; Tablespace: 
--

CREATE INDEX album_idx ON songs USING hash (album_id);


--
-- Name: album_ix; Type: INDEX; Schema: public; Owner: jon; Tablespace: 
--

CREATE INDEX album_ix ON albums USING hash (album);


--
-- Name: artist_idx; Type: INDEX; Schema: public; Owner: jon; Tablespace: 
--

CREATE INDEX artist_idx ON albums USING hash (artist_id);


--
-- Name: artist_ix; Type: INDEX; Schema: public; Owner: jon; Tablespace: 
--

CREATE INDEX artist_ix ON artists USING hash (artist);


--
-- Name: song_ix; Type: INDEX; Schema: public; Owner: jon; Tablespace: 
--

CREATE INDEX song_ix ON songs USING hash (song);


--
-- Name: album_genres_album_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jon
--

ALTER TABLE ONLY album_genres
    ADD CONSTRAINT album_genres_album_id_fkey FOREIGN KEY (album_id) REFERENCES albums(album_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: album_genres_genre_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jon
--

ALTER TABLE ONLY album_genres
    ADD CONSTRAINT album_genres_genre_id_fkey FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: albums_artist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jon
--

ALTER TABLE ONLY albums
    ADD CONSTRAINT albums_artist_id_fkey FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: artist_genres_artist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jon
--

ALTER TABLE ONLY artist_genres
    ADD CONSTRAINT artist_genres_artist_id_fkey FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: artist_genres_genre_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jon
--

ALTER TABLE ONLY artist_genres
    ADD CONSTRAINT artist_genres_genre_id_fkey FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: playlists_metadata_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jon
--

ALTER TABLE ONLY playlists_metadata
    ADD CONSTRAINT playlists_metadata_playlist_id_fkey FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: similar_artists_artist1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jon
--

ALTER TABLE ONLY similar_artists
    ADD CONSTRAINT similar_artists_artist1_id_fkey FOREIGN KEY (artist1_id) REFERENCES artists(artist_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: similar_artists_artist2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jon
--

ALTER TABLE ONLY similar_artists
    ADD CONSTRAINT similar_artists_artist2_id_fkey FOREIGN KEY (artist2_id) REFERENCES artists(artist_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: songs_album_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: jon
--

ALTER TABLE ONLY songs
    ADD CONSTRAINT songs_album_id_fkey FOREIGN KEY (album_id) REFERENCES albums(album_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: public; Type: ACL; Schema: -; Owner: jon
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM jon;
GRANT ALL ON SCHEMA public TO jon;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

