import sys, os, subprocess, urllib2, json, Levenshtein
sys.path.append("packages")
import whatapi
import cPickle as pickle
from libzarv import *
from libzarvclasses import *
from lookup import *
from database import *
#from pimpmytunes.pimpmytunes.pimpmytunes import PimpMyTunes
from numpy import float128

#classvars
credentials = None
conf = None


def calc_vbr(br):
	return round(10-10*pow(((br-60.0)/160.0),1.125),3)

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
  
  def levi_song(x,y,song):
	  #Data that will be available to us about the files:
	  #name, size,duration[, encoding]
	  #Song:
	  #name, duration[, encoding]
	  #Weights:
	  # 40,60
	  try:
	  	l1x = float128(Levenshtein.ratio(x['name'],song['filename']))*0.4
	  	l1y = float128(Levenshtein.ratio(y['name'],song['filename']))*0.4
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



  assoc = {}
	for f in fileInfo:
		f['duration'] = getDuration(path_to_album+'/'+f['name'])
	for song in songInfo:
		sfile = reduce(lambda x,y: levi_song(x,y,song) ,fileInfo)
		song['size'] = sfile['size']
		song.pop('filename')
		assoc[sfile.name] = song
		fileInfo.remove(sfile)
	return assoc



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
	metadata['songs'] = associateSongToFile( songInfo,fileInfo)
	#extension = getAudioExtension(path_to_album)
	
	for song,songInfo in metadata['songs']:
		#figure out bitrate
		bitrate = getBitrate(path_to_album+'/'+song)
		if metadata['format'] != 'mp3' or bitrate>287.5:
			convertSong(metadata['path_to_album']+'/'+song)
			metadata[song.replace('.'+metadata['format'],'.mp3')] = metadata['songs'][song]
			metadata['songs'].pop(song)
		else:
			print("Bitrate of mp3 "+song+" is good at "+str(bitrate)+"; not converting")
	#generate album, artist, songs objects from pmt
	credentials = getCreds()
	songs_obj=[songLookup(song,path) for path,song in metadata['songs'] ]
	album=albumLookup()
	artist=artistLookup()

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


#old code:

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
