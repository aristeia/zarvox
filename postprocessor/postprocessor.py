import sys, os, subprocess, json, Levenshtein, musicbrainzngs as mb, postgresql as pg
sys.path.extend(os.listdir(os.getcwd()))
import postgresql.driver as pg_driver
from math import ceil
import whatapi
import pickle
from functools import reduce
from libzarv import *
from lookup import *
from musicClasses import *
from database import databaseCon
#from pimpmytunes.pimpmytunes.pimpmytunes import PimpMyTunes
from numpy import float128


def startup_tests(credentials):
	#Check sys.argv for path_to_album
	if len(sys.argv) != 2:
		print("Error: postprocessor received wrong number of args")
		exit(1)
	try:
	  db = pg_driver.connect(
	    user = credentials['db_user'],
	    password = credentials['db_password'],
	    host = 'localhost',
	    port = 5432,
	    database  = credentials['db_name'])
	except Exception as e:
	  print("Error: cannot connect to database",file=sys.stderr)
	  print(e,file=sys.stderr)
	  exit(1)
	print("Zarvox database are online")
	# try:
	# 	pingtest(['whatcd','lastfm','spotify','lyrics', 'music'])
	# except Exception:
	# 	print(e)
	# 	exit(1)
	print("Pingtest complete; sites are online")
	return db

def getAlbumPath(albums_folder, arg):
	temp = '/'+albums_folder.strip(' /') + '/'+arg.strip('/')
	if not os.path.isdir(temp):
		print("Error: postprocessor received a bad folder path")
		print('"'+temp+'"')
		exit(1)
	print("Found folder "+temp)
	return temp


def convertSong(song_path, bitrate):
	#Dequeue album from rtorrent 
	#Use proper MP3 VBR format for space efficiency + quality maximization
	if bitrate>220:
		vbr_format = 0.0
	elif bitrate<60:
		print("Error: bitrate too low at "+bitrate)
		return False
	else:
		vbr_format=calc_vbr(bitrate)
	#convert files to mp3 with lame
	try:
		subprocess.call("lame -V"+vbr_format+" '"+song_path.replace("'","'\\''")+"'' '"+('.'.join(song_path.split('.')[0:-1]))+".mp3'", shell=True)
	except Exception as e:
		print("LAME conversion failed:\n")
		print(e)
		return False
	return True

def getBitrate(path_to_song):
	try:
		bitrate = float(subprocess.check_output("exiftool -AudioBitrate '"+path_to_song.replace("'","'\\''")+"'", shell=True).split()[-2]) 
	except Exception as e:
		print("Error: cannot get bitrate properly:")
		print(e)
		print("Will try converting anyway")
		bitrate = 276 # max bitrate +1
	return bitrate

def getDuration(path_to_song):
	try:
		durations = str(subprocess.check_output("exiftool -Duration '"+path_to_song.replace("'","'\\''")+"'", shell=True)).split()[2].split(':')
		duration = reduce(lambda x,y:x+y,[float(durations[x])*pow(60,len(durations)-1-x) for x in range(len(durations))]) 
	except Exception as e:
		print("Error: cannot get duration properly for "+path_to_song+":\n")
		print(e)
		exit(1)
	return ceil(duration)

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
		mb.set_useragent('Zarvox_Automated_DJ','Alpha',"KUPS' Webmaster (Jon Sims) at communications@kups.net")
		mb.set_rate_limit()
		artists = mb.search_artists(artist=mbquote(metadata['artist']), limit=10)['artist-list']
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
				, mb.search_releases(arid=x['id'], release=mbquote(metadata['album']),limit=8)['release-list'])
				if len(x)!=0 else None
				, artists) if x is not None])
		songAssoc = []
		albumInfo = mb.get_release_by_id(id=reid['id'], includes=['recordings'])
		for x in albumInfo['release']['medium-list']:
			for y in x['track-list']:
				temp = {}
				temp['name'] = y['recording']['title']
				temp['filename'] = ((str(int(songAssoc[-1]['filename'][0:2])+1) if len(songAssoc)!=0 else '01')
					+'-'+metadata['artist'].replace(' ','_')
					+'-'+y['recording']['title'].replace(' ','_')
					+'.'+metadata['format'])
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
			temp['filename']=((('0'+str(lastfmSong[1])) if int(lastfmSong[1])<10 else str(lastfmSong[1]))
				+'-'+metadata['artist'].replace(' ','_')
				+'-'+lastfmSong[0].replace(' ','_')
				+'.'+metadata['format'])
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

def associateSongToFile(songInfo, fileInfo, path):
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
			xTitle = str(subprocess.check_output("exiftool -Title '"+(path+'/'+x['name']).replace("'","'\\''")+"' | cut -d: -f2-10",shell=True).decode('utf8').strip())
			if xTitle!='':
				xTitle = ' '.join(xTitle.split()[2:])[:-3]
			yTitle = str(subprocess.check_output("exiftool -Title '"+(path+'/'+y['name']).replace("'","'\\''")+"' | cut -d: -f2-10",shell=True).decode('utf8').strip())
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
	db = startup_tests(credentials)
	con = databaseCon(db)
	conf = getConfig()
	cookies = pickle.load(open('config/.cookies.dat', 'rb'))
	apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'], cookies=cookies)
	data = getData(getAlbumPath(conf['albums_folder'],sys.argv[1]))
	metadata = data['metadata']
	fileInfo = data['fileAssoc']
	for f in fileInfo:
	# 	f['duration'] = getDuration(metadata['path_to_album']+'/'+f['name'])
	# metadata['songs'] = associateSongToFile( getSongInfo(metadata), fileInfo, metadata['path_to_album']) 	
		f['duration'] = getDuration(metadata['path_to_album']+'/'+f['path'])
	metadata['songs'] = dict([
		(f['fname'],
			{'name':f['track'],
			'duration': f['duration'],
			'size':f['size']}) for f in data['fileAssoc']])
	#extension = getAudioExtension(path_to_album)
	
	for song,songInfo in list(metadata['songs'].items()):
		#figure out bitrate
		bitrate = getBitrate(metadata['path_to_album']+'/'+song)
		if metadata['format'] != 'mp3' or bitrate>300:
			if not convertSong(metadata['path_to_album']+'/'+song, bitrate):
				print("Removing "+song+" from db")
				metadata.pop(song)
			else:
				metadata[song.replace('.'+metadata['format'],'.mp3')] = metadata['songs'][song]
				if song != song.replace('.'+metadata['format'],'.mp3'):
					metadata['songs'].pop(song)
		else:
			print("Bitrate of mp3 "+song+" is good at "+str(bitrate)+"; not converting")
	#generate album, artist, songs objects from pmt

	# print("Artist obj:\n"+str(artist),'\n\nAlbum obj:\n',str(album),"\nSong objs:\n")
	# for song in songs:
	# 	print(str(song))
	# # #Store all in db
	res = {}

	artists=[artistLookup(a,apihandle, True, con) for a in metadata['artists']]
	res['artists'] = con.getArtistsDB(artists,True)
	print("Done with artists")
	album=albumLookup(metadata,apihandle,con)
	res['album'] = con.getAlbumDB( album,True,db_artistid=res['artists'][0]['select'][0])

	if res['album'][0]['select'][2] != metadata['path_to_album']:
		print("Error: album is already in DB under other album path; reverting changes")
		album = Album(res['album'][0]['response'][1],
			res['album'][0]['response'][2],
			album.genres,
		  	album.spotify_popularity,
		  	album.lastfm_listeners,
		  	album.lastfm_playcount,
		  	album.whatcd_seeders,
		  	album.whatcd_snatches,
		  	album.pitchfork_rating,
			res['album'][0]['response'][10],
			res['album'][0]['response'][8])
		res['album'][0] = con.getAlbumDB( album,True,db_artistid=res['artists'][0]['select'][0])
	else:
		print("Done with album")

		songs=[songLookup(metadata,song,path,con=con) for path,song in metadata['songs'].items() ]
		lst = {
		    'sp':[song.spotify_popularity for song in songs],
		    'll':[song.lastfm_listeners for song in songs],
		    'lp':[song.lastfm_playcount for song in songs],
		    'kp':[song.kups_playcount for song in songs]
		  }

		for song in songs:
		  song.popularity = con.popularitySingle( 'songs'+metadata['album'].replace(' ','_')+'_'+(', '.join(metadata['artists'])).replace(' ','_'), 
		    spotify_popularity=song.spotify_popularity,
		    lastfm_listeners=song.lastfm_listeners,
		    lastfm_playcount=song.lastfm_playcount,
		    kups_playcount=song.kups_playcount,
		    lists=lst)
		res['song'] = con.getSongsPopDB(songs, True, db_albumid=res['album'][0]['select'][0])
	  
		print("Done with songs")

	res['artists_albums'] = con.getArtistAlbumDB(res['album'][0]['select'][0],True, [artist['select'][0] for artist in res['artists']])

	abgenres = con.getGenreDB( [x for x in album.genres.keys()], apihandle,'album_',True)
	argenres = con.getGenreDB( list(set([x for artist in artists for x in artist.genres.keys() if x not in album.genres])), apihandle,'artist_',True)
	res['genre'] = abgenres+argenres
	album.genres = correctGenreNames(album.genres, abgenres)
	for artist in artists:
	  artist.genres = correctGenreNames(artist.genres, argenres)
	print("Done with genres")

	res['album_genre'] = con.getAlbumGenreDB( album.genres, True,album=res['album'][0]['select'])
	print("Done with album genres")

	res['artist_genre'] = [lst for artist, dbartist in zip(artists,res['artists']) for lst in con.getArtistGenreDB( artist.genres, True,artist=dbartist['select'])]

	print("Done with artist genres")
	res['similar_artist'], res['other_artist'], res['other_similar'] = [],[],[]
	for artist,dbartist in zip(artists,res['artists']):
	  temp = con.getSimilarArtistsDB(artist.similar_artists, apihandle, dbartist['select'],True)
	  res['similar_artist'].extend(temp[0])
	  res['other_artist'].extend(temp[1])
	  res['other_similar'].extend(temp[2])

	print("Done working with database")
	print("The following values exist:")
	con.printRes(res)
	pickle.dump(apihandle.session.cookies, open('config/.cookies.dat', 'wb'))

if  __name__ == '__main__':
	main()