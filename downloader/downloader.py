import sys,os,math,datetime,pg
sys.path.append("packages")
import whatapi
from libzarv import *


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
#classvars
credentials = {}
apihandle = None
db = None

#Usage (to be ran from root of zarvox): python downloader.py
def main():
  global db,credentials,apihandle
  #get all subgenres
  startup_tests()
  genres = db.query("SELECT * FROM genres;").getresult()
  hour = datetime.datetime.now().hour
  credentials = getCreds()
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'])
  for genre in genres:
    #download based on pop
    data = apihandle.request("top10", limit=10)
    
  #make folder for it, then make .info file with metadata
  #download a few (by popularity) torrents of each




if  __name__ == '__main__':
  main()