import os,sys,whatapi,postgresql as pg, datetime, time, Levenshtein
sys.path.append("packages")
from random import shuffle
from lookup import *
from libzarv import *
from urllib import parse
from html import unescape
from libzarvclasses import *
from database import databaseCon
from math import ceil,floor
from statistics import mean
from SpinPapiClient import SpinPapiClient

#Download the top whatcd & lastfm & spotify albums' metadata via lookup
#Calc their downloadability and set that into db

apihandle = None
con = None 
client = None

def notBadArtist(group):
  return ('artist' in group 
    and group['artist'].lower()!='various artists')

def startup_tests(args, credentials):
  if len(args) != 2:
    print("Error: postprocessor received wrong number of args")
    exit(1)
  try:
    db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_password']+'@localhost/'+credentials['db_name'])
  except Exception as e:
    print("Error: cannot connect to database",file=sys.stderr)
    print(e,file=sys.stderr)
    exit(1)
  print("Zarvox database are online")
  try:
    pingtest(['whatcd','spinitron'])
  except Exception as e:
    print(e,file=sys.stderr)
    exit(1)
  print("Pingtest complete; sites are online")
  return db

def downloadGenreData(genre):
  #global apihandle
  whatPages=[]
  popularity = (ceil(10*(2*genre[1])**2) if genre[1] is not None else 0) + 3
  x=0
  print("Downloading "+str(popularity)+" for "+genre[0])
  while len(whatPages)<popularity:
    x+=1
    time.sleep(5)
    what = apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x),category='Music')
    while what['status'] != 'success':
      time.sleep(10)
      what = apihandle.request("browse",searchstr='',order_by='seeders',taglist=parse.quote(genre[0],'.'),page=(x),category='Music')
    whatPages+=what['response']['results']
  return processedGroups(whatPages[0:popularity])

def processedGroups(whatPages):
  #global apihandle
  what_info=[]
  for group in whatPages:
    processedGroup = processData(group)
    if processedGroup != {}:
      what_info.append(processedGroup)
  return what_info

def processedTorsWithInfo(whatTors):
  #global apihandle,con
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
      print("Failed to get torrentgroup from what",file=sys.stderr)
      print(e,file=sys.stderr)
  print("Out of this group, "+str(len(what_info))+" good downloads")
  return [processInfo(x) for x in what_info]

def processData(group):
  if notBadArtist(group):
    whatGroup = apihandle.request("torrentgroup",id=group['groupId'])
    if whatGroup['status']=='success':
      try: 
        return getTorrentMetadata(whatGroup['response'], group['artist-credit-phrase'] if 'artist-credit-phrase' in group else None)
      except Exception as e:
        print(e, file=sys.stderr)
        return {}
  return {}

def processInfo(metadata, kups_song=None):
  #global apihandle,con
  if len(metadata) == 0:
    print("Not processing info")
    return {}
  res = {}
  try:
    artists = [artistLookup(x, apihandle, True, con) for x in metadata['artists']]
    if kups_song is not None:
      for artist in artists:
        artist.kups_playcount+=1
    res['artists'] = con.getArtistsDB(artists,True)
    print("Done with artists")
    album = albumLookup(metadata,apihandle,con)
    if kups_song is not None:
      album.kups_playcount+=1
    res['album'] = con.getAlbumDB( album,True,db_artistid=res['artists'][0]['select'][0])
    print("Done with album")
    if kups_song is not None:
      song = songLookup(metadata,kups_song,'',con=con)
      song.kups_playcount+=1
      res['song'] = con.getSongsDB([song], True, db_albumid=res['album'][0]['select'][0])
      print("Done with tracks")
    res['artists_albums'] = con.getArtistAlbumDB(res['album'][0]['select'][0],True, [artist['select'][0] for artist in res['artists']])
    
    abgenres = con.getGenreDB( [x for x in album.genres.keys()], apihandle,'album_',True)
    argenres = con.getGenreDB( list(set([x for artist in artists for x in artist.genres.keys() if x not in album.genres])), apihandle,'artist_',True)
    res['genre'] = abgenres+argenres
    album.genres = correctGenreNames(album.genres, abgenres)
    for artist in artists:
      artist.genres = correctGenreNames(artist.genres, argenres)
    print("Done with genres")

    res['album_genre'] = con.getAlbumGenreDB( album.genres, True,album=res['album'][0]['select'])
    print("Done with album genres")
    # res['artist_genre'] = []
    # for artist, dbartist in zip(artists,res['artists']):
    #   # print(artist,dbartist)
    #   for lst in con.getArtistGenreDB( artist.genres, True,artist=dbartist['select']):
    #     # print(lst)
    #     res['artist_genre'].append(lst)
    res['artist_genre'] = [lst for artist, dbartist in zip(artists,res['artists']) for lst in con.getArtistGenreDB( artist.genres, True,artist=dbartist['select'])]
    
    print("Done with artist genres")
    res['similar_artist'], res['other_artist'], res['other_similar'] = [],[],[]
    for artist,dbartist in zip(artists,res['artists']):
      temp = con.getSimilarArtistsDB(artist.similar_artists, apihandle, dbartist['select'],True)
      res['similar_artist'].extend(temp[0])
      res['other_artist'].extend(temp[1])
      res['other_similar'].extend(temp[2])
  except Exception as e:
    print("Error with processInfo")
    print(e, file=sys.stderr)
  return res

def lookupAll(lookupType,conf,fields):
  #global apihandle,con
  if lookupType == 'genre':
    lookupGenre(conf,fields)
  if len(lookupType)>8 and lookupType[:7] == 'whattop':
    lookupTopAll(conf,fields,int(lookupType[7:]))
  if lookupType == 'kups':
    lookupKUPS(conf,fields)
  else:
    print("Error: didn't find a lookup type")
    exit(1)

def lookupGenre(conf,fields):
  #global apihandle,con
  genres = [x for lst in con.db.prepare("SELECT genre,popularity FROM genres ORDER BY popularity DESC LIMIT 300").chunks() for x in lst]
  shuffle(genres)
  for genre in genres:
    for x in downloadGenreData(genre):
      con.printRes(processInfo(x),fields)

def lookupTopAll(conf,fields,n):
  #global apihandle,con
  whatTop10 = apihandle.request("top10",limit=n)
  if whatTop10['status'] == 'success':
    for response in whatTop10['response'][::-1]:
      print("Downloading "+response["caption"])
      for result in processedTorsWithInfo(response['results']):
        con.printRes(result,fields)

def lookupKUPS(conf,fields):
  #global apihandle,con,client
  con.db.execute("UPDATE artists set kups_playcount=artists_true_kups_playcount.sum from artists_true_kups_playcount where artists.artist_id = artists_true_kups_playcount.artist_id and artists.kups_playcount != artists_true_kups_playcount.sum")
  con.db.execute("UPDATE albums set kups_playcount=albums_true_kups_playcount.sum from albums_true_kups_playcount where albums.album_id = albums_true_kups_playcount.album_id and albums.kups_playcount != albums_true_kups_playcount.sum")
  already_downloaded = sum([int(x[0]) for lst in con.db.prepare("select sum(kups_playcount) from songs").chunks() for x in lst])
  shouldnt_download = [int(x[0]) for lst in con.db.prepare("select badtrack_id from kupstracks_bad").chunks() for x in lst]
  wont_download = con.db.prepare("insert into kupstracks_bad (badtrack_id) values ($1)")
  for kupstrack_id in range(1,163950):
    if kupstrack_id in shouldnt_download:
      pass
    elif already_downloaded > 0:
      already_downloaded -= 1
    else:
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
        print("Working on "+track['SongName']+' by '+track["ArtistName"])
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
            if mean(
              list(
                map(lambda z: Levenshtein.ratio(*z),
                  zip([track["ArtistName"],track["DiskName"],track["SongName"]],
                    [whatGroup['artist'],whatGroup['groupName'],whatGroup['song']['name']])))) < 0.5:
              print("Ratio of two is too low, so ditching")
            else:
              print("Downloading info for track "+whatGroup['song']['name'])
              res = processInfo(
                      processData(
                        whatGroup),
                      kups_song=whatGroup['song'])
              if len(res) > 0:
                con.printRes(
                  res,
                  fields)
                kupstrack_id = 0
      if kupstrack_id != 0:
        print("Didn't download track "+(track["SongName"] if "results" in spinres and spinres["results"] is not None else str(kupstrack_id))+", so won't download again")
        wont_download(kupstrack_id)



def main():
  global apihandle,con,client
  credentials = getCreds()
  db = startup_tests(sys.argv,credentials)
  conf = getConfig()
  cookies = {'cookies':pickle.load(open('config/.cookies.dat', 'rb'))} if os.path.isfile('config/.cookies.dat') else {}
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], **cookies)
  client = SpinPapiClient(str.encode(credentials['spinpapi_userid']),str.encode(credentials['spinpapi_secret']),station='kups')
  con = databaseCon(db)
  fields = con.getFieldsDB()
  lookupAll(sys.argv[1],conf,fields)
  pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))


if  __name__ == '__main__':
  main()

  