#Postprocessor
##Given an album, get its metadata online and load some album & some song metadata into DB
- Use other programs to query for metadata & associate the file types with it
- If file types aren't in playable format, convert to MP3 V0 if bitrate ave > 220, V1 if >190, V2 if 170, V3 if 150, V4 if 140, V5 if 120, V6 if 100, V7 if 80, V8 if 70, V9 if 60, delete otherwise & do error checking 
- Use site to query explicity
- Load relavent information into database
- For an artist, load name, similar artists (table)
- For an album, load name, artist, path, songs (table), and genres (table)
- For a song, load name, album, length, filename, popularity
- For a genre, load name, subgenre (from major ones), similar genres (table), popularity
- Email webmaster if errors 