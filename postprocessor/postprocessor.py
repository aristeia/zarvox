import sys, os, 


try:
	from musicbrainz2.pimpmytunes import pimpmytunes
except:
	sys.path.append("..")
	from musicbrainz2.pimpmytunes import pimpmytunes

# All dicts are name:val
# genres would be genre_name:similarity/applicability and so forth
class song:
	name=""
	filename=""
	length=0
	explicit=False
	spotify_popularity=0
	lastfm_listeners=0
	lastfm_playcount=0

class album:
	name=""
	filepath=""
	songs=[]
	genres={}
	spotify_popularity=0
	lastfm_listeners=0
	lastfm_playcount=0
	whatcd_seeds=0
	whatcd_snatches=0

class artist:
	name=""
	albums=[]
	genres={}
	similar_artists={}
	spotify_popularity=0
	lastfm_listeners=0
	lastfm_playcount=0

def main(): 
	#Check sys.argv for path_to_album
	if len(sys.argv) != 2:
		print("Error: postprocessor received wrong number of args")
	else:
		path_to_album = string.strip(sys.argv[1], ' /')
		#If format other than MP3
		extensions = [ for obj in os.listdir(path_to_album) if os.path.isfile(path_to_album+'/'+obj) ]
			#Dequeue album from rtorrent
			#convert files to mp3
				#V0 if bitrate ave > 220, V1 if >190, V2 if 170, V3 if 150, V4 if 140, V5 if 120, V6 if 100, V7 if 80, V8 if 70, V9 if 60, delete otherwise & do error checking 

		#run pimpmytunes to determine basic metadata

		mode = pimpmytunes.PMT_MODE_AUTOMATIC
		try:
			pmt = pimpmytunes.PimpMyTunes("0.1.0", path_to_album)
			pmt.setDebug(False)
			pmt.setTerse(False)
			pmt.identify(, mode)
		except pimpmytunes.NoSuchIndexError, msg:
			print msg

	#Get basic metadata for album
	#If album missing artist or album or song missing song name
		#Query Chromaprint and Acoustid
		#reget metadata
	#Get explicitness for each song
	#Get popularity per song
	#Get genres for album
	#Store all in db


