import sys, os, subprocess, urllib2, json, Levenshtein, pg
sys.path.append("packages")
import whatapi
from libzarv import *
from pimpmytunes import pimpmytunes

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

	def __init__(self,n,f,l,e,sp,ll,lp):
		name=n
		filename=f
		length=l
		explicit=e
		spotify_popularity=sp
		lastfm_listeners=ll
		lastfm_playcount=lp

class Album:
	name=""
	filepath=""
	genres={}
	spotify_popularity=0
	lastfm_listeners=0
	lastfm_playcount=0
	whatcd_seeders=0
	whatcd_snatches=0

	def __init__(self,n,f,g,sp,ll,lp,we,ws):
		name=n
		filepath=f
		genres=g
		spotify_popularity=sp
		lastfm_listeners=ll
		lastfm_playcount=lp
		whatcd_seeders=we
		whatcd_snatches=ws

class Artist:
	name=""
	genres={}
	similar_artists={}
	spotify_popularity=0
	lastfm_listeners=0
	lastfm_playcount=0
	whatcd_seeders=0
	whatcd_snatches=0

	def __init__(self,n,g,sa,sp,ll,lp):
		name=n
		genres=g
		similar_artists=sa
		spotify_popularity=sp
		lastfm_listeners=ll
		lastfm_playcount=lp
		whatcd_snatches=ws
		whatcd_seeders=we

#classvars
credentials
apihandle 
db
db_res = {}


def calc_vbr(br):
	return round(10-10*pow(((br-60.0)/160.0),1.125),3)

#see which one (x,y) is closer in similarity to third arg, weighted towards song name correctness and artist correctness
#does error checking
def levi_spotify_song(x,y, song):
	if not (x['name'] and x['album'] and x['album']['name'] and x['artists'] and x['artists'] != [] and x['artists'][0]['name']):
		return y
	elif not (y['name'] and y['album'] and y['album']['name'] and y['artists'] and y['artists'] != [] and y['artists'][0]['name']):
		return x
	else:
		lx = (Levenshtein.ratio(x['album']['name'].lower(),song.album.lower())+2*Levenshtein.ratio(x['artists'][0]['name'].lower(),song.artist.lower())+4*Levenshtein.ratio(x['name'].lower(),song.track.lower()))
		ly = (Levenshtein.ratio(y['album']['name'].lower(),song.album.lower())+2*Levenshtein.ratio(y['artists'][0]['name'].lower(),song.artist.lower())+4*Levenshtein.ratio(y['name'].lower(),song.track.lower()))
		return y if ly>lx else x

def startup_tests(args):
	#Check sys.argv for path_to_album
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
	return db

def getAlbumPath(path):
	path_to_album = '/'+path.strip('/')
	with open("config/config") as f:
		for line in iter(f):
			if line.split('=')[0].strip() == "albums_folder":
				path_to_album = '/'+line.split('=')[1].strip(' /') + path_to_album
	if not os.path.isdir(path_to_album):
		print("Error: postprocessor received a bad folder path")
		exit(1)
	print("Found folder "+path_to_album)
	return path_to_album

def largestFile(path_to_album):
	return reduce(lambda x,y: (x if os.stat(x).st_size > os.stat(y).st_size else y), [x for x in os.listdir(path_to_album) if os.path.isfile(path_to_album+'/'+x)])

def getAudioExtension(path_to_album):
	#Check if song format other than MP3
	#Get all extensions in the folder, order them by frequency, filter non-music ones,
	# then pick the most frequent remaining one or the most frequent one overall
	# (in the case that it's some obscure format not listed)
	try:
		extensions = [obj.split('.')[-1] for obj in os.listdir(path_to_album) if os.path.isfile(path_to_album+'/'+obj) and '.' in obj]
		extensions_in_folder = []
		map(lambda x: extensions_in_folder.append((x,extensions.count(x))) if (x,extensions.count(x)) not in extensions_in_folder else None , extensions) 
		extensions_in_folder.sort(key=(lambda x:x[1]), reverse=True)
		extension_vals = filter(lambda x: (x[0].lower() in ['mp3','acc','flac','wav','ogg','ac3','alac']),extensions_in_folder)
		extension = extension_vals[0][0] if len(extension_vals) > 0 else largestFile(path_to_album).split('.')[-1] 
	except Exception, e:
		print("Error: cannot get extension of music\n"+str(e))
		exit(1)
	print("The primary extension type in "+path_to_album+" is "+extension)
	return extension

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

def pimpTunes(songs):
	#run pimpmytunes to determine basic metadata
	try:
		pmt = pimpmytunes.PimpMyTunes("0.1.0", path_to_album)
		pmt.setDebug(False)
		pmt.setTerse(False)
		# metadata is a dict with key = songpath, val=metadata obj
		# I modified the source code of pimpmytunes for this functionality
		metadata = pmt.identify(songs, pimpmytunes.PMT_MODE_AUTOMATIC) 
		# metadata objs have following methods: artist,album,track,trackNum,duration, and more
	except Exception, e:
		print("Error: issue with pimpmytunes metadata grabber:\n"+str(e))
		exit(1)
	if len(metadata) == 0:
		print("Error: issue with pimpmytunes returning no songs:\n"+str(e))
		exit(1)
	#TODO
	#If album missing artist or album or song missing song name
		#Query Chromaprint and Acoustid
		#reget metadata

def countToJSON(listOfTags, tagType = 'count'):
	return dict(map(lambda x: (x["name"].lower(),x[tagType]),listOfTags))

def songLookup(path,song):
	#Get explicitness for each song
	try:
		explicit = is_explicit(str(lookup('lyrics','song',{'artist':song.artist, 'song':song.track})['query']['pages']).split('lyrics>')[1])
		#Get song popularity from lastfm and spotify
		lastfm = lookup('lastfm','song',{'artist':song.artist, 'song':song.track})
		lastfm_listeners = lastfm['listeners']
		lastfm_playcount = lastfm['playcount']
		spotify_id = reduce(lambda x,y:levi_spotify_song(x,y,song), lookup('spotify','song',{'artist':song.artist,'album':song.album, 'song':song.track})['tracks']['items'])
		spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'songs'})['popularity']
	except Exception, e:
		print("Error: cannot get all song metadata\n"+str(e))
		exit(1)
	return Song(song.track.lower(),path.split('/')[-1],ceil(song.duration/1000.0),explicit,spotify_popularity,lastfm_listeners,lastfm_playcount)

def albumLookup(song,path_to_album):
	#Get genres for album from lastfm, what.cd
	#Get popularities for album from spotify, lastfm, what.cd
	try:
		lastfm = lookup('lastfm','album',{'artist':song.artist, 'album':song.album})['album']
		lastfm_listeners = lastfm['listeners']
		lastfm_playcount = lastfm['playcount']
		lastfm_genres = countToJSON(map(lambda x: {'name':self.tag.sub('.',x['name']),'count':x['count']},lookup('lastfm','albumtags',{'artist':song.artist, 'album':song.album})["toptags"]["tag"]))
		spotify_id = reduce(lambda x,y:levi_misc(x['name'].lower(),y['name'].lower(),song.album.lower()), lookup('spotify','album',{'artist':song.artist,'album':song.album})['albums']['items'])
		spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'albums'})['popularity']
		whatcd_artist = apihandle.request("artist", artistname=song.artist)["response"]
		whatcd_album = reduce(lambda x,y: levi_misc(x['groupName'].lower(),y['groupName'].lower(),song.album.lower()),whatcd_artist["torrentgroup"])
		whatcd_genres = countToJSON(map(lambda x: {'name': self.tag.sub('.',x['name']),'count':x['count']}, whatcd_album["tags"]))
		whatcd_snatches = reduce(lambda x,y: {"snatched":(x["snatched"]+y["snatched"])},whatcd_album["torrents"])["snatched"]
		whatcd_seeders = reduce(lambda x,y: {"seeders":(x["seeders"]+y["seeders"])},whatcd_album["torrents"])["seeders"]
		genres = dict([(x,50) for x in whatcd_genres if x not in lastfm_genres]+lastfm_genres.iteritems())
	except Exception, e:
		print("Error: cannot get all album metadata\n"+str(e))
		exit(1)
	return Album(song.album.lower(),path_to_album,genres,spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches)

def artistLookup(artist):
	# query whatcd for genres and similar and popularity
	try:
		whatcd_artist = self.apihandle.request("artist", artistname=artist)["response"]
		whatcd_similar = countToJSON(self.apihandle.request("similar_artists", id=whatcd_artist["response"]['id']), 'score')
		whatcd_seeders = whatcd_artist["statistics"]["numSeeders"]
		whatcd_snatches = whatcd_artist["statistics"]["numSnatches"]
		whatcd_genres = countToJSON(map(lambda x: {'name':self.tag.sub('.',x['name']),'count':x['count']}, whatcd_artist["tags"]))
		# query lastfm for popularity and genres and similar
		lastfm = lookup('lastfm','artist',{'artist':artist})['artist']
		lastfm_listeners = lastfm['listeners']
		lastfm_playcount = lastfm['playcount']
		lastfm_genres = countToJSON(map(lambda x: {'name':self.tag.sub('.',x['name']),'count':x['count']},lookup('lastfm','artisttags',{'artist':artist})["toptags"]["tag"]))
		lastfm_similar = countToJSON(lookup('lastfm','artistsimilar',{'artist':artist})["similarartists"]["artist"], "match")
	  # query spotify for popularity
		spotify_id = reduce(lambda x,y:levi_misc(x['name'].lower(),y['name'].lower(),song.artist.lower()), lookup('spotify','artist',{'artist':artist})['artists']['items'])
		spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'artist'})['popularity']
		genres = dict([(x,y) for x,y in whatcd_genres if x not in lastfm_genres]+lastfm_genres.iteritems())
	except Exception, e:
		print("Error: cannot get all artist metadata\n"+str(e))
		exit(1)	
	return Artist(artist.lower(), genres, similar_artists, spotify_popularity,lastfm_listeners,lastfm_playcount, whatcd_snatches, whatcd_seeders)


def getArtistDB( artist, ret=False):
	#artist
	try:
		res = self.db.query("SELECT * FROM artists WHERE artist = $1;", (artist.name)).getresult()
	except Exception, e:
		print("Error: cannot query artist in db\n"+str(e))
		exit(1)
	if len(res) == 0:
		try:
			self.db.query("INSERT INTO artists ( artist, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches) VALUES ($1, $2, $3, $4,$5, $6, $7);", (artist.name,artist.spotify_popularity,artist.lastfm_listeners,artist.lastfm_playcount,artist.whatcd_seeders,artist.whatcd_snatches))
			db_artist = self.db.query("SELECT * FROM artists WHERE artist = $1;", (artist.name)).getresult()[0]
		except Exception, e:
			print("Error: cannot insert artist in db\n"+str(e))
			exit(1)
	elif len(res)>1:
		print("Error: more than two results for artist query")
		exit(1)
	else:
		self.db.query("UPDATE artists SET spotify_popularity = $2, lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6 WHERE artist_id = $1;", (res[0][0],artist.spotify_popularity,artist.lastfm_listeners,artist.lastfm_playcount,artist.whatcd_seeders,artist.whatcd_snatches))
		db_artist = self.db.query("SELECT * FROM artists WHERE artist_id = $1;", (res[0][0])).getresult()[0]
	if ret:
		return [{	'response':res[0] if len(res)>0 else None, 'select':db_artist}]
	self.db_res['artist'] = [{
		'response':res[0] if len(res)>0 else None, 
		'select':db_artist
		}]


def getAlbumDB(album ):
	#album
	db_artistid = self.db_res['artist'][0]['select'][0]
	try:
		res = self.db.query("SELECT * FROM albums WHERE album = $1 AND artist_id = $2;", (album.name, db_artistid)).getresult()
	except Exception, e:
		print("Error: cannot query album in db\n"+str(e))
		exit(1)
	if len(res) == 0:
		try:
			self.db.query("INSERT INTO albums ( album, folder_path, spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches, artist_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8);", (album.name,album.filepath,album.spotify_popularity,album.lastfm_listeners,album.lastfm_playcount,album.whatcd_seeders,album.whatcd_snatches,db_artistid)).getresult()
			db_album = self.db.query("SELECT * FROM albums WHERE album = $1 AND artist_id = $2;", (album.name, db_artistid)).getresult()[0]
		except Exception, e:
			print("Error: cannot insert album in db\n"+str(e))
			exit(1)
	elif len(res)>1:
		print("Error: more than one results for album query")
		exit(1)
	else:
		self.db.query("UPDATE albums SET spotify_popularity = $2,lastfm_listeners = $3,lastfm_playcount = $4,whatcd_seeders = $5,whatcd_snatches = $6, WHERE album_id = $1;", (res[0][0],album.spotify_popularity,album.lastfm_listeners,album.lastfm_playcount,album.whatcd_seeders,album.whatcd_snatches))
		db_album = self.db.query("SELECT * FROM albums WHERE album_id = $1;", (res[0][0])).getresult()[0]
	self.db_res['album'] = [{
		'response':res[0] if len(res)>0 else None, 
		'select':db_album
		}]

def getSongsDB(songs):
	#song
	results = []
	db_albumid = self.db_res['album'][0]['select'][0]
	for song in songs:
		try:
			res = self.db.query("SELECT * FROM songs WHERE song = $1 AND album_id = $2;", (song.name, db_albumid)).getresult()
		except Exception, e:
			print("Error: cannot query song in db\n"+str(e))
			exit(1)
		if len(res)==0:
			try:
				self.db.query("INSERT INTO songs ( song, filename, album_id, length,  explicit, spotify_popularity,lastfm_listeners,lastfm_playcount) VALUES ($1,$2,$3,$4,$5,$6,$7, $8);", (song.name,song.filename,db_albumid, song.length,song.explicit,song.spotify_popularity,song.lastfm_listeners,song.lastfm_playcount)).getresult()
				db_song = self.db.query("SELECT * FROM songs WHERE song = $1 AND album_id = $2;", (song.name, db_albumid)).getresult()[0]
			except Exception, e:
				print("Error: cannot insert song in db\n"+str(e))
				exit(1)
		elif len(res)>1:	
			print("Error: more than one results for song query")
			exit(1)
		else:
			self.db.query("UPDATE songs SET spotify_popularity =$2,lastfm_listeners = $3,lastfm_playcount = $4 WHERE song_id = $1;", (res[0][0],song.spotify_popularity,song.lastfm_listeners,song.lastfm_playcount))
			db_song = self.db.query("SELECT * FROM songs WHERE song_id = $1;", (res[0[0]])).getresult()[0]
		results.append({
		'response':res[0] if len(res)>0 else None, 
		'select':db_song
		})
	self.db_res['song'] = results

def getGenreDB(genres, addOne=False):
	results = []
	for genre in genres:
		try:
			res = self.db.query("SELECT * FROM genres WHERE genre = $1;", (genre)).getresult()
		except Exception, e:
			print("Error: cannot query genre in db\n"+str(e))
			exit(1)
		if len(res)==0:
			whatres = sum(map(lambda x: x['totalSnatched'], self.apihandle.request("browse",searchstr="",taglist=genre)['response']['results']))
			#first check if exists
			if whatres>5000: #Enough to be worth using
				blacklist = map(lambda x: x[1], self.db.query("SELECT * FROM genres_blacklist").getresult())
				if genre not in blacklist or whatres > 12500:
					if genre in blacklist:
						self.db.query("DELETE FROM genres_blacklist WHERE genre = $1;", (genre))
					supergenre = 
					try:
						self.db.query("INSERT INTO genres ( genre, supergenre) VALUES ($1,$2);", (genre,supergenre)).getresult()
					except Exception, e:
						print("Error: cannot insert genre in db\n"+str(e))
						exit(1)

			#if so, get correction
			#otherwise, calculate supergenre, and insert
			db_genre = self.db.query("SELECT * FROM genres WHERE genre = $1;", (genre)).getresult()[0]
		elif len(res)>1:
			print("Error: more than one results for genre query")
			exit(1)
		else:
			db_genre = res[0]
		if addOne:
			try:
				#supergenre_albums = self.db.query("SELECT COUNT(*) FROM albums WHERE album_id IN (SELECT album_genres.album_id FROM albums_genres LEFT OUTER JOIN genres ON (album_genres.genre_id = genres.genre_id) WHERE genres.supergenre = $1); ", (db_genre[2]))
				subgenre_albums = self.db.query("SELECT COUNT(*) FROM albums_genres, genres WHERE album_genres.genre_id = genres.genre_id AND genres.genre = $1;", (genre))
				popularity =(subgenre_albums+1.0) / (1.0+(subgenre_albums/db_genre[3]))
				self.db.query("UPDATE genres SET popularity = $1 WHERE genre_id = $2;", (popularity, db_genre[0]))
				db_genre = self.db.query("SELECT * FROM genres WHERE genre_id = $1;", (db_genre[0])).getresult()[0]
			except Exception, e:
				print("Error: cannot update the popularity of "+genre+" in db\n"+str(e))
				exit(1)
		results.append({
		'response':res[0] if len(res)>0 else None, 
		'select':db_genre
		})
	self.db_res['genres'] = results

def getAlbumGenreDB(vals):
	results = []
	album = self.db_res['album'][0]['select']
	db_genres = map( lambda x: x['select'], self.db_res['album_genre'])
	for db_genre in db_genres:
		try:
			res = self.db.query("SELECT * FROM album_genres  WHERE album_id = $1 AND genre_id = $2;", (album[0],db_genre[0])).getresult()
		except Exception, e:
			print("Error: cannot query association between album "+album[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
			exit(1)
		if len(res)==0:
			try:
				self.db.query("INSERT INTO album_genres (album_id, genre_id, similarity) VALUES ($1,$2,$3);", (album[0],db_genre[0],vals[db_genre[1]]))
			except Exception, e:
				print("Error: cannot associate album "+album[1]+" with genre "+db_genre[1]+" in db\n"+str(e))
				exit(1)
		elif len(res)>1:
			print("Error: more than one results for album_genre association query")
			exit(1)
		else:
			try:
				self.db.query("UPDATE album_genres SET similarity = $3 WHERE album_id = $1 AND genre_id = $2;", (album[0],db_genre[0],vals[db_genre[1]]))
			except Exception, e:
				print("Error: cannot update association between album "+album[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
				exit(1)
		try:
			db_albumgenre = self.self.db.query("SELECT * FROM album_genres  WHERE album_id = $1 AND genre_id = $2;", (album[0],db_genre[0])).getresult()[0]
		except Exception, e:
			print("Error: cannot query association between album "+album[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
			exit(1)
		results.append({
		'response':res[0] if len(res)>0 else None, 
		'select':db_albumgenre
		})
	self.db_res['album_genres'] =  results


def getArtistGenreDB(vals):
	results = []
	artist = self.db_res['artist'][0]['select']
	db_genres = map( lambda x: x['select'], self.db_res['artist_genre'])
	for db_genre in db_genres:
		try:
			res = self.db.query("SELECT * FROM artist_genres  WHERE artist_id = $1 AND genre_id = $2;", (artist[0],db_genre[0])).getresult()
		except Exception, e:
			print("Error: cannot query association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
			exit(1)
		if len(res)==0:
			try:
				self.db.query("INSERT INTO artist_genres (artist_id, genre_id, similarity) VALUES ($1,$2,$3);", (artist[0],db_genre[0],vals[db_genre[1]]))
			except Exception, e:
				print("Error: cannot associate artist "+artist[1]+" with genre "+db_genre[1]+" in db\n"+str(e))
				exit(1)
		elif len(res)>1:
			print("Error: more than one results for artist_genre association query")
			exit(1)
		else:
			try:
				self.db.query("UPDATE artist_genres SET similarity = $3 WHERE artist_id = $1 AND genre_id = $2;", (artist[0],db_genre[0],vals[db_genre[1]]))
			except Exception, e:
				print("Error: cannot update association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
				exit(1)
		try:
			db_artistgenre = self.db.query("SELECT * FROM artist_genres  WHERE artist_id = $1 AND genre_id = $2;", (artist[0],db_genre[0])).getresult()[0]
		except Exception, e:
			print("Error: cannot query association between artist "+artist[1]+" and genre "+db_genre[1]+" in db\n"+str(e))
			exit(1)
		results.append({
		'response':res[0] if len(res)>0 else None, 
		'select':db_artistgenre
		})
	self.db_res['artist_genres'] = results


def getSimilarArtistsDB( similar_artists):
	db_otherartists = []
	results = []
	db_artist = self.db_res['artist'][0]['select']
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
			res = self.db.query("SELECT * FROM similar_artists WHERE artist1_id = $1 and artist2_id = $2",(artist1_id,artist2_id)).getresult()
		except Exception, e:
			print("Error: cannot query association between artist "+artist+" and artist "+db_artist[1]+" in db\n"+str(e))
			exit(1)
		if len(res)==0:
			try:
				self.db.query("INSERT INTO similar_artists (artist1_id, artist2_id, similarity) VALUES ($1,$2,$3);", (artist1_id,artist2_id,val))
			except Exception, e:
				print("Error: cannot associate artist "+artist+" with artist "+db_artist[1]+" in db\n"+str(e))
				exit(1)
		elif len(res)>1:
			print("Error: more than one results for artist_genre association query")
			exit(1)
		else:
			try:
				self.db.query("UPDATE similar_artists SET similarity = $3 WHERE artist1_id = $1 and artist2_id = $2",(artist1_id,artist2_id,val))
			except Exception, e:
				print("Error: cannot update association between artist "+artist+" and artist "+db_artist[1]+" in db\n"+str(e))
				exit(1)
		try:
			db_similarartist = self.db.query("SELECT * FROM similar_artists WHERE artist1_id = $1 and artist2_id = $2",(artist1_id,artist2_id)).getresult()[0]
		except Exception, e:
			print("Error: cannot query association between artist "+artist+" and artist "+db_artist[1]+" in db\n"+str(e))
			exit(1)
		results.append({
		'response':res[0] if len(res)>0 else None, 
		'select':db_similarartist
		})
	self.db_res['similar_artists'] =  results
	self.db_res['other_artists'] = db_otherartists

def getFieldsDB():
	fields = {}
	try:
		fields['artist'] = self.db.query("SELECT * FROM artists LIMIT 1").listfields()
		fields['album'] = self.db.query("SELECT * FROM albums LIMIT 1").listfields()
		fields['song'] = self.db.query("SELECT * FROM songs LIMIT 1").listfields()
		fields['genre'] = self.db.query("SELECT * FROM genres LIMIT 1").listfields()
		fields['album_genre'] = self.db.query("SELECT * FROM album_genres LIMIT 1").listfields()
		fields['artist_genre'] = self.db.query("SELECT * FROM artist_genres LIMIT 1").listfields()
		fields['similar_artist'] = self.db.query("SELECT * FROM similar_artists LIMIT 1").listfields()
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

def printOneRes(name, res, fields):
	prepend=''
	if len(res)>1:
		print(name+":")
		prepend+='\t'
	for x in range(res):
		print(prepend+name+" info for "+res[x]['select'][1])
		for y in range(res[x]):
			print(prepend+"\t"+fields[y]+":"+res[x]['select'][y] +" "+ changes(res[x]['select'][y], res[x]['results'],y ))

def printRes():
	fields = getFieldsDB()
	try:
		printOneRes("Artist",self.db_res['artist'][0]fields['artist'])
		printOneself.db_res("Album",self.db_res['album'],fields['album'])
		printOneself.db_res("Song",self.db_res['songs'],fields['song'])
		printOneself.db_res("Genre",self.db_res['genself.db_res'],fields['genre'])
		printOneself.db_res("Album Genre",self.db_res['album_genself.db_res'],fields['album_genre'])
		printOneself.db_res("Artist Genre",self.db_res['artist_genself.db_res'],fields['artist_genre'])
		printOneself.db_res("Similar Artist",self.db_res['similar_artists'],fields['similar_artist'])
		printOneself.db_res("Other Artist",self.db_res['similar_artists'],fields['artist'])
	except Exception, e:
		print("Error: problem accessing and printing results\n"+str(e))
		exit(1)

#Usage (to be ran from root of zarvox): python postprocessor.py 'album_folder'
def main(): 
	self.db = startup_tests(sys.argv)
	path_to_album = getAlbumPath(sys.argv[1])
	extension = getAudioExtension(path_to_album)
	
	songs = filter(lambda x: x.split('.')[-1] == extension,os.listdir(path_to_album))
	for song in songs:
		#figure out bitrate
		bitrate = getBitrate(path_to_album+'/'+song)
		if extension != 'mp3' or bitrate>275:
			convertSong(path_to_album+'/'+song)
		else:
			print("Bitrate of mp3 "+song+" is good at "+str(bitrate)+"; not converting")
	songs = map(lambda x: path_to_album+'/'+('.'.join(x.split('.')[0:-1]))+".mp3",songs)
	metadata = pimpTunes(songs)

	#generate album, artist, songs objects from pmt
	self.credentials = getCreds()
	self.apihandle = whatapi.WhatAPI(username=self.credentials['username'], password=self.credentials['password'])
	songs_obj=[songLookup(path,song) for path,song in metadata.iteritems() ]
	song = metadata.iteritems()[0]
	album=albumLookup(song,path_to_album)
	artist=artistLookup(song.artist)

	#Store all in db
	#using 3d lists since Ima scrub
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


if  __name__ == '__main__':
	main()

