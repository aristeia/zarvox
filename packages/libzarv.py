import sys,os,re,datetime,subprocess, json, Levenshtein, codecs
from urllib.request import urlopen,Request
from urllib.parse import quote,urlencode
from functools import reduce
import socket
from numpy import float128
from decimal import Decimal

socket.setdefaulttimeout(30)

cocksucker = re.compile('cock.{,12}suck')
number = re.compile('^[0-9]+$')

sites = {
  'whatcd':'www.what.cd',
  'lastfm':'ws.audioscrobbler.com',
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
    'song': "https://api.spotify.com/v1/albums/@albumid/tracks",
    'album': "https://api.spotify.com/v1/artists/@artistid/albums",
    'artist': "https://api.spotify.com/v1/search?q=@artist&limit=5&type=artist",
    'id': "https://api.spotify.com/v1/@type/@id",
    'token':"https://accounts.spotify.com/api/token"
    },
  'lyrics': {
    'song':"http://lyrics.wikia.com/api.php?action=query&prop=revisions&format=json&rvprop=content&titles=@artist:@song"
    }
}

formats = ['MP3','FLAC','AC3','ACC','AAC','DTS']

encoding = ['V0', 'Lossless','24bit Lossless']

def compareTors(x,y):
  def getEncoding(z):
    def calcLosslessness(bitrate):
      return 0.0724867+ float128(Decimal(bitrate-220.0)**Decimal(0.3940886699507389))
    if len(z)>1 and z[0:2] in encoding:
      return encoding.index(z[0:2])
    else:
      if z[0] == 'V':
        return int(z[1])+2
      else:
        if number.match(z):
          if int(z) >= 220:
            return calcLosslessness(float(z))
          else:
            return calc_vbr(int(z))+2
        else:
          return 11
  if formats.index(x['format']) != formats.index(y['format']):
    return x if formats.index(x['format'])<formats.index(y['format']) else y
  ex,ey = getEncoding(x['encoding']), getEncoding(y['encoding'])
  if ex != ey:
    return x if ex<ey else y
  return x if x['seeders']>y['seeders'] else y



def averageResults(l):
  zeros = reduce(lambda x,y:tuple([x[i]+y[i] for i in range(len(x))]),[tuple([0 if y>0 else 1 for y in x]) for x in l])
  vals = reduce(lambda x,y:tuple([x[i]+y[i] for i in range(len(x))]),l)
  return [(float128(vals[x])/(len(l)-zeros[x])) if (len(l)-zeros[x])>0 else 0 for x in range(len(vals))]
    

def countToJSON(listOfTags, tagType = 'count'):
  return dict(map(lambda x: (x["name"],x[tagType]),listOfTags))


def massrep(args,query):
  if len(args)==0:
    return query
  return massrep(args[1:],query.replace('@'+args[0][0],args[0][1]))

def lookup(site, medium, args, data=None,headers=None):
  items = args.items()
  if site == 'lastfm':
    items = [(x,quote(y.replace(' ','+'),'+')) for (x,y) in items]
  elif site=='lyrics':
    items = [(x,quote(y.replace(' ','_'),'_')) for x,y in items]
  else:
    items = [(x,quote(y,'')) for x,y in items]
  query = massrep(items,queries[site][medium])
  if data is not None:
    data = codecs.encode(urlencode(data),'utf-8')
  try:
    if headers:
      with urlopen(Request(query,data,headers)) as response:
        res = response.readall().decode('utf-8')
    else:
      with urlopen(Request(query,data)) as response:
        res = response.readall().decode('utf-8')
  except Exception:
    print("Error: cannot reach site "+site+"\n")
  try:
    return json.loads(res)
  except Exception:
    print("Error: cannot convert response to json\n")
  return {}

def is_safe_harbor():
	return (datetime.datetime.now().time() < time(6) or datetime.datetime.now().time() > time(22))

def is_explicit(text):
  return ('fuck' in text or 'cunt' in text or cocksucker.match(text))

def levi_misc(x,y, thing):
  return y if Levenshtein.ratio(y.lower(),thing.lower())>Levenshtein.ratio(x.lower(),thing.lower()) else x

def calc_vbr(br):
  return round(10-10*pow(((br-60.0)/160.0),1.125),3)

def pingtest(args):
  print("Pinging "+sites[args[0]])
  try:
    print(subprocess.check_output('ping -c 3 '+sites[args[0]], shell=True))
  except Exception:
    print("Error: cannot ping "+sites[args[0]]+"\n")
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

def customIndex(lst,item):
  if item in lst:
    return lst.index(item)
  elif item<min(lst):
    return 0
  else:
    temp = max([x for x in range(len(lst)) if lst[x]<item])
    if temp==(len(lst)-1):
      return len(lst)
    return temp+(float128((item-lst[temp]))/(lst[temp+1]-lst[temp]))

def whatquote(text):
  return (text.replace('+','%2B')
    .replace('&','%26')
    .replace(',','%2C')
    .replace('=','%3D')
    .replace('+','%2B')
    .replace('@','%40')
    #.replace('#','%23')
    #.replace('$','%24')
    #.replace('/','%2F')
    .replace(';','%3B')
    .replace(':','%3A'))
    #.replace(' ','+'))  
  #quote(text,' $\'!')

#def genre() :
#	now = datetime.datetime.now().time()
	## etc..
