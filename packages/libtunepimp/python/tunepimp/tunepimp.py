#---------------------------------------------------------------------------
#
#   libtunepimp -- The MusicBrainz tagging library.  
#                  Let a thousand taggers bloom!
#   
#   Copyright (C) Robert Kaye 2003
#   
#   This file is part of libtunepimp.
#
#   libtunepimp is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   libtunepimp is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with libtunepimp; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#   $Id: tunepimp.py 8242 2006-07-22 10:33:56Z luks $
#
#---------------------------------------------------------------------------
import os, types, sys
from ctypes import *
import track

# TODO
#   Unhandled case - handle result_t casting cases   

# TPCallBackEnum values used for GetNotification
eFileAdded = 0;
eFileChanged = 1;
eFileRemoved = 2;
eWriteTagsComplete = 3;

# TPError returned by WriteTags and GetResults
eOk                     = 0
eTooManyPUIDs            = 1
eNoUserInfo             = 2
eLookupError            = 3
eSubmitError            = 4
eInvalidIndex           = 5
eInvalidObject          = 6

# TPFileStatus
eMetadataRead           = 0    # pending metadata read
ePending                = 1    # pending puid calculation
eUnrecognized           = 2    # unrecognized
eRecognized             = 3    # Recognized and previously saved
ePUIDLookup              = 4    # puid done, pending puid lookup
ePUIDCollision           = 5    # puid done, pending puid lookup
eFileLookup             = 6    # puid done, no matches, pending file lookup
eUserSelection          = 7    # file lookup done, needs user selection
eVerified               = 8    # User verified, about to write changes to disk 
eSaved                  = 9    # File was saved
eDeleted                = 10   # to be deleted, waiting for refcount == 0
eError                  = 11   # Error

# TPResultType
eNone                   = 0
eArtistList             = 1
eAlbumList              = 2
eTrackList              = 3
eMatchedTrack           = 4

# TPAlbumType
eAlbumType_Album        = 0
eAlbumType_Single       = 1
eAlbumType_EP           = 2
eAlbumType_Compilation  = 3
eAlbumType_Soundtrack   = 4
eAlbumType_Spokenword   = 5
eAlbumType_Interview    = 6
eAlbumType_Audiobook    = 7
eAlbumType_Live         = 8
eAlbumType_Remix        = 9
eAlbumType_Other        = 10;
eAlbumType_Error        = 11;

# TPAlbumStatus
eAlbumStatus_Official   = 0
eAlbumStatus_Promotion  = 1
eAlbumStatus_Bootleg    = 2

# TPID3Encoding
eLatin1                 = 0
eUTF8                   = 1
eUTF16                  = 2
eEncodingError          = 3

# TPThreadPriorityEnum
eIdle                   = 0
eLowest                 = 1
eLow                    = 2
eNormal                 = 3
eHigh                   = 4
eHigher                 = 5
eTimeCritical           = 6

# Thread identifiers
tpThreadNone            = 0x0000
tpThreadLookupPUID       = 0x0001
tpThreadLookupFile      = 0x0002
tpThreadWrite           = 0x0004
tpThreadRead            = 0x0008
tpThreadAnalyzer        = 0x0010
tpThreadAll             = 0xFFFF


class TunePimpError(Exception):
    pass
Error = TunePimpError

def toUTF8(text):
    '''Thus convenience function converts common types to strings with UTF-8 encoidng'''

    if text.__class__.__name__ == 'int' or text.__class__.__name__ == 'float':
        return str(text).decode("utf-8", 'replace')

    if text.__class__.__name__ == 'unicode' or text.__class__.__name__ == 'str':
        return text.encode("utf-8", 'replace')

    assert 0, "Don't know how to convert " + text.__class__.__name__ + " to UTF-8"

def _openLibrary(libName, version):
    """Opens a library using the ctypes cdll loader.

    raise TunePimpError, "Cannot find TunePimp shared library: " + lib
    The dynamic linker (ld.so on Un*x systems) is used to load the library,
    so it has to be in the linker search path. On some systems, such as
    Linux, the search path can be influenced using the C{LD_LIBRARY_PATH}
    environement variable.

    @param libName: library name without 'lib' prefix or version number
    @param version: a string containing a version number

    @return: a C{ctypes.CDLL} object, representing the opened library

    @raise NotImplementedError: if the library can't be opened
    """
    # This only works for ctypes >= 0.9.9.3. Any library with the given
    # name and version number is found, no matter how it's called on this
    # platform.
    try:
        if hasattr(cdll, 'load_version'):
            if sys.platform == 'win32':
                lib = cdll.load('lib%s' % (libName,))
            else:
                lib = cdll.load_version(libName, version)
            return lib
    except OSError, e:
        raise NotImplementedError('Error opening library: ' + str(e))

    # For compatibility with ctypes < 0.9.9.3 try to figure out the library
    # name without the help of ctypes. We use cdll.LoadLibrary() below,
    # which isn't available for ctypes == 0.9.9.3.
    #
    if sys.platform == 'linux2':
        fullName = 'lib%s.so.%s' % (libName, version)
    elif sys.platform == 'darwin':
        fullName = 'lib%s.%s.dylib' % (libName, version)
    elif sys.platform == 'win32':
        fullName = 'lib%s.dll' % (libName,)
    else:
        # This should at least work for Un*x-style operating systems
        fullName = 'lib%s.so.%s' % (libName, version)

    try:
        lib = cdll.LoadLibrary(fullName)
        return lib
    except OSError, e:
        raise NotImplementedError('Error opening library: ' + str(e))

    assert False # not reached

try:
    tplib = _openLibrary('tunepimp', '5')
except NotImplementedError, e:
    raise TunePimpError(str(e))
    
if sys.platform == "win32":
    tplib.tp_WSAInit.argtypes = [c_void_p]
    tplib.tp_WSAStop.argtypes = [c_void_p]

class tunepimp(object):
    '''This is the main tunepimp class. For details on how to use this class, 
       please look up the main tunepimp documentation'''

    BUFLEN = 255

    def __init__(self, appName, appVersion, threads=tpThreadAll, pluginDir = None):
        self.tplib = tplib
        tplib.tp_NewWithArgs.argtypes = [c_char_p, c_char_p, c_int, c_char_p]
        tplib.tp_NewWithArgs.restype = c_void_p
        self.tp = tplib.tp_NewWithArgs(toUTF8(appName), toUTF8(appVersion), threads, pluginDir)
        self.NTFFUNC = CFUNCTYPE(c_void_p, c_void_p, c_void_p, c_int, c_int, c_int)
        self.funcs = []

        # for ctypes 0.9.6
        if not isinstance(self.tp, c_void_p):
            self.tp = c_void_p(self.tp) 
        
        if sys.platform == "win32":
            tplib.tp_WSAInit(self.tp)

    tplib.tp_Delete.argtypes = [c_void_p]
    def __del__(self):
        if sys.platform == "win32":
            self.tplib.tp_WSAStop(self.tp)
            
        self.tplib.tp_Delete(self.tp)
        self.tplib = None

    tplib.tp_GetVersion.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p]
    def GetVersion(self):
        major = c_int()
        minor = c_int()
        rev = c_int()
        tplib.tp_GetVersion(self.tp, byref(major), byref(minor), byref(rev))
        return (major.value, minor.value, rev.value,)

    tplib.tp_SetServer.argtypes = [c_void_p, c_char_p, c_int]
    def setServer(self, server, port):
        tplib.tp_SetServer(self.tp, toUTF8(server), port)

    tplib.tp_GetServer.argtypes = [c_void_p, c_char_p, c_int]
    def getServer(self):
        server = c_buffer(self.BUFLEN)
        port = c_short()
        len = c_int(self.BUFLEN)
        tplib.tp_GetServer(self.tp, server, len, byref(port))
        return (unicode(server.value, "UTF-8", 'replace'), port.value)

    tplib.tp_SetProxy.argtypes = [c_void_p, c_char_p, c_short]
    def setProxy(self, server, port):
        tplib.tp_SetProxy(self.tp, toUTF8(server), port)

    tplib.tp_GetProxy.argtypes = [c_void_p, c_char_p, c_int, c_void_p]
    def getProxy(self):
        proxy = c_buffer(self.BUFLEN)
        port = c_short()
        len = c_int(self.BUFLEN)
        tplib.tp_GetProxy(self.tp, proxy, len, byref(port))
        return (unicode(proxy.value, "UTF-8", 'replace'), port.value) 

    tplib.tp_GetNumSupportedExtensions.argtypes = [c_void_p]
    def getNumSupportedExtensions(self):
        return tplib.tp_GetNumSupportedExtensions(self.tp)

    TP_EXTENSION_LEN = 32
    tplib.tp_GetSupportedExtensions.argtypes = [c_void_p, c_void_p]
    def getSupportedExtensions(self):
        num = self.getNumSupportedExtensions()
        extClass = c_char * self.TP_EXTENSION_LEN
        arrayClass = extClass * num
        extension = arrayClass()
        tplib.tp_GetSupportedExtensions(self.tp, extension)
        ret = []
        for ext in extension:
           value = ''.join(ext).replace('\000', '') 
           ret.append(unicode(value, "UTF-8", 'replace'))

        return ret

    tplib.tp_SetAnalyzerPriority.argtypes = [c_void_p, c_int]
    def setAnalyzerPriority(self, priority):
        tplib.tp_SetAnalyzerPriority(self.tp, priority)

    tplib.tp_GetAnalyzerPriority.argtypes = [c_void_p]
    def getAnalyzerPriority(self):
        return tplib.tp_GetAnalyzerPriority(self.tp)

    tplib.tp_GetNotification.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p]
    def getNotification(self):
        type = c_int()
        fileId = c_int()
        status = c_int()
        ret = tplib.tp_GetNotification(self.tp, byref(type), byref(fileId), byref(status))
        return (ret, type.value, fileId.value, status.value)

    tplib.tp_GetStatus.argtypes = [c_void_p, c_char_p, c_int]
    def getStatus(self):
        buf = c_buffer(self.BUFLEN)
        len = c_int(self.BUFLEN)
        ret = tplib.tp_GetStatus(self.tp, buf, len)
        return (ret, unicode(buf.value, "UTF-8", 'replace'))

    tplib.tp_GetError.argtypes = [c_void_p, c_char_p, c_int]
    def getError(self):
        buf = c_buffer(self.BUFLEN)
        len = c_int(self.BUFLEN)
        tplib.tp_GetError(self.tp, buf, len)
        return unicode(buf.value, "UTF-8", 'replace')

    tplib.tp_SetDebug.argtypes = [c_void_p, c_int]
    def setDebug(self, debug):
        tplib.tp_SetDebug(self.tp, debug)

    tplib.tp_GetDebug.argtypes = [c_void_p]
    def getDebug(self):
        return tplib.tp_GetDebug(self.tp)

    tplib.tp_AddFile.argtypes = [c_void_p, c_char_p, c_int]
    def addFile(self, file, readMetadataNow=0):
        return tplib.tp_AddFile(self.tp, toUTF8(file), readMetadataNow)

    tplib.tp_AddDir.argtypes = [c_void_p, c_char_p]
    def addDir(self, dir):
        return tplib.tp_AddDir(self.tp, toUTF8(dir))

    tplib.tp_Remove.argtypes = [c_void_p, c_int]
    def remove(self, file):
        tplib.tp_Remove(self.tp, file)

    tplib.tp_GetNumFiles.argtypes = [c_void_p]
    def getNumFiles(self):
        return tplib.tp_GetNumFiles(self.tp)

    tplib.tp_GetNumUnsavedItems.argtypes = [c_void_p]
    def getNumUnsavedItems(self):
        return tplib.tp_GetNumUnsavedItems(self.tp)

    tplib.tp_GetTrackCounts.argtypes = [c_void_p, c_void_p, c_int]
    maxCounts = 16
    def getTrackCounts(self):
        arrayClass = c_int * self.maxCounts
        counts = arrayClass()
        tplib.tp_GetTrackCounts(self.tp, counts, self.maxCounts)
        ret = []
        for count in counts:
           ret.append(count)
        return ret

    tplib.tp_GetFileIds.argtypes = [c_void_p, c_void_p, c_int]
    def getFileIds(self):
        num = self.getNumFiles()
        arrayClass = c_int * num
        ids = arrayClass()
        tplib.tp_GetFileIds(self.tp, ids, num)
        ret = []
        for id in ids:
           ret.append(id)
        return ret

    tplib.tp_GetTrack.argtypes = [c_void_p, c_int]
    tplib.tp_GetTrack.restype = c_void_p
    def getTrack(self, id):
        tr = track.track(self, tplib.tp_GetTrack(self.tp, id))
        return tr

    tplib.tp_ReleaseTrack.argtypes = [c_void_p, c_void_p]
    def releaseTrack(self, tr):
        tplib.tp_ReleaseTrack(self.tp, tr.getTrackObject())

    tplib.tp_Wake.argtypes = [c_void_p, c_void_p]
    def wake(self, tr):
        tplib.tp_Wake(self.tp, tr.getTrackObject())

    tplib.tp_Misidentified.argtypes = [c_void_p, c_int]
    def misidentified(self, fileId):
        tplib.tp_Misidentified(self.tp, fileId)

    tplib.tp_IdentifyAgain.argtypes = [c_void_p, c_int]
    def identifyAgain(self, fileId):
        tplib.tp_IdentifyAgain(self.tp, fileId)

    tplib.tp_SetMusicDNSClientId.argtypes = [c_void_p, c_void_p, c_int]
    def writeTags(self, fileIds):
        num = len(fileIds)
        arrayClass = c_int * num
        ids = arrayClass()
        for i in xrange(num):
            ids[i] = fileIds[i] 

        return tplib.tp_WriteTags(self.tp, ids, num)

    tplib.tp_SetNotifyCallback.argtypes = [c_void_p, c_void_p, c_void_p]
    def setNotifyCallback(self, func):
        cb = self.NTFFUNC(func)
        self.funcs.append(cb)
        tplib.tp_SetNotifyCallback(self.tp, cb, None)

    tplib.tp_SetMusicDNSClientId.argtypes = [c_void_p, c_char_p]
    def setMusicDNSClientId(self, clientId):
        tplib.tp_SetMusicDNSClientId(self.tp, clientId)
        
    tplib.tp_GetMusicDNSClientId.argtypes = [c_void_p]
    def getMusicDNSClientId(self):
        return tplib.tp_GetMusicDNSClientId(self.tp)
        
    tplib.tp_SetRenameFiles.argtypes = [c_void_p, c_int]
    def setRenameFiles(self, rename):
        tplib.tp_SetRenameFiles(self.tp, rename)

    tplib.tp_GetRenameFiles.argtypes = [c_void_p]
    def getRenameFiles(self):
        return tplib.tp_GetRenameFiles(self.tp)
        
    tplib.tp_SetMoveFiles.argtypes = [c_void_p, c_int]
    def setMoveFiles(self, move):
        tplib.tp_SetMoveFiles(self.tp, move)

    tplib.tp_GetMoveFiles.argtypes = [c_void_p]
    def getMoveFiles(self):
        return tplib.tp_GetMoveFiles(self.tp)

    tplib.tp_SetFileNameEncoding.argtypes = [c_void_p, c_char_p]
    def setFileNameEncoding(self, encoding):
        tplib.tp_SetFileNameEncoding(self.tp, toUTF8(encoding))

    tplib.tp_GetFileNameEncoding.argtypes = [c_void_p, c_char_p, c_int]
    def getFileNameEncoding(self):
        encoding = c_buffer(self.BUFLEN)
        encodingLen = c_int(self.BUFLEN)
        tplib.tp_GetFileNameEncoding(self.tp, encoding, encodingLen)
        return unicode(encoding.value, "UTF-8", 'replace')

    tplib.tp_SetWriteID3v1.argtypes = [c_void_p, c_int]
    def setWriteID3v1(self, write):
        tplib.tp_SetWriteID3v1(self.tp, write)

    tplib.tp_GetWriteID3v1.argtypes = [c_void_p]
    def getWriteID3v1(self):
        return tplib.tp_GetWriteID3v1(self.tp)

    tplib.tp_SetWriteID3v2_3.argtypes = [c_void_p, c_int]
    def setWriteID3v2_3(self, write):
        tplib.tp_SetWriteID3v2_3(self.tp, write)

    tplib.tp_GetWriteID3v2_3.argtypes = [c_void_p]
    def getWriteID3v2_3(self):
        return tplib.tp_GetWriteID3v2_3(self.tp)

    tplib.tp_SetID3Encoding.argtypes = [c_void_p, c_int]
    def setID3Encoding(self, write):
        tplib.tp_SetID3Encoding(self.tp, write)

    tplib.tp_GetID3Encoding.argtypes = [c_void_p]
    def getID3Encoding(self):
        return tplib.tp_GetID3Encoding(self.tp)

    tplib.tp_SetClearTags.argtypes = [c_void_p, c_int]
    def setClearTags(self, clear):
        tplib.tp_SetClearTags(self.tp, clear)

    tplib.tp_GetClearTags.argtypes = [c_void_p]
    def getClearTags(self):
        return tplib.tp_GetClearTags(self.tp)

    tplib.tp_SetFileMask.argtypes = [c_void_p, c_char_p]
    def setFileMask(self, mask):
        tplib.tp_SetFileMask(self.tp, toUTF8(mask))

    tplib.tp_GetFileMask.argtypes = [c_void_p, c_char_p, c_int]
    def getFileMask(self):
        mask = c_buffer(self.BUFLEN)
        len = c_int(self.BUFLEN)
        tplib.tp_GetFileMask(self.tp, mask, len)
        return unicode(mask.value, "UTF-8", 'replace')

    tplib.tp_SetVariousFileMask.argtypes = [c_void_p, c_char_p]
    def setVariousFileMask(self, mask):
        tplib.tp_SetVariousFileMask(self.tp, toUTF8(mask))

    tplib.tp_GetVariousFileMask.argtypes = [c_void_p, c_char_p, c_int]
    def getVariousFileMask(self):
        mask = c_buffer(self.BUFLEN)
        len = c_int(self.BUFLEN)
        tplib.tp_GetVariousFileMask(self.tp, mask, len)
        return unicode(mask.value, "UTF-8", 'replace')

    tplib.tp_SetNonAlbumFileMask.argtypes = [c_void_p, c_char_p]
    def setNonAlbumFileMask(self, mask):
        tplib.tp_SetNonAlbumFileMask(self.tp, toUTF8(mask))

    tplib.tp_GetNonAlbumFileMask.argtypes = [c_void_p, c_char_p, c_int]
    def getNonAlbumFileMask(self):
        mask = c_buffer(self.BUFLEN)
        len = c_int(self.BUFLEN)
        tplib.tp_GetNonAlbumFileMask(self.tp, mask, len)
        return unicode(mask.value, "UTF-8", 'replace')

    tplib.tp_SetAllowedFileCharacters.argtypes = [c_void_p, c_char_p]
    def setAllowedFileCharacters(self, allowedChars):
        tplib.tp_SetAllowedFileCharacters(self.tp, toUTF8(allowedChars))

    tplib.tp_GetAllowedFileCharacters.argtypes = [c_void_p, c_char_p, c_int]
    def getAllowedFileCharacters(self):
        chrs = c_buffer(self.BUFLEN)
        len = c_int(self.BUFLEN)
        tplib.tp_GetAllowedFileCharacters(self.tp, chrs, len)
        return unicode(chrs.value, "UTF-8", 'replace')

    tplib.tp_SetWinSafeFileNames.argtypes = [c_void_p, c_int]
    def setWinSafeFileNames(self, value):
        tplib.tp_SetWinSafeFileNames(self.tp, value)

    tplib.tp_GetWinSafeFileNames.argtypes = [c_void_p]
    def getWinSafeFileNames(self):
        return tplib.tp_GetWinSafeFileNames(self.tp)

    tplib.tp_SetDestDir.argtypes = [c_void_p, c_char_p]
    def setDestDir(self, destDir):
        tplib.tp_SetDestDir(self.tp, toUTF8(destDir))

    tplib.tp_GetDestDir.argtypes = [c_void_p, c_char_p, c_int]
    def getDestDir(self):
        dir = c_buffer(self.BUFLEN)
        len = c_int(self.BUFLEN)
        tplib.tp_GetDestDir(self.tp, dir, len)
        return unicode(dir.value, "UTF-8", 'replace')

    tplib.tp_SetTopSrcDir.argtypes = [c_void_p, c_char_p]
    def setTopSrcDir(self, topSrcDir):
        tplib.tp_SetTopSrcDir(self.tp, toUTF8(topSrcDir))

    def getTopSrcDir(self):
        dir = c_buffer(self.BUFLEN)
        len = c_int(self.BUFLEN)
        tplib.tp_GetTopSrcDir(self.tp, dir, len)
        return unicode(dir.value, "UTF-8", 'replace')

    tplib.tp_SetAutoSaveThreshold.argtypes = [c_void_p, c_int]
    def setAutoSaveThreshold(self, thres):
        tplib.tp_SetAutoSaveThreshold(self.tp, thres)

    tplib.tp_GetAutoSaveThreshold.argtypes = [c_void_p]
    def getAutoSaveThreshold(self):
        return tplib.tp_GetAutoSaveThreshold(self.tp)

    tplib.tp_SetMaxFileNameLen.argtypes = [c_void_p, c_int]
    def setMaxFileNameLen(self, len):
        tplib.tp_SetMaxFileNameLen(self.tp, len)

    tplib.tp_GetMaxFileNameLen.argtypes = [c_void_p]
    def getMaxFileNameLen(self):
        return tplib.tp_GetMaxFileNameLen(self.tp)

    tplib.tp_SetAutoRemovedSavedFiles.argtypes = [c_void_p, c_int]
    def setAutoRemovedSavedFiles(self, autoRemove):
        tplib.tp_SetAutoRemovedSavedFiles(self.tp, autoRemove)

    tplib.tp_GetAutoRemovedSavedFiles.argtypes = [c_void_p]
    def getAutoRemovedSavedFiles(self):
        return tplib.tp_GetAutoRemovedSavedFiles(self.tp)

