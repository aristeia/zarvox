import os,sys,pg,Levenshtein,cPickle as pickle, postgresql as pg
sys.path.append("packages")
from libzarv import *
from database import updateGenrePopularity, db

def main:
  credentials = getCreds()
  try:
    db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_passwd']+'@localhost/'+credentials['db_name'])
  except Exception:
    print("Error: cannot connect to database\n")
    exit(1)
  print("Zarvox database are online")
  try:
    genres = list(db.prepare("SELECT genre_id,genre FROM genres;").chunks())[0]
    albums = list(db.prepare("SELECT spotify_popularity, lastfm_listeners, lastfm_playcount, whatcd_seeders, whatcd_snatches FROM albums;").chunks())[0]
    artists = list(db.prepare("SELECT spotify_popularity, lastfm_listeners, lastfm_playcount, whatcd_seeders, whatcd_snatches FROM artists;").chunks())[0]
  except Exception,e:
    print("Error: cannot get genres from db"+str(e))
    exit(1)
  con = databaseCon(db)
  for genre in genres:
    print("Updating "+genre[1])
    con.updateGenrePopularity(genre[0])