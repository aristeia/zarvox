import os,sys,Levenshtein,pickle, postgresql as pg
sys.path.append("packages")
from libzarv import *
from database import databaseCon

def main():
  credentials = getCreds()
  try:
    db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_passwd']+'@localhost/'+credentials['db_name'])
  except Exception:
    print("Error: cannot connect to database\n")
    exit(1)
  print("Zarvox database are online")
  try:
    genres = list(db.prepare("SELECT genre_id,genre FROM genres;").chunks())[0]
  except Exception:
    print("Error: cannot get genres from db")
    exit(1)
  dbobj = databaseCon(db)
  for genre in genres:
    dbobj.updateGenrePopularity(genre)
    

if  __name__ == '__main__':
  main()