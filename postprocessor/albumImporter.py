'''
Wrapper script for generate metadata & postprocessor

'''
import sys,os
sys.path.extend(os.listdir(os.getcwd()))
import generateMetadata, postprocessor

def albumImport(directoryPath = None, albumsFolder = None):
    if directoryPath is None:
        directoryPath = sys.argv[1]
    directoryPath = directoryPath.strip('/')
    generateMetadata.checkoutFolder(albumsFolder+'/'+directoryPath+'/')
    postprocessor.importDirectory(directoryPath, albumsFolder)


if  __name__ == '__main__':
  albumImport()