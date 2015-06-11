#Zarvox Automatic Disc Jockey
##GPL'ed by Jon Sims

Prereqs
Linux, Python3, Postgres

Zarvox has seven components to it:

1. Music finder
- Takes suggestions from 5. and finds downloads for them
- Additionally downloads new trending releases
-- Given a list of artist/album pairs, download the albums from what.cd via wget
-- Daily batch download of what.cd top 10s
-- Daily batch download of genre & popularity
-- Email webmaster 0 wgets error

2. Downloader
- Some already-build program to download the music from 1. and save it to the hard disk
- Additionally, backups & redundancy need to be structured
-- Given a folder of torrent files, queue them with rtorrent
-- Ensure that RAID is working and email webmaster RAID errors and rtorrent errors

3. Postprocessor
- Takes a finished download and gets metadata for it, including explicity, from online
- Loads metadata into database w/ file paths
-- Given an album, get its metadata online and load some album & some song metadata into DB
-- Email Jon error output

4. Database
- Literally just create a Postgres database
- Holds music metadata, liner metadata, playlist data, and intrarelational genre data
—- Two goals: satisfy playlist generator’s need of initial & additional songs per a general genre, a specific subgenre twist or two, safe harbor, and satisfy playlist finder’s need of time+genre+next_genre+safeharbor based playlist
-- Decide most efficient (space) way to do it, because less is more!
-- Email Jon if not on or if errors

5. Playlist generator
- Take several criteria into account before generating playlist (genre, certain genre/subgenre attributes, safe harbor?)
- Datamine trending & well-loved music by genre, but also in terms of genre, from what.cd, spotify, pandora(?), last.fm, rateyourmusic, etc.
- Use these to generate playlists, keeping in mind safe harbor, genre, and subgenre attributes (requires complicated algorithm)
- index length of show by number of songs remaining for best transition when Zarvox is turned on
- Store in database along with how many times played and how long since last play
-- Given a timeslot, calc genre, if transitioning & what, safe harbor
-- Using 1 criteria and 2 weights, random generate a subgenre/twist
-- Using 2 criteria, generate 20 minutes and 3 songs worth of music from that, weighing against duration beyond 5 and preferencing
-- Using 3+ songs, calculate similar artists => their similar albums => download => good songs from those albums go into playlist
-- Using list of songs, calc similarity between each to form total order (again prioritizing transition and when)
-- Using 57+ min of ordered music, calc liners
-- Store in DB and store times
-- Email jon critical errors when runing program

6. Playlist finder & Music player
- Given a timestamp (when someone pushed “start” on Zarvox), calculate what playlist to play from what song and what liner (or two) to play to buffer between now and the start of the show, so that the show ends on time (requires complicated algorithm)
- Factor in however long it takes to do this and program in for Zarvox to start off with a liner that length of time
- Information to extract from timestamp: genre to play, safeharbor, whether or not it can play a full show
- Once a playlist & liners are found, send the file path of each to the music player’s queue, do so again for the next show, and repeat the process at the end of the current show
- This is the only program that doesn’t run continuously; the rest are always doing their thing, and this program turn on when you click the zarvox icon
- Music player integrated so that it shuts down when this does
- Music player is given a file path & plays the song, super easy
-- Given a timeslot, calc genre, if transitioning & what, safe harbor
-- Using 2 criteria and 2 weight (transitioning and plays-per-playlist (double)), order playlists by what should be played
-- search by order for one with time that'll work with +/- 30 seconds
-- if none, increase time +/- 45 etc.
-- return playlist to music player
-- Email jon log with output of how the search is doing & any errors at runtime
-- Text jon with errors at runtime?
