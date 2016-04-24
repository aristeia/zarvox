import os,sys,Levenshtein,pickle, postgresql as pg
sys.path.extend(os.listdir(os.getcwd()))
from libzarv import *
from database import databaseCon

def main():
  credentials = getCreds()
  try:
    db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_password']+'@localhost/'+credentials['db_name'])
  except Exception as e:
    print("Error: cannot connect to database\n")
    print(e)
    exit(1)
  print("Zarvox database are online")
  try:
    genres = [x for lst in db.prepare("SELECT genre_id,genre FROM genres ORDER BY 1").chunks() for x in lst]
  except Exception as e:
    print("Error: cannot get genres from db")
    print(e)
    exit(1)
  dbobj = databaseCon(db)
  i=0
  for genre1,name1 in genres[1:]:
    i+=1
    for genre2,name2 in genres[:i]:
      similarity = dbobj.updateGenreSimilarity(genre1, genre2)
      print("Similarity of "+name1+" and "+name2+" is "+str(similarity))


if  __name__ == '__main__':
  main()