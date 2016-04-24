'''
Wrapper script for generate metadata & postprocessor

'''
import sys,os
sys.path.extend(os.listdir(os.getcwd()))
import generateMetadata, postprocessor

generateMetadata.main()
postprocessor.main()