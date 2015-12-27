#Zarvox Automatic DJ
##GPL'ed by Jon Sims

###Prereqs:

#####Linux, Python 3.4, Postgres, rtorrent 0.9.4, ExifTool

####Python libraries: 

#####python-Levenshtein, PyGreSQL, musicbrainzngs

***


Zarvox has six main components to it:

1. Music finder
 - Takes suggestions from 5. and finds downloads for them
 - Additionally downloads new trending releases
 - "Given a list of artist/album pairs, download the albums from what.cd"

2. Downloader
 - Some already-build program to download the music from 1. and save it to the hard disk
 - Additionally, backups & redundancy need to be structured
 - "Given a folder of torrent files, queue them with rtorrent"

3. Postprocessor
 - Takes a finished download and gets metadata for it, including explicity, from online
 - Loads metadata into database w/ file paths
 - "Given an album, get its metadata online and load some album & some song metadata into DB"

4. Database
 - Literally just create a Postgres database
 - Holds music metadata, liner metadata, playlist data, and intrarelational genre data
 — "Two goals: satisfy playlist generator’s need of initial & additional songs per a general genre, a specific subgenre twist or two, safe harbor, and satisfy playlist finder’s need of time+genre+next_genre+safeharbor based playlist"


5. Playlist generator
 - Take several criteria into account before generating playlist (genre, certain genre/subgenre attributes, safe harbor?)
 - Datamine trending & well-loved music by genre, but also in terms of genre, from what.cd, spotify, pandora(?), last.fm, rateyourmusic, etc.
 - Use these to generate playlists, keeping in mind safe harbor, genre, and subgenre attributes (requires complicated algorithm)
 - index length of show by number of songs remaining for best transition when Zarvox is turned on
 - Store in database along with how many times played and how long since last play
 - "Given a timeslot, generate a playlist"

6. Playlist finder & Music player
 - Given a timestamp (when someone pushed “start” on Zarvox), calculate what playlist to play from what song and what liner (or two) to play to buffer between now and the start of the show, so that the show ends on time (requires complicated algorithm)
 - Factor in however long it takes to do this and program in for Zarvox to start off with a liner that length of time
 - Information to extract from timestamp: genre to play, safeharbor, whether or not it can play a full show
 - Once a playlist & liners are found, send the file path of each to the music player’s queue, do so again for the next show, and repeat the process at the end of the current show
 - This is the only program that doesn’t run continuously; the rest are always doing their thing, and this program turn on when you click the zarvox icon
 - Music player integrated so that it shuts down when this does
 - Music player is given a file path & plays the song, super easy
 - "Given a timeslot, play a playlist"

##Usage instructions:
-Make a file in config named 'credentials' with entries in the form of 'key=value'
-Fill it with the following fields: username (for what.cd), password (for what.cd), spotify_client_id, spotify_client_secret (get both by creating a developer account on their api site), db_user, db_passwd, db_name (all for a locally-hosted postgres db)