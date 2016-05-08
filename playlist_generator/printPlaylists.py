import sys,os,postgresql,io
sys.path.extend(os.listdir(os.getcwd()))
from database import databaseCon
from libzarv import handleError
from bisect import insort
from math import floor, ceil, log10

fName = "playlists/playlists"
if len(sys.argv) > 1:
    fName = "playlists/"+sys.argv[1]
    if ".tsv" in fname:
        fName = fName.replace(".tsv", "")

con = databaseCon()

playlists = [x 
    for lst in con.db.prepare("SELECT * FROM playlists").chunks() 
    for x in lst]

selectSongs = con.db.prepare(
    '''SELECT songs.filename, songs.length, songs.explicit, albums.folder_path FROM playlist_song 
    INNER JOIN songs ON songs.song_id = playlist_song.song_id 
    INNER JOIN albums ON songs.album_id = albums.album_id 
    WHERE playlist_song.playlist_id = $1 ORDER BY playlist_song.interval
    ''')

def closestTimeSlot(desiredTime, songIndecies):
    return songIndecies.index(
        min(songIndecies, 
            key=lambda x: abs(desiredTime-x)))


def bestLinerSlot(linerIndecies,songIndecies):
    return songIndecies.index(
        max(songIndecies, 
            key=lambda x: min([abs(li-x) for li in linerIndecies])))

lenOfNum = int(1+floor(log10(len(playlists))))

songPathsNeeded = []

for playlistI in range(len(playlists)):
    try:
        print("On playlist "+str(playlistI+1)+"/"+str(len(playlists)))
        playlistSongs = []

        for lst in selectSongs.chunks(playlists[playlistI][0]):
            for song in lst:
                if os.path.isfile(song[0]):
                    playlistSongs.append(song[:3])
                elif os.path.isfile(song[3]+'/'+song[0]):
                    playlistSongs.append([song[3]+'/'+song[0]]+song[1:3])
                else:
                    print("Ditching song "+song[0]+" because doesn't exist in FS")

        explicit = any([song[2] for song in playlistSongs])     
        if any([len(song[0]) < 1 for song in playlistSongs]):
            raise RuntimeError("Issue with this playlist "+str(playlistI+1)+", a song isnt in the db!")

        firstSong = playlistSongs[0][:]
        songIndecies = [98]
        for song in playlistSongs[:-1]:
            songIndecies.append(songIndecies[-1]+song[1])
        playlistSongs.insert(0,("LEGALIDRANDOMIZER",44))
        playlistSongs.insert(1,("UNDERWRITER",54))
        linerIndecies = [0,44]
        additionalLiners = [("LINERSRANDOMIZER",21,15*60),("PSARANDOMIZER",30,30*60),("LINERSRANDOMIZER",21,45*60)]
        if explicit:
            playlistSongs.insert(1,("SAFEHARBOR",44))
            linerIndecies.append(88)
            for i in range(len(songIndecies)):
                songIndecies[i]+=44
            insort(additionalLiners,("SAFEHARBOR",44,20*60))
            insort(additionalLiners,("SAFEHARBOR",44,40*60))
        
        for linerName, linerLength, linerTime in additionalLiners:
            i = closestTimeSlot(linerTime,songIndecies)
            linerIndecies.append(songIndecies[i])
            playlistSongs.insert(i+len(linerIndecies)-1,(linerName, linerLength))
            for e in range(i,len(songIndecies)):
                songIndecies[e]+=linerLength
            
        print("Done adding traditional liners, now padding with extras")

        for o in range(ceil((3600-sum([s[1] for s in playlistSongs]))/21)):
            i = bestLinerSlot(linerIndecies,songIndecies)
            insort(linerIndecies,songIndecies[i])
            playlistSongs.insert(i+sum([1 for x in linerIndecies if x<songIndecies[i]]),("LINERSRANDOMIZER", 21))
            for e in range(i+1,len(songIndecies)):
                songIndecies[e]+=21
            
        playlistSongs.append(("LINERSRANDOMIZER",21))
        playlistSongs.append(("LINERSRANDOMIZER",21))

        
        print("Done with liners\nWriting playlist "+str(playlistI+1))
        zf = (lenOfNum-1) if (playlistI == 0) else (lenOfNum-int(floor(log10(playlistI))))
        with io.open('_'.join([fName,playlists[playlistI][1]+("-explicit" if explicit else ""),str(playlistI).zfill(zf)]).replace(" ","")+'.psv' , 'w',encoding='utf8') as f:
            for i in range(2):
                for track in playlistSongs:
                    f.write("|".join(["+", track[0], "AUDIO"]) + "\n")
                    if len(track) > 3:
                        line = '/'.join([track[3],track[0]])
                        if line not in songPathsNeeded:
                            insort(songPathsNeeded,line)
        print("Wrote playlist "+str(playlistI+1))

    except RuntimeError as re:
        handleError(re)

print("Finished all playlists!")

with io.open(fName+'_songs.txt' , 'w', encoding='utf8') as f:
    for line in songPathsNeeded:
        f.write(line + "\n")