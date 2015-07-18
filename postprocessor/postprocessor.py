import sys, os, subprocess, json, Levenshtein, musicbrainzngs as mb, postgresql as pg
sys.path.append("packages")
import whatapi
import pickle
from functools import reduce
from libzarv import *
from lookup import *
from libzarvclasses import *
from database import databaseCon
#from pimpmytunes.pimpmytunes.pimpmytunes import PimpMyTunes
from numpy import float128


def startup_tests(args,credentials):
	#Check sys.argv for path_to_album
	if len(args) != 2:
		print("Error: postprocessor received wrong number of args")
		exit(1)
	try:
		db = pg.open('pq://'+credentials['db_user']+':'+credentials['db_passwd']+'@localhost/'+credentials['db_name'])
	except Exception:
		print("Error: cannot connect to database\n")
		exit(1)
	print("Zarvox database are online")
	try:
		pingtest(['whatcd','lastfm','spotify','lyrics', 'music'])
	except Exception:
		print(e)
		exit(1)
	print("Pingtest complete; sites are online")
	return db

def getAlbumPath(albums_folder, arg):
	temp = '/'+albums_folder.strip(' /') + '/'+arg.strip('/')
	if not os.path.isdir(temp):
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
		subprocess.call("lame -V"+vbr_format+" '"+song_path.replace("'","'\''")+"'' '"+('.'.join(song_path.split('.')[0:-1]))+".mp3'", shell=True)
	except Exception:
		print("Execution failed:\n")
		exit(1)

def getBitrate(path_to_song):
	try:
		bitrate = float(subprocess.check_output("exiftool -AudioBitrate '"+path_to_song.replace("'","'\''")+"'", shell=True).split()[-2]) 
	except Exception:
		print("Error: cannot get bitrate properly:\n")
		print("Will try converting anyway")
		bitrate = 276 # max bitrate +1
	return bitrate

def getDuration(path_to_song):
	try:
		durations = str(subprocess.check_output("exiftool -Duration '"+path_to_song+"'", shell=True)).split()[2].split(':')
		duration = reduce(lambda x,y:x+y,[int(durations[x])*pow(60,2-x) for x in range(len(durations))]) 
	except Exception:
		print("Error: cannot get duration properly:\n")
		exit(1)
	return duration

def getSongInfo(metadata):
	def levi_brainzalbum(x,y):
		lx = Levenshtein.ratio(x['title'].lower(),metadata['album'].lower())
		ly = Levenshtein.ratio(y['title'].lower(),metadata['album'].lower())
		if lx==ly:
			if 'country' in x:
				return x if x['country']=='US' else y
			elif 'country' in y:
				return y if y['country']=='US' else x
		return y if ly>lx else x
	def levi_brainz(x,y):
		lx = ((Levenshtein.ratio(x['title'].lower(),metadata['album'].lower())*2.0)
			+(Levenshtein.ratio(x['title'].lower(),metadata['album'].lower())))
		ly = (Levenshtein.ratio(y['title'].lower(),metadata['album'].lower())*2.0)
		if lx==ly:
			if 'country' in x:
				return x if x['country']=='US' else y
			elif 'country' in y:
				return y if y['country']=='US' else x
		return y if ly>lx else x
	def getMusicBrains():
		mb.set_useragent('Zarvox Automated DJ','Pre-Alpha',"KUPS' Webmaster (Jon Sims) at jsims@pugetsound.edu")
		artists = mb.search_artists(artist=metadata['artist'], limit=10)['artist-list']
		if len(artists)==0:
			print("Musicbrainz returned 0 artists; skipping data source...")
			return None
		arids = filter(lambda x: 
			(Levenshtein.ratio(x['name'], metadata['artist'])>0.874
				or ((Levenshtein.ratio(x['name'], metadata['artist'])*len(metadata['artist']))-len(metadata['artist']))==2)
			, sorted(artists, key=(lambda x:Levenshtein.ratio(str(x['name']).lower(), metadata['artist'].lower()))))
		#print arids
		reid  = reduce(lambda x,y: levi_brainz(x,y), 
			[x for x in map(lambda x: 
			reduce(lambda y,z:levi_brainzalbum(z,y)
				, mb.search_releases(arid=x['id'], release=metadata['album'],limit=8)['release-list'])
				if len(x)!=0 else None
				, artists) if x is not None])
		songAssoc = []
		albumInfo = mb.get_release_by_id(id=reid['id'], includes=['recordings'])
		for x in albumInfo['release']['medium-list']:
			for y in x['track-list']:
				temp = {}
				temp['name'] = y['recording']['title']
				temp['filename'] = (str(int(songAssoc[-1]['filename'][0:2])+1) if len(songAssoc)!=0 else '01')+'-'+metadata['artist'].replace(' ','_')+'-'+y['recording']['title'].replace(' ','_')+'.'+metadata['format']
				if temp['filename'][1]=='-':
					temp['filename'] = '0'+temp['filename']
				print(temp['filename'])
				if 'duration' in y['recording']:
					temp['duration'] = y['recording']['duration']
				elif 'duration' in y:
					temp['duration'] = y['duration']
				else:
					temp['duration'] = y['track_or_recording_length']
				temp['duration'] = round(float(temp['duration'])/1000.0)
				songAssoc.append(temp)
		return songAssoc
	def getLastfm():
		lastfmList = lookup('lastfm','album',{'artist':metadata['artist'], 'album':metadata['album']})['album']['tracks']['track']
		songList = [ (track['name'],track['@attr']['rank'],track['duration']) for track in lastfmList]
		songAssoc = []
		for lastfmSong in songList:
			temp = {}
			temp['name'] = lastfmSong[0] #sanitize for unicode?
			temp['filename']=(('0'+str(lastfmSong[1])) if int(lastfmSong[1])<10 else str(lastfmSong[1]))+'-'+metadata['artist'].replace(' ','_')+'-'+lastfmSong[0].replace(' ','_')+'.'+metadata['format']
			temp['duration']=int(lastfmSong[2])
			songAssoc.append(temp)
		print("Got song info from lastfm")
		return songAssoc
	allAssoc = None
	print("Looking up song info on music brains...")
	allAssoc = getMusicBrains()
	if allAssoc is not None:
		return allAssoc
	print("Music brainz didn't work, looking up song info on lastfm...")
	allAssoc['lastfm'] = getLastfm()
	print("Done getting song info")
	return allAssoc
	

def getData(path):
	try:
		with open(path+"/.metadata.json") as f:
			data = json.loads(f.read())
	except Exception:
		print("Error: cannot read album metadata")
		exit(1)
	return data

def associateSongToFile( songInfo,fileInfo,path):
	def levi_song(x,y,song):
		#Data that will be available to us about the files:
		#name[/title], duration
		#Song:
		#lastfm and brainz averaged if existant 
		#name/title, duration
		#Weights:
		# 40[,80],60	 
		xTitle=''
		yTitle=''
		try:
			xTitle = str(subprocess.check_output("exiftool -Title '"+path+'/'+x['name']+"'",shell=True))
			if xTitle!='':
				xTitle = ' '.join(xTitle.split()[2:])[:-3]
			yTitle = str(subprocess.check_output("exiftool -Title '"+path+'/'+y['name']+"'",shell=True))
			if yTitle!='':
				yTitle = ' '.join(yTitle.split()[2:])[:-3]
		except Exception:
			print("Error: cannot check title of song "+song['name']+"\n")
			exit(1)
		try:
			l1x = float128(Levenshtein.ratio(x['name'],song['filename']))*0.4
			l1y = float128(Levenshtein.ratio(y['name'],song['filename']))*0.4
			if xTitle!='' and yTitle!= '':
				l1x+=float128(Levenshtein.ratio(xTitle,song['name']))*0.8
				l1y+=float128(Levenshtein.ratio(yTitle,song['name']))*0.8
		except Exception:
			print("Error: cannot get levi ratio between songname and filenames\n")
			exit(1)
		try:
			l2x = ((song['duration']-abs(float128(song['duration'])-x['duration']))/song['duration'])*0.6
			l2y = ((song['duration']-abs(float128(song['duration'])-y['duration']))/song['duration'])*0.6
		except Exception:
			print("Error: cannot get levi ratio between songduration and fileduration\n")
			exit(1)
		return x if (l1x+l2x)>(l1y+l2y) else y
	assoc = {}
	for song in sorted(songInfo,key=(lambda x:len(x['name'])),reverse=True):
		sfile = reduce(lambda x,y: levi_song(x,y,song) ,fileInfo)
		song['size'] = sfile['size']
		song.pop('filename')
		assoc[sfile['name']] = song
		fileInfo.remove(sfile)
	for key,val in assoc.items():
		print("Key is "+key+"\t Val is:"+str(val)+"\n")
	return assoc


#Usage (to be ran from root of zarvox): python postprocessor.py 'album_folder'
def main(): 
	credentials = getCreds()
	db = startup_tests(sys.argv,credentials)
	conf = getConfig()
	cookies = pickle.load(open('config/.cookies.dat', 'rb'))
	apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
	data = getData(getAlbumPath(conf['albums_folder'],sys.argv[1]))
	metadata = data['metadata']
	fileInfo = data['fileAssoc']
	for f in fileInfo:
		f['duration'] = getDuration(metadata['path_to_album']+'/'+f['name'])
	metadata['songs'] = associateSongToFile( getSongInfo(metadata),fileInfo,metadata['path_to_album'])
	#extension = getAudioExtension(path_to_album)
	
	for song,songInfo in metadata['songs'].items():
		#figure out bitrate
		bitrate = getBitrate(metadata['path_to_album']+'/'+song)
		if metadata['format'] != 'mp3' or bitrate>300:
			convertSong(metadata['path_to_album']+'/'+song)
			metadata[song.replace('.'+metadata['format'],'.mp3')] = metadata['songs'][song]
			metadata['songs'].pop(song)
		else:
			print("Bitrate of mp3 "+song+" is good at "+str(bitrate)+"; not converting")
	#generate album, artist, songs objects from pmt
	songs_obj=[songLookup(metadata,song,path) for path,song in metadata['songs'].items() ]
	album=albumLookup(metadata,apihandle)
	artist=artistLookup(metadata['artist'],apihandle)

	print("Artist obj:\n"+str(artist),'\n\nAlbum obj:\n',str(album),"\nSong objs:\n")
	for song in songs_obj:
		print(str(song))
	# #Store all in db
	con = databaseCon(db)
	con.getArtistDB( artist)
	con.getAlbumDB( album)
	con.getSongsDB( songs_obj)

	#store genres
	# con.getGenreDB( [x for x,_ in album.genres.items()], apihandle,'album_')
	# con.getGenreDB( [x for x,_ in artist.genres.items()], apihandle,'artist_')
	# #attach them to album & artist all by ids
	# con.getAlbumGenreDB( album.genres)
	# con.getArtistGenreDB( artist.genres)
	#store similar artist
	con.getSimilarArtistsDB( artist.similar_artists,apihandle,None)

	print("Done working with database")
	print("The following values exist:")
	con.printRes()
	pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))

if  __name__ == '__main__':
	main()