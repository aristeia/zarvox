/*----------------------------------------------------------------------------

   libtunepimp -- The MusicBrainz tagging library.  
                  Let a thousand taggers bloom!
   
   Copyright (C) Robert Kaye 2003
   
   This file is part of libtunepimp.

   libtunepimp is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

   libtunepimp is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with libtunepimp; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

   $Id: metadata.h 9816 2008-04-22 08:06:09Z luks $

----------------------------------------------------------------------------*/
#ifndef __METADATA_H__
#define __METADATA_H__

#include <string>
#include <cstring>
#include <cstdio>

#include "defs.h"
#include "tp_c.h"

struct Metadata
{
    std::string        artist;
    std::string        sortName;
    std::string        album;
    std::string        track;
    int           trackNum;
    int           totalInSet;
    bool          variousArtist;
    bool          nonAlbum;
    std::string        artistId;   
    std::string        albumId;   
    std::string        trackId;
    std::string        filePUID;
    std::string        albumArtistId;
    unsigned long duration;
    TPAlbumType   albumType;
    TPAlbumStatus albumStatus;
    std::string        fileFormat;
    int           releaseYear, releaseMonth, releaseDay;
    std::string        releaseCountry;

    // This is only used in case of PUID collision
    int           numPUIDIds;

    std::string        albumArtist;
    std::string        albumArtistSortName;
    
    Metadata(void) 
    { 
        trackNum = 0; 
        duration = 0; 
        variousArtist = false; 
        nonAlbum = false; 
        albumType = eAlbumType_Error;
        albumStatus = eAlbumStatus_Error;
        numPUIDIds = 0;
        releaseYear = releaseMonth = releaseDay = 0;
        totalInSet = 0;
    };

    ~Metadata(void) 
    {
    }

    Metadata &operator=(const Metadata &other)
    {
        artist = other.artist;
        sortName = other.sortName;
        album = other.album;
        track = other.track;
        trackNum = other.trackNum;
        trackId = other.trackId;
        artistId = other.artistId;
        albumId = other.albumId;
        filePUID = other.filePUID;
        duration = other.duration;
        variousArtist = other.variousArtist;
        nonAlbum = other.nonAlbum;
        albumArtistId = other.albumArtistId;
        albumType = other.albumType;
        albumStatus = other.albumStatus;
        fileFormat = other.fileFormat;
        numPUIDIds = other.numPUIDIds;
        releaseYear = other.releaseYear;
        releaseMonth = other.releaseMonth;
        releaseDay = other.releaseDay;
        releaseCountry = other.releaseCountry;
        totalInSet = other.totalInSet;
        albumArtist = other.albumArtist; 
        albumArtistSortName = other.albumArtistSortName; 

        return *this;
    };

    bool isEmpty(void)
    {
        return (artist.empty() && album.empty() && track.empty() &&
            trackNum == 0 && duration == 0 && filePUID.empty() &&
            artistId.empty() && albumId.empty() && albumId.empty() &&
            sortName.empty() && fileFormat.empty() &&
            albumArtist.empty() && albumArtistSortName.empty());
    }

    bool operator==(const Metadata &other)
    {
        if (artist == other.artist &&
            album == other.album &&
            track == other.track &&
            trackNum == other.trackNum &&
            trackId == other.trackId &&
            artistId == other.artistId &&
            albumId == other.albumId &&
            filePUID == other.filePUID &&
            duration == other.duration &&
            sortName == other.sortName &&
            albumArtistId == other.albumArtistId &&
            variousArtist == other.variousArtist &&
            nonAlbum == other.nonAlbum &&
            albumType == other.albumType &&
            albumStatus == other.albumStatus &&
            fileFormat == other.fileFormat &&
            releaseYear == other.releaseYear &&
            releaseDay == other.releaseDay &&
            releaseMonth == other.releaseMonth &&
            releaseCountry == other.releaseCountry &&
            totalInSet == other.totalInSet &&
            albumArtist == other.albumArtist &&
            albumArtistSortName == other.albumArtistSortName)
            return true;

        return false;
    };

    void clear(void)
    {
        artist = "";
        album = "";
        track = "";
        trackNum = 0;
        filePUID = "";
        duration = 0;
        artistId = "";
        trackId = "";
        albumId = "";
        sortName = "";
        albumArtistId = "";
        variousArtist = false;
        nonAlbum = false;
        albumType = eAlbumType_Error;
        albumStatus = eAlbumStatus_Error;
        fileFormat = "";
        numPUIDIds = 0;
        releaseYear = releaseMonth = releaseDay = 0;
        releaseCountry = "";
        totalInSet = 0;
        albumArtist = "";
        albumArtistSortName = "";
    }

    void readFromC(const metadata_t *mdata)
    {
        artist = mdata->artist;
        sortName = mdata->sortName;
        album = mdata->album;
        track = mdata->track;
        trackNum = mdata->trackNum;
        variousArtist = mdata->variousArtist;
        nonAlbum = mdata->nonAlbum;
        artistId = mdata->artistId;
        albumId = mdata->albumId;
        trackId = mdata->trackId;
        filePUID = mdata->filePUID;
        albumArtistId = mdata->albumArtistId;
        duration = mdata->duration;
        albumType = mdata->albumType;
        albumStatus = mdata->albumStatus;
        fileFormat = mdata->fileFormat;
        numPUIDIds = mdata->numPUIDIds;
        releaseYear = mdata->releaseYear;
        releaseMonth = mdata->releaseMonth;
        releaseDay = mdata->releaseDay;
        releaseCountry = mdata->releaseCountry;
        totalInSet = mdata->totalInSet;
        albumArtist = mdata->albumArtist;
        albumArtistSortName = mdata->albumArtistSortName;
    }

    void writeToC(metadata_t *mdata) const
    {
        memset(mdata, 0, sizeof(metadata_t));

        strncpy(mdata->artist, artist.c_str(), TP_ARTIST_NAME_LEN - 1);
        strncpy(mdata->sortName, sortName.c_str(), TP_ARTIST_NAME_LEN - 1);
        strncpy(mdata->album, album.c_str(), TP_ALBUM_NAME_LEN - 1);
        strncpy(mdata->track, track.c_str(), TP_TRACK_NAME_LEN - 1);
        mdata->trackNum = trackNum;
        mdata->variousArtist = (bool)variousArtist;
        mdata->nonAlbum = (bool)nonAlbum;
        strncpy(mdata->artistId, artistId.c_str(), TP_ID_LEN - 1);
        strncpy(mdata->albumId, albumId.c_str(), TP_ID_LEN - 1);
        strncpy(mdata->trackId, trackId.c_str(), TP_ID_LEN - 1);
        strncpy(mdata->filePUID, filePUID.c_str(), TP_ID_LEN - 1);
        strncpy(mdata->albumArtistId, albumArtistId.c_str(), TP_ID_LEN - 1);
        mdata->duration = duration;
        mdata->albumType = albumType;
        mdata->albumStatus = albumStatus;
        strncpy(mdata->fileFormat, fileFormat.c_str(), TP_FORMAT_LEN - 1);
        mdata->numPUIDIds = numPUIDIds;
        mdata->releaseYear = releaseYear;
        mdata->releaseMonth = releaseMonth;
        mdata->releaseDay = releaseDay;
        strncpy(mdata->releaseCountry, releaseCountry.c_str(), TP_COUNTRY_LEN - 1);
        mdata->totalInSet = totalInSet;
        strncpy(mdata->albumArtist, albumArtist.c_str(), TP_ARTIST_NAME_LEN - 1);
        strncpy(mdata->albumArtistSortName, albumArtistSortName.c_str(), TP_ARTIST_NAME_LEN - 1);
    }

    void print(void)
    {
        printf("artist: '%s'\n", artist.c_str());
        printf("sortName: '%s'\n", sortName.c_str());
        printf("album: '%s'\n", album.c_str());
        printf("track: '%s'\n", track.c_str());
        printf("trackNum: %d\n", trackNum);
        printf("totalInSet: %d\n", totalInSet);
        printf("duration: %lu\n", duration);
        printf("va: %i\n", variousArtist);
        printf("na: %i\n", nonAlbum);
        printf("artistId: '%s'\n", artistId.c_str());
        printf("albumId: '%s'\n", albumId.c_str());
        printf("trackId: '%s'\n", trackId.c_str());
        printf("filePUID: '%s'\n", filePUID.c_str());
        printf("albumArtistId: '%s'\n", albumArtistId.c_str());
        printf("albumArtist: '%s'\n", albumArtist.c_str());
        printf("albumArtistSortName: '%s'\n", albumArtistSortName.c_str());
        printf("albumType: %d\n", albumType);
        printf("albumStatus: %d\n", albumStatus);
        printf("format: '%s'\n", fileFormat.c_str());
        printf("releaseYear: %d\n", releaseYear);
        printf("releaseMonth: %d\n", releaseMonth);
        printf("releaseDay: %d\n", releaseDay);
        printf("releaseCountry: %s\n", releaseCountry.c_str());
    }
};

class MetadataCompare 
{
    public:

                 MetadataCompare(void) {};
        virtual ~MetadataCompare(void) {};

        int      compare(const Metadata &a, const Metadata &b) const;

    private:

        double   durationSim(int trackA, int trackB) const;
};

TPAlbumStatus convertToAlbumStatus  (const char *albumStatus);
TPAlbumType   convertToAlbumType    (const char *albumType);
void          convertFromAlbumStatus(TPAlbumStatus status, std::string &albumStatus);
void          convertFromAlbumType  (TPAlbumType type, std::string &albumType);

#endif
