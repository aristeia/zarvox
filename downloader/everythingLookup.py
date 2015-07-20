#Download the top whatcd & lastfm & spotify albums' metadata via lookup
#Calc their downloadability and set that into db

def main():
  credentials = getCreds()
  db = startup_tests(sys.argv,credentials)
  conf = getConfig()
  cookies = pickle.load(open('config/.cookies.dat', 'rb'))
  apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
  