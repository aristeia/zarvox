'''
Wrapper script for albumImporter for all directories in album folder

'''
import sys,os,json
sys.path.extend(os.listdir(os.getcwd()))
from albumImporter import albumImport
from libzarv import getConfig, handleException

root_dir = getConfig()["albums_folder"]
metadata_filename = root_dir+"/.metadata.json"

if os.path.isfile(metadata_filename):
    with open(metadata_filename,"r") as f:
        directories = json.load(f)
else:
    directories = []

try:
    for path in os.listdir():
        if path not in directories:
            directories.append(path)
            try:
                print("Importing '"+path+"'")
                albumImport(path)
            except Exception as e:
                handleException(e, "Warning: issue with directory '"+path+"'")
except Exception:
    pass

with open(metadata_filename,"w") as f:
    directories = json.dump(directories, f)