#Postprocessor
##Given an album, get its metadata online and load some album & some song metadata into DB
- Use other programs (picard, puddletag) to query for metadata & associate the file types with it
  - If not enough metadata to look up, use Chromaprint and Acoustid to look up music via musical fingerprint
- Also use what.cd, Last.fm, Spotify, Discogs API (and maybe wget rateyourmusic) to get metadata
- If file types aren't in playable format, convert to MP3 
- Use site (lyricswikia, itunes, etc.) to query explicity
- Load relavent information into database
- For an artist, load name, albums (table), similar artists (table)
- For an album, load name, artist, path, songs (table), and genres (table)
- For a song, load name, album, length, filename, popularity
- For a genre, load name, subgenre (from major ones), similar genres (table), popularity
- Email webmaster if errors 

##Notes on APIs
- picard & puddletag can get all metadata, but work weirdly with CLI
- what.cd has everything in their DB (metadata, album/artist genre applicability, artist similarities, album popularity) available via queryable API and python libraries
- Last.fm has virtually everything in their DB (metadata, album/artist genre applicability, artist/song similarities, all popularities (genre, album, artist, by genre, etc), fucking GEOGRAPHICAL popularity data) available via queryable API
- Spotify has popularity in an accurate, yet imprecise way, also has some relations and genres
- Discogs has some shitty metadata
- rateyourmusic needs a fucking API since they have hella ratings and similarities
- iTunes has an API with explicitness
- Lyrics wikia has one too with lyrics (http://lyrics.wikia.com/api.php?action=query&prop=revisions&format=json&rvprop=content&titles=ARTIST_NAME:SONG_NAME)