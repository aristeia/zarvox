import numpy as np, sys,os, postgresql as pg, bisect, json, whatapi, threading, time
from random import random, randint 
import postgresql.driver as pg_driver
from math import ceil,floor, sqrt
from getSimilarSong import playlistBuilder
sys.path.append("packages")
from database import databaseCon
from libzarv import *
from statistics import mean
from bisect import insort
from scipy.stats import chi2, norm
sys.path.append("downloader")
import everythingLookup as eL


def startup_tests():
  #Check sys.argv for id_to_album
  if len(sys.argv) != 1:
    print("Error: postprocessor received wrong number of args")
    exit(1)
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

def getitem(query):
  mysum = 0
  breakpoints = [] 
  for res in query:
    mysum += res[1]
    breakpoints.append(mysum)
  score = random() * mysum
  i = bisect.bisect(breakpoints, score)
  return query[i-1] 

def main():
  if not os.path.isfile("config/schedule.tsv"):
    print("Error: no schedule file found. Write one and save it to config/schedule.tsv")
    exit(1)
  conf = getConfig()
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
  print("Processed supergenres from schedule with frequencies")
  day = list(schedule.keys())[randint(0,6)]
  hour = randint(0,23)
  print("Starting on "+day+" at "+str(hour)+":00:00, and doing a 1-hour playlist for each hour henceforth")
  linerTimes = json.loads(conf['liners'])
  print("Doing liners during the following times:")
  for t, duration in sorted(list(linerTimes.items())):
    print('\t'+str(t)+':00 - '+str(t)+':'+str(duration))
  db = startup_tests()
  current_playlist = playlistBuilder(db, 0.0025)
  eL.main()
  subgenres = dict([(x[0], list(x[1:]) if x[1] is not None else [0,x[2]]) for lst in db.prepare("SELECT genre_id, popularity, supergenre FROM genres").chunks() for x in lst])
  subgenres_rvars = {}
  for key in supergenres.keys():
    subgenres_rvars[key] = norm(*norm.fit([x[0] for x in subgenres.values() if x[1]==key]))
  genresUsed = db.prepare("SELECT genres.genre, COUNT(subgenre) FROM playlists FULL OUTER JOIN genres ON genres.genre = playlists.subgenre WHERE playlists.genre = $1 GROUP BY genres.genre")
  albumsBest = db.prepare("SELECT album_id, similarity from album_genres where genre_id=$1")
  getSubgenreName = db.prepare("SELECT genres.genre FROM genres WHERE genres.genre_id = $1") 
  

  #done with setup; real work now
  while True:
    supergenresSum = sum([supergenres[y] for y in schedule[day][hour]])
    print("Generating 20+ albums out of one of the following genres with the following weights (of which gets picked:")
    genres = [(x, supergenres[x]/supergenresSum) for x in schedule[day][hour]]
    print('\t'+(',\t'.join([' : '.join(map(str,x)) for x in genres])))
    genre, temp = getitem(genres)
    print("Picked "+genre)
    for lst in genresUsed(genre):
      for subgenre,plays in lst:
        if len(subgenres[subgenre]) == 2:
          subgenres[subgenre].append(plays)
    genresUsed_rvar = chi2(*chi2.fit([x[2] if len(x)>2 else 0 for x in subgenres.values() if x[1]==genre]))
    possible_subgenres = sorted([ (key,
      ((1-genresUsed_rvar.cdf(val[2] if len(val)>2 else 0))+subgenres_rvars[genre].cdf(val[0])) )
      for key,val in subgenres.items()
      if val[1]==genre], key=lambda x: x[1])
    albums = []
    while len(albums) < 2:
      subgenre, temp = getitem(possible_subgenres)
      possible_subgenres.remove((subgenre,temp))
      albums = sorted([list(lst) for lst in albumsBest(subgenre) if not np.isnan(lst[1])])
    subgenreName = list(getSubgenreName(subgenre))[0][0]
    print("Picked "+subgenreName+" as a starting subgenre")
    albums_rvar = norm(*norm.fit([x[1] for x in albums]))
    for album in albums:
      album[1] = albums_rvar.cdf(album[1])
    album_id, temp = getitem(albums)
    songs = []
    minDuration = 0
    def processNextAlbum(minDuration, ti):
      eL.main()
      album_songs = sorted(
        eL.processSongs(
          current_playlist.printAlbumInfo(album_ids[ti])),
        key=lambda x: x.popularity, reverse=True)
      while len(album_songs) > 5:
        album_songs.pop()
      songs.append(album_songs)
      minDuration += min([x.length for x in album_songs])
      ti+=1

    album_ids = [album_id]
    def getAlbumThread(album_id):
      album_ids.append(current_playlist.getNextAlbum(album_id))
    
    ti = 0
    print("Starting new processor thread")
    threads = []
    threads.append(threading.Thread(target = processNextAlbum, args = (minDuration, ti), name = 'processor'))
    threads[-1].start()
    while minDuration < 3000:
      if threading.active_count() < 3:
        if any([t.name == 'processor' for t in threading.enumerate()]):
          if ti >= len(album_ids)-3:
            print("Starting new getter thread")
            threads.append(threading.Thread(target = getAlbumThread, args = (album_ids[-1],), name = 'getter'))
            threads[-1].start()
        else:
          print("Starting new processor thread")
          threads.append(threading.Thread(target = processNextAlbum, args = (minDuration, ti), name = 'processor'))
          threads[-1].start()
      time.sleep(2)
    while ti < len(album_ids)-1:
      processNextAlbum(minDuration, ti)


    
    # minDuration += processNextAlbum(minDuration)
    # print("minDuration is "+str(minDuration))
    # while minDuration < 4500:
    #   getAlbumThread(album_id)
    #   processNextAlbum(minDuration)
    #   print("minDuration is "+str(minDuration))
    exit(0)


if  __name__ == '__main__':
  main()


