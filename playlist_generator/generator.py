import numpy as np, sys,os, postgresql as pg, bisect, json, whatapi, threading, time, multiprocessing
sys.path.extend(os.listdir(os.getcwd()))
from random import random, randint 
import postgresql.driver as pg_driver
from math import ceil,floor, sqrt, pow
from getSimilarSong import playlistBuilder
from database import databaseCon
from libzarv import *
from statistics import mean,pstdev
from bisect import insort
from scipy.stats import expon, norm
sys.path.append("downloader")
import everythingLookup as eL

#to be defined in main()
albumsBest, current_playlist, con, getSongData = None, None, None, None
repeatsList, nonExplicitList = [], []

def startup_tests():
  #Check sys.argv for id_to_album
  credentials = getCreds()
  try:
    db = pg_driver.connect(
      user = credentials['db_user'],
      password = credentials['db_password'],
      host = 'localhost',
      port = 5432,
      database  = credentials['db_name'])
  except Exception as e:
    print("Error: cannot connect to database\n")
    print(e, file=sys.stderr)
    exit(1)
  print("Zarvox database are online")
  return db

def processSchedule():
  schedule = {'Sunday':[],'Monday':[],'Tuesday':[],'Wednesday':[],'Thursday':[],'Friday':[],'Saturday':[]}
  supergenres = {}
  with open("config/schedule.tsv") as tsv:
    for line in tsv:
      for day, value in zip(['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'], line.strip().split('\t')):
        schedule[day].append(value.split(','))
        for supergenre in schedule[day][-1]:
          if supergenre not in supergenres:
            supergenres[supergenre] = 0
          supergenres[supergenre] += len(schedule[day][-1])**(-1)
  maxGenre = max(supergenres.values())
  for supergenre in supergenres.keys():
    supergenres[supergenre] = maxGenre / supergenres[supergenre]
  return schedule, supergenres

def getitem(query):
  mysum = 0
  breakpoints = [] 
  for res in query:
    mysum += res[1]
    breakpoints.append(mysum)
  score = random() * mysum
  i = bisect.bisect(breakpoints, score)
  return query[i-1] 



def getStartingAlbum(subgenre, albums=[]):
  if len(albums) == 0:
    albums = sorted([[x[0],percentValidation(x[1])] for x in albumsBest(subgenre)], reverse=True)
  albums = albums[:ceil(len(albums)/10.0)+1]
  albums_rvar = norm(*norm.fit([x[1] for x in albums]))
  for album in albums:
    album[1] = albums_rvar.cdf(album[1])
  return getitem(albums)[0]


def generateSubgenre(bestPlaylistAlbumIds):
  subgenre_means = {}
  subgenre_sims = [(x[3],percentValidation(x[1]),percentValidation(x[2]))
    for album_id in bestPlaylistAlbumIds 
    for lst in current_playlist.selectTopGenres.chunks(album_id) 
    for x in lst]
  subgenre_poprvar = norm(*norm.fit([x[2]
    for x in subgenre_sims]))
  subgenre_simrvar = norm(*norm.fit([x[1]
    for x in subgenre_sims]))

  for key, val in [(x[0], 
    subgenre_simrvar.cdf(x[1]) / subgenre_poprvar.cdf(x[2]))
    for x in subgenre_sims]:
    if key not in subgenre_means:
      subgenre_means[key] = []
    subgenre_means[key].append(val)
  return max([
    (sum(x[1]), x[0]) 
    for x in subgenre_means.items()],
    key=lambda x:x[0])[1]


def genPlaylist(album_id, linerTimes={}, playlistLength=3600, production = True, playlistRepeats = False, genre='', subgenre=''):
  songs = []
  album_ids = [album_id]
  album_metadata = [tuple(current_playlist.printAlbumInfo(album_id))]

  def processNextAlbum(i):
    songData = [x for lst in getSongData.chunks(album_ids[i]) for x in lst]
    album_songs = sorted(
      [x for x in eL.processSongs(album_metadata[i], songData)
        if x.length > 0
        and x.length < playlistLength/2.0],
      key=lambda x: x.popularity, reverse=True)
    if genre != '' and genre in nonExplicitList:
      for s in album_songs[:]:
        if s.explicit:
          print("Removing "+s.name+" because it's explicit in a nonexplicit playlist")
          album_songs.remove(s)      
    if production:
      for s in album_songs[:]:
        if s.filename == '' or not os.path.isfile(s.filename):
          print("Removing "+s.name+" because it doesnt exist in the FS for production")
          album_songs.remove(s)
    if playlistRepeats:
      for s in album_songs[:]:
        if s.song_id not in repeatsList:
          print("Removing "+s.name+" because it hasnt already been played in a repeats playlist")
          album_songs.remove(s)    
    if len(album_songs) < 1:
      print("Warning: dropping album "+str(album_ids[i])+" because no songs are downloaded")
      current_playlist.blacklistAlbum(album_ids.pop(i))
      album_metadata.pop(i)
      return 0
    while len(album_songs) > max(10-floor(playlistLength/360), 3):
      album_songs.pop()
    if len(album_ids) > 10 and len(album_songs) > 2:
      album_songs.pop()
    songs.append(album_songs)
    return (sum([x.length*x.popularity for x in album_songs])
      / sum([x.popularity for x in album_songs]))

  def getAlbumThread(album_id):
    album_ids.append(current_playlist.getNextAlbum(album_id))
    album_metadata.append(tuple(current_playlist.printAlbumInfo(album_ids[-1])))

  minDuration = processNextAlbum(0)
  while minDuration < playlistLength:
    print("Currently have "+str(minDuration)+" out of "+str(playlistLength)+" seconds of music")
    if len(album_ids) < 1:
      print("Playlist generation cannot continue since first album was dropped")
      print(floor(time.time()*1000))
      return None
    getAlbumThread(album_ids[-1])
    minDuration+=processNextAlbum(len(album_ids)-1)
  print("All done getting album and song info")

  playlistEval = lambda x: sum([y for y in x[1] if y > 0])+(x[0]/playlistLength)
  def assessPlaylist(tracks, length, linerKeys):
    if len(tracks) == 0 or length >= playlistLength:
      return (abs(playlistLength-length), [-1 for temp in tracks])
    res = []
    threads = []
    resValues = {}
    resValues[playlistLength-length] = [-1 for temp in tracks]
    insort(res, playlistLength-length)
    for i in range(len(tracks[0])):
      l = 0
      ls = linerKeys[:]
      if len(linerKeys)>0 and int(linerKeys[0])*60 < length+tracks[0][i].length:
        l+=min(abs(int(linerKeys[0])*60-length), abs(int(linerKeys[0])*60-length-tracks[0][i].length))
        ls.pop(0)
      def myRun():
        x,y = assessPlaylist(tracks[1:],length+tracks[0][i].length, ls)
        resValues[x+l] = [i]+y
        insort(res, x+l)
      if float(len(tracks))/float(len(album_ids)) < 0.5 and multiprocessing.cpu_count()*2-1 > threading.active_count():
        t = threading.Thread(target=myRun)
        t.start()
        threads.append(t)
      else:
        myRun()
      if len(res)>0 and res[0] < 33:
        return min([p for p in list(resValues.items()) if p[0] < 33], key=playlistEval)
    if length==0:
      x,y = assessPlaylist(tracks[1:],length, linerKeys)
      resValues[x] = [-1]+y
      insort(res, x)
    for t in threads:
      if res[0] < 32:
        return min([p for p in list(resValues.items()) if p[0] < 33], key=playlistEval)
      t.join()
    i = 2
    while res[0] >= (15*i)+i:
      i+=1
    return min([p for p in list(resValues.items()) if p[0] < 15*i+i], key=playlistEval)

  bestPlaylist =  assessPlaylist(songs, 0, list(linerTimes.keys()))
  print("Done getting playlist info")

  bestPlaylistStr = ""
  bestPlaylistSongIds = []
  bestPlaylistAlbumIds = []
  bestPlaylistArtistIds = []
  esc = lambda x: x.replace('-', '_')
  print("Best Playlist:")
  for index, song, album_id in zip(bestPlaylist[1],songs, album_ids): 
    if index >=0 :
      temp = [list(x) for lst in current_playlist.selectAlbum.chunks(album_id) for x in lst]
      album = temp[0][1]
      if len(temp) == 2:
        artists += temp[0][2]+' & '+temp[1][2]
      elif len(temp) > 2:
        temp[-2][2] += ', and '+temp[-1][2]
        temp.pop()
        artists = ', '.join([r[2] for r in temp])
      else:
        artists = temp[0][2]
      secs = str(floor(song[index].length%60))
      if len(secs) == 1:
        secs = '0' + secs
      print('>> '
        + esc(artists) + ' - '
        + esc(album) + ' - '
        + esc(song[index].name)+  ' - '
        + str(floor(song[index].length/60)) + ':'
        + secs + ' <<')
      bestPlaylistStr+= (', '+esc(artists) + ' - '
        + esc(album) + ' - '
        + esc(song[index].name))
      bestPlaylistSongIds.append(song[index].song_id)
      bestPlaylistAlbumIds.append(album_id)
      bestPlaylistArtistIds.extend([x[3] for x in temp])
  if subgenre == "":
    subgenre = generateSubgenre(album_ids)
  subgenreInfo = [x for lst in con.db.prepare("SELECT supergenre,genre FROM genres WHERE genre_id = $1").chunks(subgenre) for x in lst][0]
  print("Subgenre is "+subgenreInfo[1])
  genre = subgenreInfo[0]
  print("Genre is "+genre)

  playlistHash = (hash(bestPlaylistStr) % (2**(32)-1)) - (2**(31))
  con.getPlaylistDB({
    'playlist_id' : playlistHash,
    'genre': genre,
    'subgenre': subgenre
    })
  con.getPlaylistSongsDB(bestPlaylistSongIds, db_playlist_id=playlistHash)
  for tableName, ids in [('album', bestPlaylistAlbumIds), ('artist', bestPlaylistArtistIds)]:
    updateStm = con.db.prepare("UPDATE "+tableName+"s SET PLAYCOUNT = PLAYCOUNT+1 WHERE "+tableName+"_id = $1")
    for i in ids:
      updateStm.chunks(i)

  print(floor(time.time()*1000))


def main():
  print(floor(time.time()*1000))
  db = startup_tests()
  eL.main(False)
  conf = getConfig()
  global albumsBest, current_playlist, con, getSongData, repeatsList, nonExplicitList
  albumsBest = db.prepare(
    "SELECT album_genres.album_id, album_genres.similarity from album_genres INNER JOIN albums on albums.album_id=album_genres.album_id WHERE "
    +("SUBSTRING(albums.folder_path,1,1) = '/' and albums.album_id in (select songs.album_id from songs where SUBSTRING(songs.filename,1,1) = '/') AND "
     if conf['production'] else "")
    +("albums.playcount>0 AND " if conf['playlistRepeats'] else "")
    +"album_genres.genre_id=$1")
  getSongData = db.prepare("SELECT songs.song, songs.length FROM songs WHERE songs.album_id=$1")
  if conf['playlistRepeats']:
    repeatsList = [x[0] for lst in db.prepare("select distinct song_id from playlist_song") for x in lst]
  nonExplicitList = conf['nonExplicitList']
  current_playlist = playlistBuilder(db)
  con = databaseCon(db)
  #Doing subgenre/album for "python3 genplaylist type id"
  if len(sys.argv) == 3:
    if sys.argv[1] == 'subgenre':
      genPlaylist(getStartingAlbum(int(sys.argv[2])), production = conf['production'], playlistRepeats = conf['playlistRepeats'],subgenre=int(sys.argv[2]))
    elif sys.argv[1] == 'album':
      current_playlist.fillAlbumsArtistsCache(int(sys.argv[2]))
      current_playlist.album_history.extend([int(sys.argv[2]) for i in range(5)])
      genPlaylist(int(sys.argv[2]), production = conf['production'], playlistRepeats = conf['playlistRepeats'])
    else:
      print("Error with arg1: not matching to album or subgenre:"+sys.argv[1])
      exit(1)
  elif len(sys.argv) != 1 and not (len(sys.argv) == 2 and sys.argv[1].strip().isdigit()):
    print("Error with args; needs some or none!")
    exit(1)
  else:
    if not os.path.isfile("config/schedule.tsv"):
      print("Error: no schedule file found. Write one and save it to config/schedule.tsv")
      exit(1)
    schedule, supergenres = processSchedule()
    if "correctGenreProportions" in conf and conf["correctGenreProportions"]:
      def getGenre(d,h):
        real_genre_vals = dict([x for lst in con.db.prepare("SELECT genre, COUNT(*) FROM playlists GROUP BY genre").chunks() for x in lst])
        for genre, val in supergenres.items():
          real_genre_vals[genre] = real_genre_vals[genre]*val
        mostDiff = min(list(real_genre_vals.items()), key=(lambda x: x[1]))
        print("Lowest corrected proportional genre is "+mostDiff[0]+" at "+str(mostDiff[1])+" playlistcount")
        return mostDiff[0]
    else:
      def getGenre(d,h):
        supergenresSum = sum([supergenres[y] for y in schedule[d][h]])
        print("Generating "+str(ceil(playlistLength/120))+"+ albums out of one of the following genres with the following weights (of which gets picked:")
        genres = [(x, supergenres[x]/supergenresSum) for x in schedule[d][h]]
        print('\t'+(',\t'.join([' : '.join(map(str,x)) for x in genres])))
        real_genre_vals = dict([x for lst in con.db.prepare("SELECT genre, COUNT(*) FROM playlists GROUP BY genre").chunks() for x in lst])
        if len(real_genre_vals) > 0 and any([x > 30 for x in real_genre_vals.values()]):
          print("Since real genre data in playlists present, here are the real proportions:")
          supergenresRealSum = sum([real_genre_vals[y[0]] for y in genres])
          print('\t'+(',\t'.join([' : '.join(map(str,x)) for x in [(y[0], real_genre_vals[y[0]]/supergenresRealSum) for y in genres]])))
          mostDiff = max([(x[0], ((x[1] - real_genre_vals[x[0]]/supergenresRealSum)/x[1])) for x in genres], key=(lambda x: x[1]))
          print("Biggest difference is in "+mostDiff[0]+" by "+str(mostDiff[1])+"%")
          return mostDiff[0]
        return getitem(genres)[0]

    print("Processed supergenres from schedule with frequencies")
    day = list(schedule.keys())[randint(0,6)]
    hour = randint(0,23)
    print("Starting on "+day+" at "+str(hour)+":00:00, and doing a 1-hour playlist for each hour henceforth")
    playlistLength = int(conf['playlistLength'])
    linerTimes = dict([ (t,l)
      for t, l in conf['liners'].items() 
      if (float(t)*60)+float(l) <= playlistLength])
    print("Doing liners during the following times:")
    for t, duration in sorted(list(linerTimes.items())):
      print('\t'+str(t)+':00 - '+str(t)+':'+str(duration))
    subgenres = dict([(x[0], list(x[1:]) if x[1] is not None else [0,x[2]]) for lst in db.prepare("SELECT genre_id, popularity, supergenre FROM genres").chunks() for x in lst])
    subgenres_rvars = {}
    for key in supergenres.keys():
      subgenres_rvars[key] = norm(*norm.fit([x[0] for x in subgenres.values() if x[1]==key]))
    genresUsed = db.prepare("SELECT subgenre, COUNT(subgenre) FROM playlists WHERE playlists.genre = $1 GROUP BY playlists.subgenre")
    getSubgenreName = db.prepare("SELECT genres.genre FROM genres WHERE genres.genre_id = $1") 
    playlistGenerations = int(sys.argv[1]) if len(sys.argv) == 2 else int(conf['playlistGenerations'])

    #done with setup; real work now
    for g in range(playlistGenerations):
      genre = getGenre(day, hour)
      print("Picked "+genre)
      for lst in genresUsed.chunks(genre):
        for subgenre,plays in lst:
          if len(subgenres[subgenre]) == 2:
            subgenres[subgenre].append(plays)
      genresUsed_rvar = expon(*expon.fit([x[2] if len(x)>2 else 0 for x in subgenres.values() if x[1]==genre]))
      possible_subgenres = sorted([ (key,
        ((1-genresUsed_rvar.cdf(val[2] if len(val)>2 else 0))+subgenres_rvars[genre].cdf(val[0])) )
        for key,val in subgenres.items()
        if val[1]==genre], key=lambda x: x[1])
      albums = []
      while len(albums) < 2 and len(possible_subgenres)>0:
        subgenre, temp = getitem(possible_subgenres)
        possible_subgenres.remove((subgenre,temp))
        albums = sorted([[x[0],percentValidation(x[1])] for x in albumsBest(subgenre)], reverse=True)
      if len(possible_subgenres)==0:
        print("Error: couldn't find a suitable subgenre for genre")
      else:
        subgenreName = list(getSubgenreName(subgenre))[0][0]
        print("Picked "+subgenreName+" as a starting subgenre")
        startingAlbum = getStartingAlbum(subgenre, albums)
        current_playlist.fillAlbumsArtistsCache(startingAlbum, genre)
        current_playlist.album_history.extend([a[0] for a in albums[:ceil(len(albums)/20.0)+1] if a[0] in current_playlist.albums])
        try:
          genPlaylist(startingAlbum, linerTimes, playlistLength, production = conf['production'], playlistRepeats = conf['playlistRepeats'], genre=genre)
        except Exception as e:
          handleError(e,"Error with generating this playlist; going to keep making new ones")

      current_playlist = playlistBuilder(db)
      hour = (hour + 1) % 23
      if hour==0:
        weekdays = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
        day = weekdays[(weekdays.index(day)+1 ) % 7]



if  __name__ == '__main__':
  main()


