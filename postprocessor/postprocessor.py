import sys, os, subprocess, urllib2, json, Levenshtein, pg
sys.path.append("packages")
import whatapi
import cPickle as pickle
from libzarv import *
from pimpmytunes.pimpmytunes.pimpmytunes import PimpMyTunes
from numpy import float128
# All dicts are name:val
# genres would be genre_name:similarity/applicability and so forth
class Song:
	name=""
	filename=""
	length=0
	explicit=False
	spotify_popularity=0
	lastfm_listeners=0
	lastfm_playcount=0

	def __init__(self,n,f='',l=0,e=False,sp=0,ll=0,lp=0):
		name=n
		filename=f
		length=l
		explicit=e
		spotify_popularity=sp
		lastfm_listeners=ll
		lastfm_playcount=lp

	def __str__(self):
		return (self.name+
			":\n\tfilename : "+self.filename+
			"\n\tlength : "+self.length+
			"\n\texplicit : "+self.explicit+
			"\n\tspotify popularity : "+self.spotify_popularity+
			"\n\tlastfm listeners : "+self.lastfm_listeners+
			"\n\tlastfm playcount : "+self.lastfm_playcount)

class Album:
	name=None
	filepath=None
	genres=None
	spotify_popularity=None
	lastfm_listeners=None
	lastfm_playcount=None
	whatcd_seeders=None
	whatcd_snatches=None

	def __init__(self,n,f='',g={},sp=0,ll=0,lp=0,we=0,ws=0):
		name=n
		filepath=f
		genres=g
		spotify_popularity=sp
		lastfm_listeners=ll
		lastfm_playcount=lp
		whatcd_seeders=we
		whatcd_snatches=ws
		
	def __str__(self):
		return (self.name+
			":\n\tfilepath : "+self.filepath+
			"\n\tgenres : "+self.genres+
			"\n\tspotify popularity : "+self.spotify_popularity+
			"\n\tlastfm listeners : "+self.lastfm_listeners+
			"\n\tlastfm playcount : "+self.lastfm_playcount+
			"\n\twhatcd seeders : "+self.whatcd_seeders+
			"\n\twhatcd snatches: "+self.whatcd_snatches)

class Artist:
	name=None
	genres=None
	similar_artists=None
	spotify_popularity=None
	lastfm_listeners=None
	lastfm_playcount=None
	whatcd_seeders=None
	whatcd_snatches=None

	def __init__(self,n,g={},sa={},sp=0,ll=0,lp=0,we=0,ws=0):
		name=n
		genres=g
		similar_artists=sa
		spotify_popularity=sp
		lastfm_listeners=ll
		lastfm_playcount=lp
		whatcd_snatches=ws
		whatcd_seeders=we
		
	def __str__(self):
		return (self.name+
			"\n\tgenres : "+self.genres+
			"\n\tsimilar artists : "+self.similar_artists+
			"\n\tspotify popularity : "+self.spotify_popularity+
			"\n\tlastfm listeners : "+self.lastfm_listeners+
			"\n\tlastfm playcount : "+self.lastfm_playcount+
			"\n\twhatcd seeders : "+self.whatcd_seeders+
			"\n\twhatcd snatches: "+self.whatcd_snatches)

#classvars
credentials = None
apihandle = None
db = None
db_res = None
conf = None
metadata = None


def calc_vbr(br):
	return round(10-10*pow(((br-60.0)/160.0),1.125),3)

#see which one (x,y) is closer in similarity to third arg, weighted towards song name correctness and artist correctness
#does error checking
def levi_spotify_song(x,y, song):
	global metadata
	if not (x['name'] and x['album'] and x['album']['name'] and x['artists'] and x['artists'] != [] and x['artists'][0]['name']):
		return y
	elif not (y['name'] and y['album'] and y['album']['name'] and y['artists'] and y['artists'] != [] and y['artists'][0]['name']):
		return x
	else:
		lx = (Levenshtein.ratio(x['album']['name'].lower(),metadata['album'].lower())+2*Levenshtein.ratio(x['artists'][0]['name'].lower(),metadata['artist'].lower())+4*Levenshtein.ratio(x['name'].lower(),song))
		ly = (Levenshtein.ratio(y['album']['name'].lower(),metadata['album'].lower())+2*Levenshtein.ratio(y['artists'][0]['name'].lower(),metadata['artist'].lower())+4*Levenshtein.ratio(y['name'].lower(),song))
		return y if ly>lx else x

def levi_song(x,y,song):
  #Data that will be available to us about the files:
  #name, size,duration[, encoding]
  #Song:
  #name, duration[, encoding]
  #Weights:
  # 40,60
  try:
  	l1x = float128(Levenshtein.ratio(x['name'],song['name']))*0.4
  	l1y = float128(Levenshtein.ratio(y['name'],song['name']))*0.4
  except Exception, e:
  	print("Error: cannot get levi ratio between songname and filenames\n"+str(e))
  	exit(1)
  try:
  	l2x = ((song['duration']-abs(numpy.float128(song['duration'])-x['duration']))/song['duration'])*0.6
  	l2y = ((song['duration']-abs(numpy.float128(song['duration'])-x['duration']))/song['duration'])*0.6
  except Exception, e:
  	print("Error: cannot get levi ratio between songduration and fileduration\n"+str(e))
  	exit(1)
  return x if (l1x+l2x)>(l1y+l2y) else y


def startup_tests(args):
	#Check sys.argv for path_to_album
	global db
	if len(args) != 2:
		print("Error: postprocessor received wrong number of args")
		exit(1)
	try:
		db = pg.connect('zarvox', user='kups', passwd='fuck passwords')
	except Exception, e:
		print("Error: cannot connect to database\n"+str(e))
		exit(1)
	print("Zarvox database are online")
	try:
		pingtest(['whatcd','lastfm','spotify','lyrics','music'])
	except Exception, e:
		print(e)
		exit(1)
	print("Pingtest complete; sites are online")

def getAlbumPath(arg):
	global conf
	temp = '/'+conf["albums_folder"].strip(' /') + '/'+arg.strip('/')
	if not os.path.isdir(metadata["path_to_album"]):
		print("Error: postprocessor received a bad folder path")
		exit(1)
	print("Found folder "+temp)
	return temp

# def largestFile():
# 	global metadata
# 	try:
# 		return reduce(lambda x,y: (x if os.stat(x).st_size > os.stat(y).st_size else y), [x for x in os.listdir(metadata["path_to_album"]) if os.path.isfile(metadata["path_to_album"]+'/'+x)])
# 	except Exception,e:
# 		print("Error: cannot check the greatest file size"+str(e))
# 		exit(1)

# def getAudioExtension(path_to_album):
# 	#Check if song format other than MP3
# 	#Get all extensions in the folder, order them by frequency, filter non-music ones,
# 	# then pick the most frequent remaining one or the most frequent one overall
# 	# (in the case that it's some obscure format not listed)
# 	try:
# 		extensions = [obj.split('.')[-1] for obj in os.listdir(path_to_album) if os.path.isfile(path_to_album+'/'+obj) and '.' in obj]
# 		extensions_in_folder = []
# 		map(lambda x: extensions_in_folder.append((x,extensions.count(x))) if (x,extensions.count(x)) not in extensions_in_folder else None , extensions) 
# 		extensions_in_folder.sort(key=(lambda x:x[1]), reverse=True)
# 		extension_vals = filter(lambda x: (x[0].lower() in ['mp3','acc','flac','wav','ogg','ac3','alac']),extensions_in_folder)
# 		extension = extension_vals[0][0] if len(extension_vals) > 0 else largestFile(path_to_album).split('.')[-1] 
# 	except Exception, e:
# 		print("Error: cannot get extension of music\n"+str(e))
# 		exit(1)
# 	print("The primary extension type in "+path_to_album+" is "+extension)
# 	return extension

def convertSong(song_path):
	#Dequeue album from rtorrent 
	#Use proper MP3 VBR format for space efficiency + quality maximization
	if bitrate>220:
		vbr_format = 0.0
	elif bitrate<60:
		print("Error: bitrate too low at "+bitrate)
		exit(1)
	else:
		vbr_format=calc_vbr(bitrate)
	#convert files to mp3 with lame
	try:
		subprocess.call("lame -V"+vbr_format+" '"+song_path+"'' '"+('.'.join(song_path.split('.')[0:-1]))+".mp3'", shell=True)
	except Exception, e:
		print("Execution failed:\n"+str(e))
		exit(1)

def getBitrate(path_to_song):
	try:
		bitrate = float(subprocess.check_output("exiftool -AudioBitrate '"+path_to_song+"'", shell=True).split()[-2]) 
	except Exception, e:
		print("Error: cannot get bitrate properly:\n"+str(e))
		print("Will try converting anyway")
		bitrate = 276 # max bitrate +1
	return bitrate

def getDuration(path_to_song):
	try:
		durations = subprocess.check_output("exiftool -Duration '"+path_to_song+"'", shell=True).split()[-2].split(':')
		duration = reduce(lambda 	x,y:x+y,[int(durations[x])*math.pow(60,2-x) for x in xrange(len(durations))]) 
	except Exception, e:
		print("Error: cannot get duration properly:\n"+str(e))
		exit(1)
	return duration

def getData(path):
	try:
		with open(path+"/.metadata.json") as f:
	    data = json.loads(f.read())
	except Exception, e:
		print("Error: cannot read album metadata"+str(e))
		exit(1)
	return data

def getDataVals(data):
	return tuple([val for key,val in data.iteritems()])

def associateSongToFile( songInfo,fileInfo):
  assoc = {}
	for f in fileInfo:
		f['duration'] = getDuration(path_to_album+'/'+f['name'])
	for song in songInfo:
		sfile = reduce(lambda x,y: levi_song(x,y,song) ,fileInfo)
		song['size'] = sfile['size']
		assoc[sfile.name] = song
		fileInfo.remove(sfile)
	return assoc

# def pimpTunes(songs):
# 	#run pimpmytunes to determine basic metadata
# 	try:
# 		pmt = PimpMyTunes("0.1.0", path_to_album)
# 		pmt.setDebug(False)
# 		pmt.setTerse(False)
# 		# metadata is a dict with key = songpath, val=metadata obj
# 		# I modified the source code of pimpmytunes for this functionality
# 		metadata = pmt.identify(songs, pimpmytunes.PMT_MODE_AUTOMATIC) 
# 		# metadata objs have following methods: artist,album,track,trackNum,duration, and more
# 	except Exception, e:
# 		print("Error: issue with pimpmytunes metadata grabber:\n"+str(e))
# 		exit(1)
# 	if len(metadata) == 0:
# 		print("Error: issue with pimpmytunes returning no songs:\n"+str(e))
# 		exit(1)
# 	return metadata
# 	#TODO
# 	#If album missing artist or album or song missing song name
# 		#Query Chromaprint and Acoustid
# 		#reget metadata

def countToJSON(listOfTags, tagType = 'count'):
	return dict(map(lambda x: (x["name"].lower(),x[tagType]),listOfTags))

def songLookup(song):
	#Get explicitness for each song
	global metadata
	try:
		explicit = is_explicit(str(lookup('lyrics','song',{'artist':metadata['artist'], 'song':song.name})['query']['pages']).split('lyrics>')[1])
		#Get song popularity from lastfm and spotify
		lastfm = lookup('lastfm','song',{'artist':metadata['artist'], 'song':song.name})
		lastfm_listeners = lastfm['listeners']
		lastfm_playcount = lastfm['playcount']
		spotify_id = reduce(lambda x,y:levi_spotify_song(x.lower(),y.lower(),song.name.lower()), lookup('spotify','song',{'artist':metadata['artist'],'album':metadata['album'], 'song':song.name})['tracks']['items'])
		spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'songs'})['popularity']
	except Exception, e:
		print("Error: cannot get all song metadata\n"+str(e))
		exit(1)
	return Song(song.name,song.path,ceil,song.duration,explicit,spotify_popularity,lastfm_listeners,lastfm_playcount)

def albumLookup():
	#Get genres for album from lastfm, what.cd
	#Get popularities for album from spotify, lastfm, what.cd
	global metadata, apihandle
	try:
		lastfm = lookup('lastfm','album',{'artist':metadata['artist'], 'album':metadata['album']})['album']
		lastfm_listeners = lastfm['listeners']
		lastfm_playcount = lastfm['playcount']
		lastfm_genres = countToJSON(map(lambda x: {'name':self.tag.sub('.',x['name']),'count':x['count']},lookup('lastfm','albumtags',{'artist':metadata['artist'], 'album':metadata['album']})["toptags"]["tag"]))
		spotify_id = reduce(lambda x,y:levi_misc(x['name'].lower(),y['name'].lower(),song.album.lower()), lookup('spotify','album',{'artist':metadata['artist'],'album':metadata['album']})['albums']['items'])
		spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'albums'})['popularity']
		whatcd_artist = apihandle.request("artist", artistname=metadata['artist'])["response"]
		whatcd_album = reduce(lambda x,y: levi_misc(x['groupName'].lower(),y['groupName'].lower(),metadata['album'].lower()),whatcd_artist["torrentgroup"])
		whatcd_genres = countToJSON(map(lambda x: {'name': self.tag.sub('.',x['name']),'count':x['count']}, whatcd_album["tags"]))
		whatcd_snatches = reduce(lambda x,y: {"snatched":(x["snatched"]+y["snatched"])},whatcd_album["torrents"])["snatched"]
		whatcd_seeders = reduce(lambda x,y: {"seeders":(x["seeders"]+y["seeders"])},whatcd_album["torrents"])["seeders"]
		genres = dict([(x,50) for x in whatcd_genres if x not in lastfm_genres]+lastfm_genres.items())
	except Exception, e:
		print("Error: cannot get all album metadata\n"+str(e))
		exit(1)
	return Album(metadata['album'].lower(),metadata['path'],genres,spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches)

def artistLookup():
	# query whatcd for genres and similar and popularity
	global metadata,apihandle
	try:
		whatcd_artist = apihandle.request("artist", artistname=metadata['artist'])["response"]
		whatcd_similar = countToJSON(apihandle.request("similar_artists", id=whatcd_artist["response"]['id']), 'score')
		whatcd_seeders = whatcd_artist["statistics"]["numSeeders"]
		whatcd_snatches = whatcd_artist["statistics"]["numSnatches"]
		whatcd_genres = countToJSON(map(lambda x: {'name':self.tag.sub('.',x['name']),'count':x['count']}, whatcd_artist["tags"]))
		# query lastfm for popularity and genres and similar
		lastfm = lookup('lastfm','artist',{'artist':metadata['artist']})['artist']
		lastfm_listeners = lastfm['listeners']
		lastfm_playcount = lastfm['playcount']
		lastfm_genres = countToJSON(map(lambda x: {'name':self.tag.sub('.',x['name']),'count':x['count']},lookup('lastfm','artisttags',{'artist':metadata['artist']})["toptags"]["tag"]))
		lastfm_similar = countToJSON(lookup('lastfm','artistsimilar',{'artist':metadata['artist']})["similarartists"]["artist"], "match")
	  # query spotify for popularity
		spotify_id = reduce(lambda x,y:levi_misc(x['name'].lower(),y['name'].lower(),metadata['artist'].lower()), lookup('spotify','artist',{'artist':metadata['artist']})['artists']['items'])
		spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'artist'})['popularity']
		genres = dict([(x,y) for x,y in whatcd_genres if x not in lastfm_genres]+lastfm_genres.items())
	except Exception, e:
		print("Error: cannot get all artist metadata\n"+str(e))
		exit(1)	
	return Artist(metadata['artist'], genres, similar_artists, spotify_popularity,lastfm_listeners,lastfm_playcount, whatcd_snatches, whatcd_seeders)


def getArtistDB( artist, ret=False):
	global db,metadata,db_res
	try:
		res = db.query("SELECT * FROM artists WHERE artist = $1;", (artist.name)).getresult()
	except Exception, e:
		print("Error: cannot query artist in db\n"+str(e))
		exit(1)
	if len(res) == 0:
		try:
			db.query("INSERT INTO artists ( artist, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches) VALUES ($1, $2, $3, $4,$5, $6, $7);", (artist.name,artist.spotify_popularity,artist.lastfm_listeners,artist.lastfm_playcount,artist.whatcd_seeders,artist.whatcd_snatches))
			db_artist = db.query("SELECT * FROM artists WHERE artist = $1;", (artist.name)).getresult()[0]
		except Exception, e:
			print("Error: cannot insert artist in db\n"+str(e))
			exit(1)
	elif len(res)>1:
		print("Error: more than two results for artist query")
		exit(1)
	else:
		db.query("UPDATE artists SET spotify_popularity = $2, lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6 WHERE artist_id = $1;", (res[0][0],artist.spotify_popularity,artist.lastfm_listeners,artist.lastfm_playcount,artist.whatcd_seeders,artist.whatcd_snatches))
		db_artist = db.query("SELECT * FROM artists WHERE artist_id = $1;", (res[0][0])).getresult()[0]
	if ret:
		return [{	'response':res[0] if len(res)>0 else None, 'select':db_artist}]
	db_res['artist'] = [{
		'response':res[0] if len(res)>0 else None, 
		'select':db_artist
		}]


def getAlbumDB(album ):
	global db,metadata,db_res
	db_artistid = db_res['artist'][0]['select'][0]
	try:
		res = db.query("SELECT * FROM albums WHERE album = $1 AND artist_id = $2;", (album.name, db_artistid)).getresult()
	except Exception, e:
		print("Error: cannot query album in db\n"+str(e))
		exit(1)
	if len(res) == 0:
		try:
			db.query("INSERT INTO albums ( album, folder_path, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches, artist_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8);", (album.name,album.filepath,album.spotify_popularity,album.lastfm_listeners,album.lastfm_playcount,album.whatcd_seeders,album.whatcd_snatches,db_artistid)).getresult()
			db_album = db.query("SELECT * FROM albums WHERE album = $1 AND artist_id = $2;", (album.name, db_artistid)).getresult()[0]
		except Exception, e:
			print("Error: cannot insert album in db\n"+str(e))
			exit(1)
	elif len(res)>1:
		print("Error: more than one results for album query")
		exit(1)
	else:
		db.query("UPDATE albums SET spotify_popularity = $2,lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6, WHERE album_id = $1;", (res[0][0],album.spotify_popularity,album.lastfm_listeners,album.lastfm_playcount,album.whatcd_seeders,album.whatcd_snatches))
		db_album = db.query("SELECT * FROM albums WHERE album_id = $1;", (res[0][0])).getresult()[0]
	db_res['album'] = [{
		'response':res[0] if len(res)>0 else None, 
		'select':db_album
		}]

def getSongsDB(songs):
	global db,metadata,db_res
	results = []
	db_albumid = db_res['album'][0]['select'][0]
	for song in songs:
		try:
			res = db.query("SELECT * FROM songs WHERE song = $1 AND album_id = $2;", (song.name,metadata['album'])).getresult()
		except Exception, e:
			print("Error: cannot query song in db\n"+str(e))
			exit(1)
		if len(res)==0:
			try:
				db.query("INSERT INTO songs ( song, filename, album_id, length,  explicit, spotify_popularity,lastfm_listeners,lastfm_playcount) VALUES ($1,$2,$3,$4,$5,$6,$7, $8);", (song.name,song.filename,db_albumid, song.length,song.explicit,song.spotify_popularity,song.lastfm_listeners,song.lastfm_playcount)).getresult()
				db_song = db.query("SELECT * FROM songs WHERE song = $1 AND album_id = $2;", (song.name, db_albumid)).getresult()[0]
			except Exception, e:
				print("Error: cannot insert song in db\n"+str(e))
				exit(1)
		elif len(res)>1:	
			print("Error: more than one results for song query")
			exit(1)
		else:
			db.query("UPDATE songs SET spotify_popularity =$2,lastfm_listeners = $3,lastfm_playcount = $4 WHERE song_id = $1;", (res[0][0],song.spotify_popularity,song.lastfm_listeners,song.lastfm_playcount))
			db_song = db.query("SELECT * FROM songs WHERE song_id = $1;", (res[0[0]])).getresult()[0]
		results.append({
		'response':res[0] if len(res)>0 else None, 
		'select':db_song
		})
	db_res['song'] = results

def getGenreDB(genres, addOne=False):
	global apihandle,db, metadata,db_res
	results = []
	for genre in genres:
		db_genre = None
		try:
			res = db.query("SELECT * FROM genres WHERE genre = $1;", (genre)).getresult()
		except Exception, e:
			print("Error: cannot query genre in db\n"+str(e))
			exit(1)
		if len(res)==0:
			whatres = apihandle.request("browse",searchstr="",taglist=genre)['response']['results']
			snatched = sum(map(lambda x: x['totalSnatched'], whatres))
			#first check if exists
			if snatched>5000: #Enough to be worth using
				blacklist_query = db.query("SELECT * FROM genres_blacklist WHERE genre=$1;", (genre)).getresult()
				blacklist = blacklist_query[0] if len(blacklist_query)>0 else []
				if genre not in blacklist or (snatched > 12500 and len(blacklist)>2 and not blacklist[2]):
					try:
						if genre in blacklist:
							db.query("DELETE FROM genres_blacklist WHERE genre_id = $1;", (blacklist[0]))
						percentile = (lambda x:
							float(sum([1 for y in whatres if any([z in y['tags'] for z in x])] ))/float(len(whatres)))
						supergenre = reduce( lambda x1,x2,y1,y2: ((x1,x2) if x2>y2 else (y1,y2)), {
							'rock': percentile(['rock','metal','classic.rock','hard.rock','punk.rock','blues.rock','progressive.rock','black.metal','death.metal','hardcore.punk','hardcore','grunge','pop.rock']),
							'hip.hop': percentile(['rap','hip.hop','rhythm.and.blues','trip.hop','trap.rap','southern.rap','gangsta','gangsta.rap']),
							'electronic':percentile(['electronic','dub','ambient','dubstep','house','breaks','downtempo','techno','glitch','idm','edm','dance','electro','trance','midtempo','beats','grime']),
							'alternative':percentile(['alternative','indie','indie.rock','punk','emo','singer.songwriter','folk','dream.pop','shoegaze','synth.pop','post.punk','chillwave','kpop','jpop','ska','folk.rock','reggae','new.wave','ethereal','instrumental','surf.rock']),
							'specialty':percentile(['experimental','funk','blues','world.music','soul','psychedelic','art.rock','country','classical','baroque','minimalism','minimal','score','disco','avant.garde','math.rock','afrobeat','post.rock','noise','drone','jazz','dark.cabaret','neofolk','krautrock','improvisation','space.rock','free.jazz'])
						}.iteritems())[0]
						db.query("INSERT INTO genres ( genre, supergenre) VALUES ($1,$2);", (genre,supergenre))
						db_genre = db.query("SELECT * FROM genres WHERE genre = $1;", (genre)).getresult()[0]
					except Exception, e:
						print("Error: cannot insert genre "+genre+ " into db\n"+str(e))
						exit(1)
			else: #check if misspelling 
				other_genres = filter(lambda x: Levenshtein.ratio(x[0],genre)>0.875,db.query("SELECT genre FROM genres;").getresult())
				if len(other_genres)>0: #mispelling
					genre = reduce(lambda x,y: levi_misc(x,y,genre),other_genres)
					db_genre = db.query("SELECT * FROM genres WHERE genre = $1;", (genre)).getresult()[0]
				else: #add to blacklist
					db.query("INSERT INTO genres_blacklist (genre,permanent) VALUES ($1);", (genre,False))
		elif len(res)>1:
			print("Error: more than one results for genre query")
			exit(1)
		else:
			db_genre = res[0]
		if db_genre:
			if addOne:
				try:
					#supergenre_albums = db.query("SELECT COUNT(*) FROM albums WHERE album_id IN (SELECT album_genres.album_id FROM albums_genres LEFT OUTER JOIN genres ON (album_genres.genre_id = genres.genre_id) WHERE genres.supergenre = $1); ", (db_genre[2]))
					subgenre_albums = db.query("SELECT COUNT(*) FROM albums_genres, genres WHERE album_genres.genre_id = genres.genre_id AND genres.genre = $1;", (genre))
					popularity =(subgenre_albums+1.0) / (1.0+(subgenre_albums/db_genre[3]))
					db.query("UPDATE genres SET popularity = $1 WHERE genre_id = $2;", (popularity, db_genre[0]))
					db_genre = db.query("SELECT * FROM genres WHERE genre_id = $1;", (db_genre[0])).getresult()[0]
				except Exception, e:
					print("Error: cannot update the popularity of "+genre+" in db\n"+str(e))
					exit(1)
			results.append({
			'response':res[0] if len(res)>0 else None, 
			'select':db_genre
			})
	db_res['genres'] = results

def getAlbumGenreDB(vals):
	global db,metadata,db_res
	results = []
	album = db_res['album'][0]['select']
	db_genres = map( lambda x: x['select'], db_res['album_genre'])
	for db_genre in db_genres:
		try:
			res = db.query("SELECT * FROM album_genres  WHERE album_id = $1 AND genre_id = $2;", (album[0],db_genre[0])).getresult()
		except Exception, e:
			print("Error: cannot query association between album "+album[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
			exit(1)
		if len(res)==0:
			try:
				db.query("INSERT INTO album_genres (album_id, genre_id, similarity) VALUES ($1,$2,$3);", (album[0],db_genre[0],vals[db_genre[1]]))
			except Exception, e:
				print("Error: cannot associate album "+album[1]+" with genre "+db_genre[1]+" in db\n"+str(e))
				exit(1)
		elif len(res)>1:
			print("Error: more than one results for album_genre association query")
			exit(1)
		else:
			try:
				db.query("UPDATE album_genres SET similarity = $3 WHERE album_id = $1 AND genre_id = $2;", (album[0],db_genre[0],vals[db_genre[1]]))
			except Exception, e:
				print("Error: cannot update association between album "+album[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
				exit(1)
		try:
			db_albumgenre = self.db.query("SELECT * FROM album_genres  WHERE album_id = $1 AND genre_id = $2;", (album[0],db_genre[0])).getresult()[0]
		except Exception, e:
			print("Error: cannot query association between album "+album[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
			exit(1)
		results.append({
		'response':res[0] if len(res)>0 else None, 
		'select':db_albumgenre
		})
	db_res['album_genres'] =  results


def getArtistGenreDB(vals):
	global db,metadata,db_res
	results = []
	artist = db_res['artist'][0]['select']
	db_genres = map( lambda x: x['select'], db_res['artist_genre'])
	for db_genre in db_genres:
		try:
			res = db.query("SELECT * FROM artist_genres  WHERE artist_id = $1 AND genre_id = $2;", (artist[0],db_genre[0])).getresult()
		except Exception, e:
			print("Error: cannot query association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
			exit(1)
		if len(res)==0:
			try:
				db.query("INSERT INTO artist_genres (artist_id, genre_id, similarity) VALUES ($1,$2,$3);", (artist[0],db_genre[0],vals[db_genre[1]]))
			except Exception, e:
				print("Error: cannot associate artist "+artist[1]+" with genre "+db_genre[1]+" in db\n"+str(e))
				exit(1)
		elif len(res)>1:
			print("Error: more than one results for artist_genre association query")
			exit(1)
		else:
			try:
				db.query("UPDATE artist_genres SET similarity = $3 WHERE artist_id = $1 AND genre_id = $2;", (artist[0],db_genre[0],vals[db_genre[1]]))
			except Exception, e:
				print("Error: cannot update association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
				exit(1)
		try:
			db_artistgenre = db.query("SELECT * FROM artist_genres  WHERE artist_id = $1 AND genre_id = $2;", (artist[0],db_genre[0])).getresult()[0]
		except Exception, e:
			print("Error: cannot query association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
			exit(1)
		results.append({
		'response':res[0] if len(res)>0 else None, 
		'select':db_artistgenre
		})
	db_res['artist_genres'] = results


def getSimilarArtistsDB( similar_artists):
	global db,metadata,db_res
	db_otherartists = []
	results = []
	db_artist = db_res['artist'][0]['select']
	for artist,val in similar_artists:
		db_otherartists.append(getArtistDB(db, artistLookup(artist), ret=True)[0])
		db_other = db_otherartists[-1]['select']
		if db_other[0]>db_artist[0]:
			artist1_id = db_other[0]
			artist2_id = db_artist[0]
		else:
			artist1_id = db_artist[0]
			artist2_id = db_other[0]
		try:
			res = db.query("SELECT * FROM similar_artists WHERE artist1_id = $1 and artist2_id = $2",(artist1_id,artist2_id)).getresult()
		except Exception, e:
			print("Error: cannot query association between artist "+artist+" and artist "+db_artist[1]+" in db\n"+str(e))
			exit(1)
		if len(res)==0:
			try:
				db.query("INSERT INTO similar_artists (artist1_id, artist2_id, similarity) VALUES ($1,$2,$3);", (artist1_id,artist2_id,val))
			except Exception, e:
				print("Error: cannot associate artist "+artist+" with artist "+db_artist[1]+" in db\n"+str(e))
				exit(1)
		elif len(res)>1:
			print("Error: more than one results for artist_genre association query")
			exit(1)
		else:
			try:
				db.query("UPDATE similar_artists SET similarity = $3 WHERE artist1_id = $1 and artist2_id = $2",(artist1_id,artist2_id,val))
			except Exception, e:
				print("Error: cannot update association between artist "+artist+" and artist "+db_artist[1]+" in db\n"+str(e))
				exit(1)
		try:
			db_similarartist = db.query("SELECT * FROM similar_artists WHERE artist1_id = $1 and artist2_id = $2",(artist1_id,artist2_id)).getresult()[0]
		except Exception, e:
			print("Error: cannot query association between artist "+artist+" and artist "+db_artist[1]+" in db\n"+str(e))
			exit(1)
		results.append({
		'response':res[0] if len(res)>0 else None, 
		'select':db_similarartist
		})
	db_res['similar_artists'] =  results
	db_res['other_artists'] = db_otherartists

def getFieldsDB():
	global db
	fields = {}
	try:
		fields['artist'] = db.query("SELECT * FROM artists LIMIT 1").listfields()
		fields['album'] = db.query("SELECT * FROM albums LIMIT 1").listfields()
		fields['song'] = db.query("SELECT * FROM songs LIMIT 1").listfields()
		fields['genre'] = db.query("SELECT * FROM genres LIMIT 1").listfields()
		fields['album_genre'] = db.query("SELECT * FROM album_genres LIMIT 1").listfields()
		fields['artist_genre'] = db.query("SELECT * FROM artist_genres LIMIT 1").listfields()
		fields['similar_artist'] = db.query("SELECT * FROM similar_artists LIMIT 1").listfields()
	except Exception, e:
		print("Error: cannot check fields in db\n"+str(e))
		exit(1)
	return fields

def changes(new, orignial, index):
	if orignial is None:
		return "(inserted)"
	elif len(original)>index and original[index] == new:
		return "(no changes)"
	return "(updated from "+original[index]+")"

def printRes():
	def printOneRes(name, res, fields):
		prepend=''
		if len(res)>1:
			print(name+":")
			prepend+='\t'
		for x in xrange(len(res)):
			print(prepend+name+" info for "+res[x]['select'][1])
			for y in xrange (len(res[x])):
				print(prepend+"\t"+fields[y]+":"+res[x]['select'][y] +" "+ changes(res[x]['select'][y], res[x]['results'],y ))
	fields = getFieldsDB()
	try:
		printOneRes("Artist",db_res['artist'][0],fields['artist'])
		printOneRes("Album",db_res['album'],fields['album'])
		printOneRes("Song",db_res['songs'],fields['song'])
		printOneRes("Genre",db_res['gendb_res'],fields['genre'])
		printOneRes("Album Genre",db_res['album_gendb_res'],fields['album_genre'])
		printOneRes("Artist Genre",db_res['artist_gendb_res'],fields['artist_genre'])
		printOneRes("Similar Artist",db_res['similar_artists'],fields['similar_artist'])
		printOneRes("Other Artist",db_res['similar_artists'],fields['artist'])
	except Exception, e:
		print("Error: problem accessing and printing results\n"+str(e))
		exit(1)

#Usage (to be ran from root of zarvox): python postprocessor.py 'album_folder'
def main(): 
	global db,credentials,db_res,conf,metadata,apihandle
	startup_tests(sys.argv)
	conf = getConfig()
	credentials = getCreds()
	db_res = {}
	cookies = pickle.load(open('config/.cookies.dat', 'rb'))
	apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
	metadata, songInfo,fileInfo = getDataVals(getData(getAlbumPath(sys.argv[1])))
	dataInfo = associateSongToFile( songInfo,fileInfo)
	metadata['songs'] = dataInfo
	#extension = getAudioExtension(path_to_album)
	
	for song,songInfo in metadata['songs']:
		#figure out bitrate
		bitrate = getBitrate(path_to_album+'/'+song)
		if metadata['format'] != 'mp3' or bitrate>287.5:
			convertSong(path_to_album+'/'+song)
		else:
			print("Bitrate of mp3 "+song+" is good at "+str(bitrate)+"; not converting")
	songs = filter(lambda x: x.split('.')[-1].lower() == 'mp3',os.listdir(path_to_album))

	#generate album, artist, songs objects from pmt
	credentials = getCreds()
	songs_obj=[songLookup(path,song) for path,song in metadata.iteritems() ]
	album=albumLookup(song,path_to_album)
	artist=artistLookup(song.artist)
	print "Artist obj:\n"+artist,'\n\nAlbum obj:\n',album,"\nSong objs:\n"
	for song in song_obj:
		print song
	#Store all in db
	getArtistDB( artist)
	getAlbumDB( album)
	getSongsDB( song_obj)

	#store genres
	getGenreDB( map( lambda x,y: x,album.genres.iteritems()), addOne = True)
	getGenreDB( map( lambda x,y: x,artist.genres.iteritems()))
	#attach them to album & artist all by ids
	getAlbumGenreDB( album.genres)
	getArtistGenreDB( artist.genres)
	#store similar artist
	getSimilarArtistsDB( artist.similar_artists)

	print("Done working with database")
	print("The following values exist:")
	printRes()
	pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))

if  __name__ == '__main__':
	main()