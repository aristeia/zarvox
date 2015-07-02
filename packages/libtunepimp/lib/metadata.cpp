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

   $Id: metadata.cpp 9816 2008-04-22 08:06:09Z luks $

----------------------------------------------------------------------------*/
#include <math.h>
#include <stdio.h>
#include <cstdlib>
#include "metadata.h"
#include "../config.h"
using namespace std;

extern "C"
{
   #include "astrcmp.h"
}

const int numAlbumTypeStrings = 11;
const char *albumTypeStrings[] =
{
    "album", "single", "EP", "compilation", "soundtrack",
    "spokenword", "interview", "audiobook", "live", "remix", "other", "\0"
};

const int numAlbumStatusStrings = 3;
const char *albumStatusStrings[] =
{
    "official", "promotion", "bootleg", "\0"
};

TPAlbumType convertToAlbumType(const char *albumType)
{
    for(int i = 0;; i++)
    {
        if (albumTypeStrings[i][0] == 0)
            break;

        if (strlen(albumType) > 4 && strcasecmp(albumTypeStrings[i], albumType + 4) == 0)
            return (TPAlbumType)i;

        if (strcasecmp(albumTypeStrings[i], albumType) == 0)
            return (TPAlbumType)i;
    }
    return eAlbumType_Error;
}

void convertFromAlbumType(TPAlbumType type, string &albumType)
{
    if ((int)type >= 0 && (int)type < numAlbumTypeStrings)
        albumType = string(albumTypeStrings[(int)type]);
    else 
        albumType = "unknown";
}

TPAlbumStatus convertToAlbumStatus(const char *albumStatus)
{
    for(int i = 0;; i++)
    {
        if (albumStatusStrings[i][0] == 0)
            break;

        if (strlen(albumStatus) > 6 && strcasecmp(albumStatusStrings[i], albumStatus + 6) == 0)
            return (TPAlbumStatus)i;

        if (strcasecmp(albumStatusStrings[i], albumStatus) == 0)
            return (TPAlbumStatus)i;
    }
    return eAlbumStatus_Error;
}

void convertFromAlbumStatus(TPAlbumStatus status, string &albumStatus)
{
    if ((int)status >= 0 && (int)status < numAlbumStatusStrings)
        albumStatus = string(albumStatusStrings[(int)status]);
    else 
        albumStatus = "unknown";
}

const int numFlags = 6;
const int artistFlag =    0x01;
const int albumFlag =     0x02;
const int trackFlag =     0x04;
const int trackNumFlag =  0x08;
const int durationFlag =  0x10;
const int albumTypeFlag = 0x20;
const int lastFlag =      0x20; 

const int proportions[6] = 
{
    10, // artist     0x01
    9,  // album      0x02
    10, // track      0x04
    8,  // trackNum   0x08
    10,  // duration   0x10
    8,  // albumType  0x20
};

double MetadataCompare::durationSim(int trackA, int trackB) const
{
    int diff;

    diff = abs(trackA - trackB);
    if (diff > 30000)
       return 0;

    return 1.0 - ((double)diff / (double)30000);
}

int MetadataCompare::compare(const Metadata &a, const Metadata &b) const
{
    int index = 0, i;
    Metadata A = a, B = b;
    float weights[numFlags];

    // If one of the two is completely empty of meaningful info, just return 0
    if ((A.artist.empty() && A.album.empty() && A.track.empty()) ||
        (B.artist.empty() && B.album.empty() && B.track.empty()))
        return 0;

    if (!A.artist.empty() && !B.artist.empty())
        index |= artistFlag;

    // If one album is blank, and the other is an album, copy it over to favor it.
    //if (A.album.empty() && !B.album.empty() && B.albumType == eAlbumType_Album)
    //    A.album = B.album;

    // Now check the reverse case as well.
    //if (B.album.empty() && !A.album.empty() && A.albumType == eAlbumType_Album)
    //    B.album = A.album;

    if (!A.album.empty() && !B.album.empty())
        index |= albumFlag;

    if (!A.track.empty() && !B.track.empty())
        index |= trackFlag;

    if (A.trackNum != 0 && B.trackNum != 0)
        index |= trackNumFlag;

    if (A.duration != 0 && B.duration != 0)
        index |= durationFlag;

    if (A.albumType != eAlbumType_Error && B.albumType != eAlbumType_Error)
        index |= albumTypeFlag;

    if (index == 0)
        return 0;

    int total = 0;
    for(i = 0; i < numFlags; i++)
        if ((index & (1 << i)) != 0)
        {
            weights[i] = proportions[i];
            total += proportions[i];
        }
        else
            weights[i] = 0.0;

    for(i = 0; i < numFlags; i++)
        weights[i] /= (float)total;

    return (int)ceil(min(100.0, ((astrcmp(A.artist.c_str(), B.artist.c_str()) * weights[0]) +
                      (astrcmp(A.album.c_str(), B.album.c_str()) * weights[1]) +
                      (astrcmp(A.track.c_str(), B.track.c_str()) * weights[2]) +
                      (durationSim(A.duration, B.duration) * weights[3]) +
                      (((A.trackNum == B.trackNum) ? 1.0 : 0.0) * weights[4]) +  
                      (((A.albumType == B.albumType) ? 1.0 : 0.0) * weights[5])) * 100));
}
