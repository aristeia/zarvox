'''
Wrapper script for albumImporter for all directories in album folder

'''
import sys,os,json
sys.path.extend(os.listdir(os.getcwd()))
from albumImporter import albumImport
from libzarv import getConfig, handleError
from random import shuffle

root_dir = getConfig()["albums_folder"]
metadata_filename = root_dir+"/.metadata.json"

if os.path.isfile(metadata_filename):
    with open(metadata_filename,"r") as f:
        directories = json.load(f)
else:
    directories = []

def writeToFile():
    with open(metadata_filename,"w") as f:
        json.dump(directories, f)

try:
    lstdir = os.listdir(root_dir)
    totalDirs = str(len(lstdir))
    shuffle(lstdir)
    for path in lstdir:
        if u'\udcb0' not in path and u'\udcf6' not in path and path not in directories:
            directories.append(path)
            try:
                print("Importing '"+path+"'")
                albumImport(path, root_dir)
            except Exception as e:
                handleError(e, "Warning: issue with directory '"+path+"'")
            if len(directories) % 25 == 0:
                writeToFile()
            print("Done with folder "+str(len(directories))+"/"+totalDirs)
except Exception:
    pass
writeToFile()