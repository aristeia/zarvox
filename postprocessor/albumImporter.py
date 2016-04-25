'''
Wrapper script for generate metadata & postprocessor

'''
import sys,os
sys.path.extend(os.listdir(os.getcwd()))
import generateMetadata, postprocessor

def albumImport(directoryPath = None):
    if directoryPath is not None:
        if len(sys.argv) == 1:
            sys.argv.append(directoryPath)
        else:
            sys.argv[1] = directoryPath
    generateMetadata.main()
    postprocessor.main()


if  __name__ == '__main__':
  albumImport()