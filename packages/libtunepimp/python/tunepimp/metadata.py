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
#   $Id: metadata.py 7216 2006-04-14 23:10:49Z robert $
#
#---------------------------------------------------------------------------

from ctypes import *

class metadataInternal(Structure):
    '''This class is used to get/set UTF-8 data from/to libtunepimp. Don't use this class directly!'''

    TP_ARTIST_NAME_LEN = 255
    TP_ALBUM_NAME_LEN = 255
    TP_TRACK_NAME_LEN = 255
    TP_ID_LEN = 40
    TP_FORMAT_LEN = 32
    TP_COUNTRY_LEN = 3
    TP_STATUS_LEN = 32
    TP_TYPE_LEN = 32

    artistNameType = c_char * TP_ARTIST_NAME_LEN
    albumNameType = c_char * TP_ALBUM_NAME_LEN
    trackNameType = c_char * TP_TRACK_NAME_LEN
    idType = c_char * TP_ID_LEN
    fileFormatType = c_char * TP_FORMAT_LEN
    releaseCountryType = c_char * TP_COUNTRY_LEN

    _fields_ = [
                ("artist", artistNameType),
                ("sortName", artistNameType),
                ("album", albumNameType),
                ("track", trackNameType),
                ("trackNum", c_int),
                ("totalInSet", c_int),
                ("variousArtist", c_int),
                ("nonAlbum", c_int),
                ("artistId", idType),
                ("albumId", idType),
                ("trackId", idType),
                ("filePUID", idType),
                ("albumArtistId", idType),
                ("duration", c_ulong),
                ("albumType", c_int),
                ("albumStatus", c_int),
                ("fileFormat", fileFormatType),
                ("releaseYear", c_int),
                ("releaseDay", c_int),
                ("releaseMonth", c_int),
                ("releaseCountry", releaseCountryType),
                ("numPUIDs", c_int),
                ("albumArtist", artistNameType),
                ("albumArtistSortName", artistNameType)
               ]
    def __init__(self):
        pass

    def set(self, mdata):
        self.artist = mdata.artist.encode('utf-8', 'replace')
        self.sortName = mdata.sortName.encode('utf-8', 'replace')
        self.album = mdata.album.encode('utf-8', 'replace')
        self.track = mdata.track.encode('utf-8', 'replace')
        self.trackNum = mdata.trackNum
        self.totalInSet = mdata.totalInSet
        self.variousArtist = mdata.variousArtist
        self.nonAlbum = mdata.nonAlbum
        self.artistId = mdata.artistId.encode('utf-8', 'replace')
        self.albumId = mdata.albumId.encode('utf-8', 'replace')
        self.trackId = mdata.trackId.encode('utf-8', 'replace')
        self.filePUID = mdata.filePUID.encode('utf-8', 'replace')
        self.albumArtistId = mdata.albumArtistId.encode('utf-8', 'replace')
        self.duration = mdata.duration
        self.albumType = mdata.albumType
        self.albumStatus = mdata.albumStatus
        self.fileFormat = mdata.fileFormat.encode('utf-8', 'replace')
        self.releaseYear = mdata.releaseYear
        self.releaseDay = mdata.releaseDay
        self.releaseMonth = mdata.releaseMonth
        self.releaseCountry = mdata.releaseCountry.encode('utf-8', 'replace')
        self.albumArtist = mdata.albumArtist.encode('utf-8', 'replace')
        self.albumArtistSortName = mdata.albumArtistSortName.encode('utf-8', 'replace')
        
    def get(self, mdata):
        mdata.artist = unicode(self.artist, "utf-8", 'replace')
        mdata.sortName = unicode(self.sortName, "utf-8", 'replace')
        mdata.album = unicode(self.album, "utf-8", 'replace')
        mdata.track = unicode(self.track, "utf-8", 'replace')
        mdata.trackNum = self.trackNum
        mdata.totalInSet = self.totalInSet
        mdata.variousArtist = self.variousArtist
        mdata.nonAlbum = self.nonAlbum
        mdata.artistId = unicode(self.artistId, "utf-8", 'replace')
        mdata.albumId = unicode(self.albumId, "utf-8", 'replace')
        mdata.trackId = unicode(self.trackId, "utf-8", 'replace')
        mdata.filePUID = unicode(self.filePUID, "utf-8", 'replace')
        mdata.albumArtistId = unicode(self.albumArtistId, "utf-8", 'replace')
        mdata.duration = self.duration
        mdata.albumType = self.albumType
        mdata.albumStatus = self.albumStatus
        mdata.fileFormat = unicode(self.fileFormat, "utf-8", 'replace')
        mdata.releaseYear = self.releaseYear
        mdata.releaseDay = self.releaseDay
        mdata.releaseMonth = self.releaseMonth
        mdata.releaseCountry = unicode(self.releaseCountry, "utf-8", 'replace')
        mdata.albumArtist = unicode(self.albumArtist, "utf-8", 'replace')
        mdata.albumArtistSortName = unicode(self.albumArtistSortName, "utf-8", 'replace')

class metadata(object):
    '''This class is used to get/set the metadata for a track inside tunepimp. For details
       on how to use this class, please look up the main tunepimp documentation'''


    def __init__(self, tunePimp):
        self.tplib = tunePimp.tplib
        self.tplib.md_ConvertToAlbumStatus.argtypes = [ c_char_p ]
        self.tplib.md_ConvertToAlbumType.argtypes = [ c_char_p ]
        self.tplib.md_Similarity.argtypes = [ c_char_p, c_char_p ]
        self.tplib.md_Similarity.restype = c_float 

        self.artist = u''
        self.sortName = u''
        self.album = u''
        self.track = u''
        self.trackNum = 0
        self.totalInSet = 0
        self.variousArtist = 0
        self.nonAlbum = 0
        self.artistId = u''
        self.albumId = u''
        self.trackId = u''
        self.filePUID = u''
        self.albumArtistId = u''
        self.duration = 0
        self.albumType = 0
        self.albumStatus = 0
        self.fileFormat = u''
        self.releaseYear = 0
        self.releaseDay = 0
        self.releaseMonth = 0
        self.releaseCountry = u''
        self.albumArtist = u''
        self.albumArtistSortName = u''

    def clear(self):
        internal = metadataInternal()
        internal.get(self)
        self.tplib.md_Clear(byref(internal))
        internal.set(self)

    def compare(self, other):
        internal = metadataInternal()
        internal.set(self)
        otherInternal = metadataInternal()
        otherInternal.set(other)
        return self.tplib.md_Compare(byref(internal), byref(otherInternal))

    def convertToAlbumStatus(self, statusStr):
        return self.tplib.md_ConvertToAlbumStatus(statusStr)

    def convertToAlbumType(self, typeStr):
        return self.tplib.md_ConvertToAlbumType(typeStr)

    def convertFromAlbumStatus(self, status):
        text = c_buffer(self.TP_STATUS_LEN)
        len = c_int(self.TP_STATUS_LEN)
        self.tplib.md_ConvertFromAlbumStatus(status, text, len)
        return text.value

    def convertFromAlbumType(self, type):
        text = c_buffer(self.TP_TYPE_LEN)
        len = c_int(self.TP_TYPE_LEN)
        self.tplib.md_ConvertFromAlbumType(type, text, len)
        return text.value

    def similarity(self, a, b):
        au = a.encode('utf-8', 'replace')
        bu = b.encode('utf-8', 'replace')
        return self.tplib.md_Similarity(au, bu)
