import os,sys,Levenshtein,pickle, postgresql as pg
sys.path.append("packages")
from libzarv import *
from database import databaseCon

def main():
  if len(sys.argv)!= 2:
    print("Error: recieved wrong number of args")
    exit(1)
  credentials = getCreds()
  try:
    db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_passwd']+'@localhost/'+credentials['db_name'])
  except Exception:
    print("Error: cannot connect to database\n")
    exit(1)
  print("Zarvox database are online")
  try:
    items = list(db.prepare("SELECT spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches,"+sys.argv[1]+"_id,"+sys.argv[1]+" FROM "+sys.argv[1]+"s;").chunks())[0]
  except Exception:
    print("Error: cannot get "+sys.argv[1]+"s from db")
    exit(1)
  dbobj = databaseCon(db)
  update_pop = dbobj.db.prepare("UPDATE "+sys.argv[1]+"s SET popularity = $1 WHERE "+sys.argv[1]+"_id=$2")
  for item in items:
    pop = dbobj.updateGeneralPopularity(item[0:5],sys.argv[1])
    update_pop(pop,item[5])
    print("Updated "+sys.argv[1]+" "+item[6]+" with "+str(pop))

if  __name__ == '__main__':
  main()