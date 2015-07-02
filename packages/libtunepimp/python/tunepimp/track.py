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
#   $Id: track.py 7869 2006-06-17 15:30:06Z luks $
#
#---------------------------------------------------------------------------

from ctypes import *
import metadata
import traceback
TP_ARTIST_NAME_LEN = 255
TP_ALBUM_NAME_LEN = 255
TP_TRACK_NAME_LEN = 255
TP_ID_LEN = 40
TP_COUNTRY_LEN = 3
TP_FILENAME_LEN = 1024
TP_ERROR_LEN = 1024

artistNameType = c_char * TP_ARTIST_NAME_LEN
albumNameType = c_char * TP_ALBUM_NAME_LEN
trackNameType = c_char * TP_TRACK_NAME_LEN
idType = c_char * TP_ID_LEN
releaseCountryType = c_char * TP_COUNTRY_LEN

class artistresult(Structure):
    '''This class is used to get/set the information for an artist lookup result. For details
       on how to use this class, please look up the main tunepimp documentation'''

    _fields_ = [
                ("relevance", c_int),
                ("name", artistNameType),
                ("sortName", artistNameType),
                ("id", idType)
               ]

class albumresult(Structure):
    '''This class is used to get/set the information for an album lookup result. For details
       on how to use this class, please look up the main tunepimp documentation'''

    _fields_ = [
                ("relevance", c_int),
                ("name", albumNameType),
                ("id", idType),
                ("numTracks", c_int),
                ("numCDIndexIds", c_int),
                ("isVA", c_int),
                ("isNA", c_int),
                ("status", c_int),
                ("type", c_int),
                ("releaseYear", c_int),
                ("releaseDay", c_int),
                ("releaseMonth", c_int),
                ("releaseCountry", releaseCountryType),
                ("artist", artistresult)
               ]

class albumtrackresult(Structure):
    '''This class is used to get/set the information for an album/track lookup result. For details
       on how to use this class, please look up the main tunepimp documentation'''

    _fields_ = [
                ("relevance", c_int),
                ("name", trackNameType),
                ("id", idType),
                ("numPUIDs", c_int),
                ("trackNum", c_int),
                ("duration", c_ulong),
                ("artist", artistresult),
                ("album", albumresult)
               ]


class track(object):
    '''This class is used to get/set the information for a track lookup result. For details
       on how to use this clase, please look up the main tunepimp documentation'''

    def __init__(self, tunePimp, tr):
        self.tunePimp = tunePimp
        self.tplib = tunePimp.tplib
        self.tr = c_void_p(tr)
        self.tplib.tr_GetStatus.argtypes = [ c_void_p ]
        self.tplib.tr_SetStatus.argtypes = [ c_void_p, c_int ]
        self.tplib.tr_GetSimilarity.argtypes = [ c_void_p ]
        self.tplib.tr_HasChanged.argtypes = [ c_void_p ]
        self.tplib.tr_Lock.argtypes = [ c_void_p ]
        self.tplib.tr_Unlock.argtypes = [ c_void_p ]

    def getTrackObject(self):
        return self.tr

    def getStatus(self):
        return self.tplib.tr_GetStatus(self.tr)

    def setStatus(self, status):
        self.tplib.tr_SetStatus(self.tr, status)

    def getFileName(self):
        fileName = c_buffer(TP_FILENAME_LEN)
        len = c_int(TP_FILENAME_LEN)
        self.tplib.tr_GetFileName(self.tr, fileName, len)
        return unicode(fileName.value, "UTF-8", 'replace')

    def getPUID(self):
        puid = c_buffer(TP_ID_LEN)
        len = c_int(TP_ID_LEN)
        self.tplib.tr_GetPUID(self.tr, puid, len)
        return unicode(puid.value, "UTF-8", 'replace')

    def getLocalMetadata(self):
        internal = metadata.metadataInternal()
        self.tplib.tr_GetLocalMetadata(self.tr, pointer(internal))
        mdata = metadata.metadata(self.tunePimp)
        internal.get(mdata)
        return mdata

    def setLocalMetadata(self, mdata):
        internal = metadata.metadataInternal()
        internal.set(mdata)
        self.tplib.tr_SetLocalMetadata(self.tr, pointer(internal))

    def getServerMetadata(self):
        internal = metadata.metadataInternal()
        self.tplib.tr_GetServerMetadata(self.tr, pointer(internal))
        mdata = metadata.metadata(self.tunePimp)
        internal.get(mdata)
        return mdata

    def setServerMetadata(self, mdata):
        internal = metadata.metadataInternal()
        internal.set(mdata)
        self.tplib.tr_SetServerMetadata(self.tr, pointer(internal))

    def getTrackError(self):
        err = c_buffer(TP_ERROR_LEN)
        len = c_int(TP_ERROR_LEN)
        self.tplib.tr_GetError(self.tr, err, len)
        return unicode(err.value, "UTF-8", 'replace')

    def getSimilarity(self):
        return self.tplib.tr_GetSimilarity(self.tr)

    def hasChanged(self):
        return self.tplib.tr_HasChanged(self.tr)

    def setChanged(self):
        self.tplib.tr_SetChanged(self.tr)

    def lock(self):
        self.tplib.tr_Lock(self.tr)

    def unlock(self):
        self.tplib.tr_Unlock(self.tr)
