'''
Wrapper script for generate metadata & postprocessor

'''
import sys,os
sys.path.extend(os.listdir(os.getcwd()))
import generateMetadata, postprocessor
from libzarv import getConfig

def albumImport(directoryPath = None, albumsFolder = None):
    if directoryPath is None:
        directoryPath = sys.argv[1]
        albumsFolder = getConfig()['albums_folder']
        postprocessor.main(False)
    directoryPath = directoryPath.strip('/')
    generateMetadata.checkoutFolder(albumsFolder+'/'+directoryPath+'/')
    if os.path.isfile(albumsFolder+'/'+directoryPath+'/.metadata.json'):
        postprocessor.importDirectory(directoryPath, albumsFolder)


if  __name__ == '__main__':
  albumImport()