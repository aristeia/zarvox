import sys
sys.path.append("packages")
import whatapi
from libzarv import *


#old; replaced by everything lookup

def main():
	try:
		pingtest(['whatcd'])
	except Exception:
		print("Error: cannot ping whatcd")
		exit(1)
	credentials = getCreds()
	config = getConf()
	try:
		apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'])
	except Exception as e:
		print("Error: cannot log into what.cd\n"+str(e))
		exit(1)
	data = apihandle.request("top10", limit=10)
	torIds = map(lambda x: str(x["torrentId"]), data["response"][0]["results"])
	folderPath = config['torrents_folder']+'/'
	if folderPath == "":
		print("Error: cannot find torrents_folder value in config file")
		exit(1)
	for tor in torIds:
		torPath = folderPath+tor+".torrent"
		t=None
		try:
			t = apihandle.get_torrent(tor)
			print("Downloaded "+tor)
		except Exception as e:
			print("Error: cannot retreive torrent for "+tor+" despite being able to connect to what.cd\n"+str(e)+"\nTrying a few more times...")
			for _ in xrange(3):
				time.sleep(10)
				if not os.path.isfile(torPath):
					try:
						t = apihandle.get_torrent(tor)
					except:
						pass
		if t is not None:
			with open(torPath, 'wb') as fd:
				fd.write(t)
			print("Saved "+tor)

if  __name__ =='__main__':
	main()