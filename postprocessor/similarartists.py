import sys,os,pg
sys.path.append("packages")
import whatapi
from libzarv import *
from libzarvclasses import *

db=None
apihandle=None

def startup_tests():
  global db
  try:
    db = pg.connect('zarvox', user='kups', passwd='fuck passwords')
  except Exception, e:
    print("Error: cannot connect to database\n"+str(e))
    exit(1)
  print("Zarvox database are online")
  try:
    pingtest(['whatcd'])
  except Exception, e:
    print(e)
    exit(1)
  print("Pingtest complete; sites are online")


def main:
  global db,credentials,conf,apihandle
  conf = getConfig()
  credentials = getCreds()
  cookies = pickle.load(open('config/.cookies.dat', 'rb'))
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
  db_artists = getArtists()
  artists = {}
  for db_artist in iter(db_artists):
    artists[db_artist[1]] = db_artist
  for artist in artists.iteritems():
    obj = artistLookup(artist[1])
    for other,val in obj.similar_artists:
      if other not in artists:
        artists.append(artistLookup(other))
  for artist_obj in artists:
    getArtistDB(artist_obj)



if  __name__ == '__main__':
  main()
