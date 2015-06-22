import sys,os,re,datetime,subprocess, json, urllib2


cocksucker = re.compile('cock.{,12}suck')
sites = {
  'what':'www.what.cd',
  'last':'www.last.fm',
  'spotify':'www.spotify.com',
  'lyrics':'lyrics.wikia.com',
  'pandora':'www.pandora.com',
  'music':'www.musicbrainz.com' 
}

queries = {
  'last':{
    'song': 'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key=013cecffb4bcce695153d857e4760a2c&artist=@artist&track=@song&format=json',
    'album': 'http://ws.audioscrobbler.com/2.0/?method=album.getInfo&api_key=013cecffb4bcce695153d857e4760a2c&artist=@artist&album=@album&format=json',
    'albumtags': 'http://ws.audioscrobbler.com/2.0/?method=album.gettoptags&artist=@artist&album=@album&api_key=013cecffb4bcce695153d857e4760a2c&format=json',
    'artist': 'http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&api_key=013cecffb4bcce695153d857e4760a2c&artist=@artist&format=json'
    }
  'spotify':{
    'song': "https://api.spotify.com/v1/search?q=@artist @album @song&type=album&market=US&limit=15",
    'album': "https://api.spotify.com/v1/search?q=@artist @album&type=album&market=US&limit=5",
    'artist': "https://api.spotify.com/v1/search?q=@artist&type=album&market=US&limit=5",
    'id': "https://api.spotify.com/v1/@type/@id?market=ES"
    }
  'lyrics': {
    'song':"http://lyrics.wikia.com/api.php?action=query&prop=revisions&format=json&rvprop=content&titles=@artist:@song"
    }
}

def massrep(args,query):
  if len(args)==0:
    return query
  return massrep(query.replace('@'+args[0][0],args[0][1]))

def lookup(site, type, args):
  query = massrep(args.iteritems(),queries[site][type])
  try:
    res = urllib2.urlopen(query)
  except Exception, e:
    print("Error: cannot reach site "+args['site']+"\n"+str(e))
    exit(1)
  try:
    return json.load(res)
  except Exception, e:
    print("Error: cannot convert to json\n"+str(e))
    exit(1)

def is_safe_harbor() :
	return (datetime.datetime.now().time() < time(6) or datetime.datetime.now().time() > time(22))

def is_explicit(text) :
	if 'fuck' in text or 'cunt' in text or self.cocksucker.match(text):
		return True
	return False

def pingtest(args):
  if len(args)>0:
    print("Pinging "+sites[args[0]])
    try:
      print(subprocess.check_output('ping -c 3 '+sites[args[0]], shell=True))
    except Exception, e:
      print("Error: cannot ping "+sites[args[0]]+"\n"+str(e))
      exit(1)
    pingtest(args[1:])

#def genre() :
#	now = datetime.datetime.now().time()
	## etc..
