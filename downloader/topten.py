import sys
sys.path.append("../packages")
import whatapi
from libzarv import *


def main():
	try:
		pingtest(['whatcd'])
	except Exception,e:
		print(e)
		exit(1)
	credentials = {}
	with open("../config/credentials") as f:
		for line in iter(f):
			credentials[line.split('=')[0].strip()] = line.split('=')[1].strip()
	try:
		apihandle = whatapi.WhatAPI(username=credentials['username'], password=credentials['password'])
	except Exception as e:
		print("Error: cannot log into what.cd\n"+str(e))
		exit(1)
	data = apihandle.request("top10", limit=10)
	torIds = map(lambda x: str(x["torrentId"]), data["response"][0]["results"])
	folderPath = ""
	with open("../config/config") as f:
		for line in iter(f):
			if line.split('=')[0].strip() == "torrents_folder":
				folderPath = line.split('=')[1].strip()+'/'
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
			for _ in range(3):
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