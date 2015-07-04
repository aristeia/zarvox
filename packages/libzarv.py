import sys,os,re,datetime,subprocess, json, urllib2, Levenshtein
cocksucker = re.compile('cock.{,12}suck')
tag = re.compile('\W')

sites = {
  'whatcd':'www.what.cd',
  'lastfm':'www.last.fm',
  'spotify':'www.spotify.com',
  'lyrics':'lyrics.wikia.com',
  'pandora':'www.pandora.com',
  'music':'www.musicbrainz.com' 
}

queries = {
  'lastfm':{
    'song': 'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key=013cecffb4bcce695153d857e4760a2c&artist=@artist&track=@song&format=json',
    'album': 'http://ws.audioscrobbler.com/2.0/?method=album.getInfo&api_key=013cecffb4bcce695153d857e4760a2c&artist=@artist&album=@album&format=json',
    'albumtags': 'http://ws.audioscrobbler.com/2.0/?method=album.gettoptags&artist=@artist&album=@album&api_key=013cecffb4bcce695153d857e4760a2c&format=json',
    'artist': 'http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&api_key=013cecffb4bcce695153d857e4760a2c&artist=@artist&format=json',
    'artisttags': 'http://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&artist=@artist&api_key=013cecffb4bcce695153d857e4760a2c&format=json',
    'artistsimilar': 'http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist=@artist&api_key=013cecffb4bcce695153d857e4760a2c&format=json'
    },
  'spotify':{
    'song': "https://api.spotify.com/v1/search?q=@song @artist @album&type=album&market=US&limit=10",
    'album': "https://api.spotify.com/v1/search?q=@album @artist&type=album&market=US&limit=5",
    'artist': "https://api.spotify.com/v1/search?q=@artist&type=album&market=US&limit=5",
    'id': "https://api.spotify.com/v1/@type/@id?market=ES"
    },
  'lyrics': {
    'song':"http://lyrics.wikia.com/api.php?action=query&prop=revisions&format=json&rvprop=content&titles=@artist:@song"
    }
}

def countToJSON(listOfTags, tagType = 'count'):
  return dict(map(lambda x: (x["name"].lower(),x[tagType]),listOfTags))


def massrep(args,query):
  if len(args)==0:
    return query
  return massrep(args[1:],query.replace('@'+args[0][0],args[0][1]))

def lookup(site, medium, args):
  items = args.items()
  if site in ['lastfm','spotify']:
    items = [(x,y.replace(' ','+')) for (x,y) in items]
  elif site=='lyrics':
    items = [(x,y.replace(' ','_')) for x,y in items]
  query = massrep(items,queries[site][medium])
  try:
    res = urllib2.urlopen(query)
  except Exception, e:
    print("Error: cannot reach site "+site+"\n"+str(e))
    exit(1)
  try:
    return json.load(res)
  except Exception, e:
    print("Error: cannot convert to json\n"+str(e))
    exit(1)

def is_safe_harbor():
	return (datetime.datetime.now().time() < time(6) or datetime.datetime.now().time() > time(22))

def is_explicit(text):
	return ('fuck' in text or 'cunt' in text or self.cocksucker.match(text))

def levi_misc(x,y, thing):
  return y if Levenshtein.ratio(y,thing)>Levenshtein.ratio(x,thing) else x

def pingtest(args):
  print("Pinging "+sites[args[0]])
  try:
    print(subprocess.check_output('ping -c 3 '+sites[args[0]], shell=True))
  except Exception, e:
    print("Error: cannot ping "+sites[args[0]]+"\n"+str(e))
    exit(1)
  if len(args)>1:
    pingtest(args[1:])

def concat3D(list1,list2):
  if len(list1)==len(list2):
    return [ list1[x]+list2[x] for x in xrange(list1)]
  print("Error: cannot add two lists who differ in length")
  exit(1)

def getConfig():
  return getFileContents('config')

def getCreds():
  return getFileContents('credentials')

def getFileContents(type):
  d = dict()
  with open("config/"+type) as f:
    for line in iter(f):
      if len(line)>2:
        d[line.split('=')[0].strip()] = line.split('=')[1].strip()
  return d

#Given the percent of popularity in a supergenre having a subgenre,
#return the frequency of downloading that album as a dict
#in which key=time, val=number from 0-10 of top 10
def downloadFrequency(percent):
  averageDownloads = math.log(10.0*(percent+0.05),1.3)
  if averageDownloads<1:
    averageDownloads=1
  elif averageDownloads>10:
    averageDownloads=10
  #schedule is 24h clock
  return {
    0:math.round(averageDownloads/3.0),
    1:math.round(averageDownloads/3.0),
    2:math.round(averageDownloads/3.0),
    3:math.round(averageDownloads/3.0),
    4:math.round(averageDownloads/3.0),
    5:math.round(1.25*averageDownloads/3.0),#start
    6:math.round(1.875*averageDownloads/3.0),#start
    7:math.round(2.5*averageDownloads),#peak
    8:math.round(1.875*averageDownloads/3.0),#slow
    9:math.round(1.25*averageDownloads/3.0),
    10:math.round(averageDownloads/3.0),
    11:math.round(averageDownloads/3.0),
    12:math.round(averageDownloads/3.0),
    13:math.round(averageDownloads/3.0),
    14:math.round(averageDownloads/3.0),
    15:math.round(averageDownloads/3.0),
    16:math.round(1.5*averageDownloads/3.0),
    17:math.round(2.0*averageDownloads/3.0),#start
    18:math.round(2.5*averageDownloads/3.0),#START
    19:math.round(averageDownloads),#PEAK
    20:math.round(averageDownloads),#PEAK
    21:math.round(2.5*averageDownloads/3.0),#PEAK
    22:math.round(2.0*averageDownloads/3.0),#SLOW
    23:math.round(1.5*averageDownloads/3.0)
  }




#def genre() :
#	now = datetime.datetime.now().time()
	## etc..
