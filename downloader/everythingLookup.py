import os,sys,whatapi,postgresql as pg, datetime, time, Levenshtein
import postgresql.driver as pg_driver
sys.path.extend(os.listdir(os.getcwd()))
from random import shuffle
from lookup import *
from libzarv import *
from urllib import parse
from html import unescape
from musicClasses import *
from database import databaseCon
from math import ceil,floor
from numpy.random import randint
from statistics import mean,pvariance as pvar
from SpinPapiClient import SpinPapiClient

#Download the top whatcd & lastfm & spotify albums' metadata via lookup
#Calc their downloadability and set that into db

apihandle = None
con = None 
client = None


def notBadArtist(group):
  return ('artist' in group 
    and group['artist'].lower()!='various artists')

def startup_tests(credentials):
  try:
    db = pg_driver.connect(
      user = credentials['db_user'],
      password = credentials['db_password'],
      host = 'localhost',
      port = 5432,
      database  = credentials['db_name'])
  except Exception as e:
    handleError(e, "Error: cannot connect to database")
    exit(1)
  print("Zarvox database are online")
  try:
    pingtest(['whatcd','spotify','music','lastfm'])
  except Exception as e:
    handleError(e,"Pingtest err")
    exit(1)
  print("Pingtest complete; sites are online")
  return db

def downloadGenreData(genre, maxDownloads):
  whatPages=[]
  popularity = ceil(maxDownloads*genre[1])+1
  x=0
  print("Getting metametadata for "+genre[0]+" with popularity of "+str(genre[1]))
  while len(whatPages)<popularity and (x==0 or len(what['response']['results']) > 1):
    x+=1
    what = apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x),category='Music')
    while what['status'] != 'success':
      print("Warning: status not successful for page "+str(x))
      what = apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x),category='Music')
    whatPages+=what['response']['results']
    print("Got "+str(len(what['response']['results']))+" from page "+str(x))
    if len(what['response']['results']) < 2:
      print("Going with just "+str(len(whatPages))+" anyway, not getting any more results")
  while len(whatPages) > popularity:
    whatPages.pop(randint(0, len(whatPages)))
  print("Downloading "+str(len(whatPages))+" albums' metadata for "+genre[0])
  return processedGroups(whatPages)

def processedGroups(whatPages):
  what_info=[]
  for group in whatPages:
    processedGroup = processData(group)
    if processedGroup != {}:
      what_info.append(processedGroup)
  return what_info

def processedTorsWithInfo(whatTors):
  what_info=[]
  # query = con.db.prepare("SELECT * FROM artists WHERE artist = $1 LIMIT 1")
  for tor in whatTors:
    try:
      whatGroup = apihandle.request("torrentgroup",id=tor['groupId'])
      if whatGroup['status']=='success': 
        torGroup = getTorrentMetadata(whatGroup['response'])
        if torGroup != {}:
          what_info.append(torGroup)
    except Exception as e:
      handleError(e,"Failed to get torrentgroup from what")
  print("Out of this group, "+str(len(what_info))+" good downloads")
  return what_info

def processData(group):
  if notBadArtist(group):
    whatGroup = apihandle.request("torrentgroup",id=group['groupId'])
    if whatGroup['status']=='success':
      try: 
        return getTorrentMetadata(whatGroup['response'], group['artist-credit-phrase'] if 'artist-credit-phrase' in group else None)
      except Exception as e:
        handleError(e,"Error with processData")
        return {}
  return {}

def processSongs(data, songData = []):
  albumName, artistsNames = data
  goodSongs = []
  print("Downloading song information for "+albumName+" by "+str(artistsNames))
  res = {}
  try:
    if type(artistNames) == str:
      metadata = processData(getAlbumArtistNames(albumName, artistsNames, apihandle))
    else:
      metadata = {'artists': artistNames, 'album': albumName, 'whatid': -1}
    artists = [artistLookup(x, apihandle, True, con) for x in metadata['artists']]
    res['artists'] = con.getArtistsDB(artists,True)
    print("Done with artists")
    metadata['artist_id'] = res['artists'][0]['select'][0]
    album = albumLookup(metadata,apihandle,con)
    res['album'] = con.getAlbumDB( album,True,db_artistid=res['artists'][0]['select'][0])
    print("Done with album "+res['album'][0]['response'][1])    
    res['artists_albums'] = con.getArtistAlbumDB(res['album'][0]['select'][0],True, [artist['select'][0] for artist in res['artists']])
    while len(songData) == 0 and len(artists)>0:
      songData = getSongs({'groupName':album.name, 'artist': artists.pop(0).name })
    if len(songData) == 0:
      print("Error: couldn't get song data")
      return songs
    print("Got song listing")
    songMetadata = []
    for song in songData:
      songMetadata.append({})
      songMetadata[-1]['name'], songMetadata[-1]['duration'] = song
    songs = [songLookup(metadata, song, '', con=con) for song in songMetadata]
    print("Got song information")
    lst = {
      'sp':[song.spotify_popularity for song in songs],
      'll':[song.lastfm_listeners for song in songs],
      'lp':[song.lastfm_playcount for song in songs],
      'kp':[song.kups_playcount for song in songs]
    }
    for song in songs:
      song.popularity = con.popularitySingle( 'songs'+albumName.replace(' ','_')+'_'+artistsNames.replace(' ','_'), 
        spotify_popularity=song.spotify_popularity,
        lastfm_listeners=song.lastfm_listeners,
        lastfm_playcount=song.lastfm_playcount,
        kups_playcount=song.kups_playcount,
        lists=lst)
    print("Got song relative popularity")
    res['song'] = con.getSongsDB(songs, True, db_albumid=res['album'][0]['select'][0])
    con.printRes(res)
    for s in songs:
      if s.length > 0 and len(s.name)>0:
        db_song = max(res['song'], key=lambda x: Levenshtein.ratio(s.name, x['select'][1]) - abs(((s.length-x['select'][4]) / s.length)))
        s.filename = db_song['select'][2]
        s.song_id = db_song['select'][0]
        s.length = db_song['select'][4]
        goodSongs.append(s)
  except Exception as e:
    handleError(e,"Error with processSongs")
  return goodSongs


def processInfo(metadata, songDict=None, kups_amt=0):
  if len(metadata) == 0:
    print("Not processing info")
    return {}
  res = {}
  try:
    artists = [artistLookup(x, apihandle, True, con) for x in metadata['artists']]
    for artist in artists:
      artist.kups_playcount+=kups_amt
    res['artists'] = con.getArtistsDB(artists,True)
    print("Done with artists")

    if 'album' in metadata:
      album = albumLookup(metadata,apihandle,con)
      album.kups_playcount+=kups_amt
      res['album'] = con.getAlbumDB( album,True,db_artistid=res['artists'][0]['select'][0])
      print("Done with album")
      res['artists_albums'] = con.getArtistAlbumDB(res['album'][0]['select'][0],True, [artist['select'][0] for artist in res['artists']])
      abgenres = con.getGenreDB( [x for x in album.genres.keys()], apihandle,'album_',True)
      album.genres = correctGenreNames(album.genres, abgenres)
    else:
      album = Album('')
      abgenres = []

    if songDict is not None:
      song = songLookup(metadata,songDict,'',con=con)
      song.kups_playcount+=kups_amt
      res['song'] = con.getSongsDB([song], True, db_albumid=res['album'][0]['select'][0])
      print("Done with tracks")
    
    argenres = con.getGenreDB( list(set([x for artist in artists for x in artist.genres.keys() if x not in album.genres])), apihandle,'artist_',True)
    for artist in artists:
      artist.genres = correctGenreNames(artist.genres, argenres)
    res['genre'] = abgenres+argenres
    print("Done with genres")

    if 'album' in metadata:
      res['album_genre'] = con.getAlbumGenreDB( album.genres, True,album=res['album'][0]['select'])
      print("Done with album genres")
    res['artist_genre'] = [lst for artist, dbartist in zip(artists,res['artists']) for lst in con.getArtistGenreDB( artist.genres, True,artist=dbartist['select'])]
    
    print("Done with artist genres")
    res['similar_artist'], res['other_artist'], res['other_similar'] = [],[],[]
    for artist,dbartist in zip(artists,res['artists']):
      temp = con.getSimilarArtistsDB(artist.similar_artists, apihandle, dbartist['select'],True)
      res['similar_artist'].extend(temp[0])
      res['other_artist'].extend(temp[1])
      res['other_similar'].extend(temp[2])
  except Exception as e:
    handleError(e,"Error with processInfo")   
  return res


def lookupGenre(conf,fields):
  genres = sorted(
      [ (x[0],percentValidation(x[1])) 
      for lst in con.db.prepare("SELECT genre,popularity FROM genres ORDER BY popularity DESC").chunks() 
      for x in lst],
    key=lambda x: x[1],
    reverse=True)
  maxDownloads = ceil(
    float(conf['percentile']) 
    * sum([int(x[0]) 
      for lst in con.db.prepare("SELECT COUNT(*) FROM albums").chunks() 
      for x in lst]))
  print("Downloading upto "+str(maxDownloads)+" of the top albums from upto "+str(len(genres))+" genres")
  for genre in genres:
    for x in downloadGenreData(genre, maxDownloads):
      con.printRes(processInfo(x),fields)

def lookupSelf(conf,fields,tpe):
  albums_artists = [tuple(x) for lst in con.db.prepare("SELECT albums.album, string_agg(artists.artist, ' & ') FROM albums LEFT JOIN artists_albums ON albums.album_id = artists_albums.album_id LEFT JOIN artists on artists.artist_id = artists_albums.artist_id GROUP BY albums.album").chunks() for x in lst if x is not None]
  if len(tpe) == 0:
    shuffle(albums_artists)
  elif tpe=='albumgenres':
    albumsims = {}
    for album, sim in [(x[0], percentValidation(x[1]))
      for lst in con.db.prepare("SELECT albums.album, album_genres.similarity  FROM albums LEFT JOIN album_genres ON albums.album_id = album_genres.album_id ").chunks() 
      for x in lst 
      if type(x[1]) is float]:
      if album not in albumsims:
        albumsims[album] = []
      albumsims[album].append(sim)
    albums_artists.sort(key=lambda x: pvar(albumsims[x[0]]) if x[0] in albumsims else 0)
  for album, artists in albums_artists:
    print("Updating "+album+" by "+artists)
    con.printRes(
      processInfo(
        processData(
          getAlbumArtistNames(album, artists, apihandle))
        ),
      fields)

def lookupTopAll(conf,fields,n):
  whatTop10 = apihandle.request("top10",limit=n)
  if whatTop10['status'] == 'success':
    for response in whatTop10['response'][::-1]:
      print("Downloading "+response["caption"])
      for result in processedTorsWithInfo(response['results']):
        res = processInfo(result)
        if len(res) > 0:
          con.printRes(res,fields)

def lookupKUPS(conf,fields):
  #con.db.execute("UPDATE artists set kups_playcount=artists_true_kups_playcount.sum from artists_true_kups_playcount where artists.artist_id = artists_true_kups_playcount.artist_id and artists.kups_playcount != artists_true_kups_playcount.sum")
  #con.db.execute("UPDATE albums set kups_playcount=albums_true_kups_playcount.sum from albums_true_kups_playcount where albums.album_id = albums_true_kups_playcount.album_id and albums.kups_playcount != albums_true_kups_playcount.sum")
  con.db.execute("DELETE from kupstracks_bad where badtrack_id < (select MAX(badtrack_id) from kupstracks_bad)")
  shouldnt_download = sum([int(x[0]) for lst in con.db.prepare("select badtrack_id from kupstracks_bad").chunks() for x in lst])
  wont_download = con.db.prepare("insert into kupstracks_bad (badtrack_id) values ($1)")
  for kupstrack_id in range(1,168000):
    if kupstrack_id > shouldnt_download:
      link = client.query({
        'method':'getSong',
        'EndDate':str(datetime.date.today()),
        'SongID':str(kupstrack_id)})
      spinres = lookup('spinitron','query',{'url':link})
      while 'success' not in spinres or not spinres['success']:
        time.sleep(2)
        spinres = lookup('spinitron','query',{'url':link})
      if spinres['results'] is not None:
        track = spinres['results']
        for obj in ['DiskName','ArtistName','SongName']:
          track[obj] = mbEscape(track[obj])
        print("Working on "+track['SongName']+' by '+track["ArtistName"]+", kups track "+str(kupstrack_id))
        if (len(track["ArtistName"]) > 0 and len(track["DiskName"]) > 0):
          whatGroup = getAlbumArtistNames(
            track["DiskName"],
            track["ArtistName"],
            apihandle,
            song=track["SongName"])
          if whatGroup is None:
            print("No valid whatgroup searched")
          else:
            if whatGroup['song'] is None:
              whatGroup['song'] = {}
              whatGroup['song']['name'], whatGroup['song']['duration'] = max(getSongs(whatGroup), key=lambda x: Levenshtein.ratio(x[0],track["SongName"]))
            print("True song of "+track["SongName"]+" is "+whatGroup['song']['name'])
            if not closeEnough([track["ArtistName"],track["DiskName"],track["SongName"]]
              , [whatGroup['artist'],whatGroup['groupName'],whatGroup['song']['name']]):
              print("Ratio of two is too low, so ditching")
            else:
              print("Downloading info for track "+whatGroup['song']['name'])
              res = processInfo(
                processData(
                  whatGroup),
                songDict=whatGroup['song'],
                kups_amt=1)
              if len(res) > 0:
                con.printRes(
                  res,
                  fields)
                wont_download(kupstrack_id)
                kupstrack_id = 0
      if kupstrack_id != 0:
        print("Didn't download track "+(track["SongName"] if "results" in spinres and spinres["results"] is not None else str(kupstrack_id))+", so won't download again")
        wont_download(kupstrack_id)

def lookupCSV(conf,fields):
  lines = []
  with open(sys.argv[2]) as csv:
    for line in csv:
      if len(line.strip())>1:
        lines.append([x.strip('*').strip() for x in line.split(',')])
  for line in lines:
    print("Working on "+(' - '.join(line)))
    if len(''.join(line)) > 0:
      if len(line)>1 and (len(line[1])>1 or (len(line)==3 and len(line[2])>1)): 
        whatGroup = getAlbumArtistNames(
          line[1],
          line[0],
          apihandle,
          song=(line[2] if len(line)==3 and len(line[2])>1 else None))
        if whatGroup is None:
          print("No valid whatgroup searched")
          metadata = {}
        else:
          if 'song' in whatGroup and whatGroup['song'] is None:
            whatGroup['song'] = {}
            whatGroup['song']['name'], whatGroup['song']['duration'] = max(getSongs(whatGroup), key=lambda x: Levenshtein.ratio(x[0],track["SongName"]))
          metadata = processData(whatGroup)      
      else:
        whatGroup = {}
        metadata = { 'artists': [getArtist(line[0],apihandle)] }
      if metadata != {}:
        if whatGroup != {}:
          print("Downloading info for "+whatGroup['artist']+' - '+whatGroup['groupName']+(' - '+whatGroup['song']['name'] if 'song' in whatGroup else ''))
        else:
          print("Just downloading artist data for "+(''.join(metadata['artists'])))
        res = processInfo(
          metadata,
          songDict=(whatGroup['song'] if 'song' in whatGroup else None),
          kups_amt=(int(sys.argv[3]) if len(sys.argv)>3 else 5))
        if len(res) > 0:
          con.printRes(
            res,
            fields)



def lookupAll(lookupType,conf,fields):
  if lookupType == 'genre':
    lookupGenre(conf,fields)
  elif len(lookupType)>8 and lookupType[:7] == 'whattop':
    lookupTopAll(conf,fields,int(lookupType[7:]))
  elif lookupType == 'kups':
    lookupKUPS(conf,fields)
  elif lookupType == 'csv' and len(sys.argv)>2:
    lookupCSV(conf,fields)
  elif 'update' in lookupType:
    lookupSelf(conf,fields, lookupType[6:] if len(lookupType)>6 else '')
  else:
    print("Error: didn't find a lookup type")
    exit(1)

def main(lookup=True):
  global apihandle,con,client
  credentials = getCreds()
  conf = getConfig()
  cookies = {'cookies':pickle.load(open('config/.cookies.dat', 'rb'))} if os.path.isfile('config/.cookies.dat') else {}
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], **cookies)
  client = SpinPapiClient(str.encode(credentials['spinpapi_userid']),str.encode(credentials['spinpapi_secret']),station='kups')
  db = startup_tests(credentials)
  con = databaseCon(db)
  if lookup:
    fields = con.getFieldsDB()
    lookupAll(sys.argv[1],conf,fields)
  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))


if  __name__ == '__main__':
  main(True)

  