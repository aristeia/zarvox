import sys,os,postgresql
sys.path.extend(os.listdir(os.getcwd()))
from database import databaseCon

fName = "playlists"
if len(sys.argv) > 1:
    fName = sys.argv[1]
    if ".tsv" in fname:
        fName = fName.replace(".tsv", "")

con = databaseCon()

playlists = [x 
    for lst in con.db.prepare("SELECT * FROM playlists").chunks() 
    for x in lst]

selectSongs = con.db.prepare("SELECT songs.filename, songs.length, songs.explicit FROM playlist_song LEFT JOIN songs ON songs.song_id = playlist_song.song_id WHERE playlist_song.playlist_id = $1 ORDER BY playlist_song.interval")

def closestTimeSlot(desiredTime, playlist):
    totalLength = 0
    for songI in range(len(playlist)):
        totalLength+=playlist[songI][1]
        if totalLength >= desiredTime:
            if abs(totalLength - desiredTime) > abs((totalLength-playlist[songI][1]) - desiredTime):
                return songI
            return songI+1
    return -1

lenOfNum = 1+floor(log10(len(playlists)))

for playlistI in range(len(playlists)):
    try:
        playlistSongs = [song
            for lst in selectSongIds.chunks(playlists[playlistI][0]) 
            for song in lst]
        explicit = any([song[2] for song in playlistSongs])
        playlistSongs = [tuple(song[:2]) for song in playlistSongs]       
        if any([len(song[0]) < 1 for song in playlistSongs]):
            raise RuntimeError("Issue with this playlist '"+str(playlist)+"', a song isnt in the db!")
        
        playlistSongs.insert(0,("LEGALIDRANDOMIZER",44))
        playlistSongs.insert(1,("UNDERWRITER",54))
        additionalLiners = [("LINERSRANDOMIZER",21,15*60),("PSARANDOMIZER",30,30*60),("LINERSRANDOMIZER",21,45*60)]
        if explicit:
            playlistSongs.insert(1,("SAFEHARBOR",44))
            additionalLiners.extend([("SAFEHARBOR",44,20*60), ("SAFEHARBOR",44,40*60)])
        
        for linerName, linerLength, linerTime in additionalLiners:
            i = closestTimeSlot(linerTime,playlistSongs)
            if i < 0:
                raise RuntimeError("Error with liner: cannot insert "+linerName+" with playlist times")
            playlistSongs.insert(i,(linerName, linerLength))
        
            lines.append()

        with open('_'.join([fName,playlists[playlistI][1],str(playlistI).zfill(lenOfNum-floor(log10(playlistI)))])+'.tsv' , 'w') as f:
            for track in playlistSongs:
                f.writeline("\t".join(["+", track[0], "AUDIO"]))

    except RuntimeError as re:
        handleError(re)

