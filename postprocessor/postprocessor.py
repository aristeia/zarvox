import sys, os, subprocess

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

def calc_vbr(br):
	return round(10-10*pow(((br-60.0)/160.0),1.125),3)

def main(): 
	#Check sys.argv for path_to_album
	if len(sys.argv) != 2:
		print("Error: postprocessor received wrong number of args")
		exit(-2)

	path_to_album = string.strip(sys.argv[1], ' /')
	#Check if song format other than MP3
	#Get all extensions in the folder, order them by frequency, filter non-music ones,
	# then pick the most frequent remaining one or the most frequent one overall
	# (in the case that it's some obscure format not listed)
	extensions = [obj.split('.')[-1] for obj in os.listdir(path_to_album) if os.path.isfile(path_to_album+'/'+obj)]
	extensions_in_folder = list(set( map(lambda x: (x,extensions.count(x)) , extensions)))
	extension_vals = filter(lambda (x,y): y if y.lower() not in ['mp3','acc','flac','wav','ogg','ac3','alac'],extensions_in_folder)
	extension = extension_vals[0] if len(extension_vals) > 0 else extensions_in_folder[0]
	songs = [obj for obj in os.listdir(path_to_album) if obj.split('.')[-1] == extension]
	for song in songs:
		#figure out bitrate
		try:
			bitrate = float(subprocess.check_output("mp3info -r a "+song, shell=True)) #ceilreduce(lambda x, y: x + y, map(lambda x: ), songs)) / len(songs)
		except OSError as e:
			print("Error: cannot get bitrate properly:\n"+e)
			exit(-2)
		if extension != 'mp3' or bitrate>265:
			#Dequeue album from rtorrent 
			#Use proper MP3 VBR format for space efficiency + quality maximization
			if bitrate>220:
				vbr_format = 0.0
			elif bitrate<60:
				print("Error: bitrate too low at "+bitrate)
				exit(-2)
			else:
				vbr_format=calc_vbr(bitrate)
			#convert files to mp3 with lame
			try:
				retcode = subprocess.call("lame -V"+bitrate+" "+path_to_album+'/'+song+" "+path_to_album+'/'+('.'.join(song.split('.')[0:-1]))+".mp3", shell=True)
	    	if retcode < 0:
       	 print("Error: lame didn't execute properly")
       	 exit(retcode)
			except OSError as e:
    		print >>sys.stderr, "Execution failed:", e
				exit(-2)
		songs = map(lambda x: ('.'.join(x.split('.')[0:-1]))+".mp3",songs)
	#run pimpmytunes to determine basic metadata
	mode = pimpmytunes.PMT_MODE_AUTOMATIC
	for song in songs:
		try:
			pmt = pimpmytunes.PimpMyTunes("0.1.0", path_to_album)
			pmt.setDebug(False)
			pmt.setTerse(False)
			pmt.identify(song, mode)
		except pimpmytunes.NoSuchIndexError, msg:
			print("Error: issue with pimpmytunes metadata grabber:\n"+msg)
			exit(-2)
		#If album missing artist or album or song missing song name
			#Query Chromaprint and Acoustid
			#reget metadata
		#Get explicitness for each song
		#Get popularity per song
		#Get genres for album
		#Store all in db


