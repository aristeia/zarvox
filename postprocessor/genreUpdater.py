import os,sys,pg,Levenshtein,cPickle as pickle
sys.path.append("packages")
from libzarv import *
from database import updateGenrePopularity, db

def main:
  global db
  try:
    db = pg.connect('zarvox', user='kups', passwd='fuck passwords')
  except Exception, e:
    print("Error: cannot connect to database\n"+str(e))
    exit(1)
  try:
    genres = db.query("SELECT genre_id,genre FROM genres;").getresult()
  except Exception,e:
    print("Error: cannot get genres from db"+str(e))
    exit(1)
  for genre in genres:
    print("Updating "+genre[1])
    updateGenrePopularity(genre[0])