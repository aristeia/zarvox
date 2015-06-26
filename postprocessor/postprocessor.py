import sys, os, subprocess, urllib2, json, Levenshtein, pg
sys.path.append("../packages")
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
	whatcd_seeds=0
	whatcd_snatches=0

	def __init__(self,n,f,g,sp,ll,lp,we,ws):
		name=n
		filepath=f
		genres=g
		spotify_popularity=sp
		lastfm_listeners=ll
		lastfm_playcount=lp
		whatcd_seeds=we
		whatcd_snatches=ws


class Artist:
	name=""
	genres={}
	similar_artists={}
	spotify_popularity=0
	lastfm_listeners=0
	lastfm_playcount=0

	def __init__(self,n,g,sa,sp,ll,lp):
		name=n
		genres=g
		similar_artists=sa
		spotify_popularity=sp
		lastfm_listeners=ll
		lastfm_playcount=lp


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

def levi_misc(x,y, thing):
	return y if Levenshtein.ratio(y,thing)>Levenshtein.ratio(x,thing) else x

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
	with open("../config/config") as f:
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
		print extensions_in_folder
		extension_vals = filter(lambda x: (x[0].lower() in ['mp3','acc','flac','wav','ogg','ac3','alac']),extensions_in_folder)
		print extension_vals
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
		subprocess.call("lame -V"+vbr_format+" "+song_path+" "+('.'.join(song_path.split('.')[0:-1]))+".mp3", shell=True)
	except Exception, e:
		print("Execution failed:\n"+str(e))
		exit(1)

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
	return Song(song.track,path.split('/')[-1],ceil(song.duration/1000.0),explicit,spotify_popularity,lastfm_listeners,lastfm_playcount)

def albumLookup(song,path_to_album):
	#Get genres for album from lastfm, what.cd
	#Get popularities for album from spotify, lastfm, what.cd
	try:
		lastfm = lookup('lastfm','album',{'artist':song.artist, 'album':song.album})['album']
		lastfm_listeners = lastfm['listeners']
		lastfm_playcount = lastfm['playcount']
		lastfm_genres = dict(map(lambda x: (x["name"],x["count"]),lookup('lastfm','albumtags',{'artist':song.artist, 'album':song.album})["toptags"]["tag"]))
		spotify_id = reduce(lambda x,y:levi_misc(x['name'].lower(),y['name'].lower(),song.album.lower()), lookup('spotify','album',{'artist':song.artist,'album':song.album})['albums']['items'])
		spotify_popularity = lookup('spotify','id',{'id':spotify_id, 'type':'albums'})['popularity']
		credentials = {}
		with open("../config/credentials") as f:
			for line in iter(f):
				credentials[line.split('=')[0].strip()] = line.split('=')[1].strip()
		apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'])
		whatcd_artist = apihandle.request("artist", artistname=song.artist)["response"]
		whatcd_album = reduce(lambda x,y: levi_misc(x['groupName'].lower(),y['groupName'].lower(),song.album.lower()),whatcd_artist["torrentgroup"])
		whatcd_genres = whatcd_album["tags"]
		whatcd_snatches = reduce(lambda x,y: {"snatched":(x["snatched"]+y["snatched"])},whatcd_album["torrents"])["snatched"]
		whatcd_seeders = reduce(lambda x,y: {"seeders":(x["seeders"]+y["seeders"])},whatcd_album["torrents"])["seeders"]
		genres = dict([(x,50) for x in whatcd_genres if x not in lastfm_genres]+lastfm_genres.iteritems())
	except Exception, e:
		print("Error: cannot get all album metadata\n"+str(e))
		exit(1)
	return Album(song.album,path_to_album,genres,spotify_popularity,lastfm_listeners,lastfm_playcount,whatcd_seeders,whatcd_snatches)


#Usage (to be ran from anywhere on system): python postprocessor.py album_folder
def main(): 
	db = startup_tests(sys.argv)
	path_to_album = getAlbumPath(sys.argv[1])
	extension = getAudioExtension(path_to_album)
	songs = filter(lambda x: x.split('.')[-1] == extension,os.listdir(path_to_album))
	for song in songs:
		#figure out bitrate
		try:
			bitrate = float(subprocess.check_output("mp3info -r a "+path_to_album+'/'+song, shell=True)) #ceilreduce(lambda x, y: x + y, map(lambda x: ), songs)) / len(songs)
		except Exception, e:
			print("Error: cannot get bitrate properly:\n"+str(e))
			exit(1)
		if extension != 'mp3' or bitrate>275:
			convertSong(path_to_album+'/'+song)
	songs = map(lambda x: path_to_album+'/'+('.'.join(x.split('.')[0:-1]))+".mp3",songs)
	metadata = pimpTunes(songs)
	#generate album, artist, songs objects from pmt
	songs_obj=[]
	for path,song in metadata.iteritems():
		song_obj.append(songLookup(path,song))
	album=albumLookup(song,path_to_album)
	#Check if artist in DB
		#artist=
		#Get genres for artist from lastfm, what.cd
		#Get popularities for artist from spotify, lastfm
		#Get similar artists for artist from last.fm,what.cd

	#Store all in db
	try:
		res = db.query("SELECT * FROM artists WHERE artist = '"+artist.name+"';")
	except Exception, e:
		print("Error: cannot query artist name in db with statement:\nSELECT * FROM artists WHERE artist = '"+artist.name+"'\n"+str(e))
		exit(1)
	if len(res.getresult()) == 0:
		db.query("INSERT INTO artists (FIELDS) VALUES ("+artist.name+","+artist.spotify_popularity+","+artist.lastfm_listeners+","+artist.lastfm_playcount+");")
		db.query("INSERT INTO albums (FIELDS) VALUES ("+album.name+","+album.spotify_popularity+","+album.spotify_popularity+","+album.spotify_popularity+","+album.spotify_popularity+","+album.spotify_popularity+","+album.spotify_popularity+");")
		db.query("INSERT INTO songs (FIELDS) VALUES ("+song.name+","+song.filename+","+song.length+","+song.explicit+","+song.spotify_popularity+","+song.lastfm_listeners+","+song.lastfm_playcount+");")

if  __name__ =='__main__':
	main()

