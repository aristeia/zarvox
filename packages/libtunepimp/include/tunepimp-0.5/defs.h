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

   $Id: defs.h 7216 2006-04-14 23:10:49Z robert $

----------------------------------------------------------------------------*/
#ifndef DEFS_H
#define DEFS_H

typedef enum 
{
    tpOk,
    tpTooManyPUIDs,
    tpNoUserInfo,
    tpLookupError,
    tpSubmitError,
    tpInvalidIndex,
    tpInvalidObject,

    tpErrorLast
} TPError;

typedef enum 
{
    tpFileAdded,
    tpFileChanged,
    tpFileRemoved,
    tpWriteTagsComplete,

    tpCallbackLast
} TPCallbackEnum;

typedef enum 
{
    eMetadataRead = 0,     // pending metadata read
    ePending = 1,          // pending puid calculation
    eUnrecognized = 2,     // unrecognized
    eRecognized = 3,       // Recognized and previously saved
    ePUIDLookup = 4,        // puid done, pending puid lookup
    ePUIDCollision = 5,     // puid done, pending puid lookup
    eFileLookup = 6,       // puid done, no matches, pending file lookup
    eUserSelection = 7,    // file lookup done, needs user selection
    eVerified = 8,         // User verified, about to write changes to disk 
    eSaved = 9,            // File was saved
    eDeleted = 10,          // to be deleted, waiting for refcount == 0
    eError = 11,            // Error

    eLastStatus = 12       // Just a placeholder -- don't delete
} TPFileStatus;

typedef enum
{
    eNone,
    eArtistList,
    eAlbumList,
    eTrackList,
    eMatchedTrack
} TPResultType;

typedef enum 
{
    eAlbumType_Album        = 0,
    eAlbumType_Single       = 1,
    eAlbumType_EP           = 2,
    eAlbumType_Compilation  = 3,
    eAlbumType_Soundtrack   = 4,
    eAlbumType_Spokenword   = 5,
    eAlbumType_Interview    = 6,
    eAlbumType_Audiobook    = 7,
    eAlbumType_Live         = 8,
    eAlbumType_Remix        = 9,
    eAlbumType_Other        = 10,
    eAlbumType_Error        = 11
} TPAlbumType;


typedef enum 
{
    eAlbumStatus_Official,
    eAlbumStatus_Promotion,
    eAlbumStatus_Bootleg,
    eAlbumStatus_Error
} TPAlbumStatus;

typedef enum
{
    eLatin1,
    eUTF8,
    eUTF16,
    eEncodingError
} TPID3Encoding;

typedef enum 
{
    eIdle = 0,
    eLowest = 1,
    eLow = 2,
    eNormal = 3,
    eHigh = 4,
    eHigher = 5,
    eTimeCritical = 6
} TPThreadPriorityEnum;


/* Thread definitions */
#define TP_THREAD_NONE        0x0000
#define TP_THREAD_LOOKUPPUID   0x0001
#define TP_THREAD_LOOKUPFILE  0x0002
#define TP_THREAD_WRITE       0x0004
#define TP_THREAD_READ        0x0008
#define TP_THREAD_ANALYZER    0x0010
#define TP_THREAD_ALL         0xFFFF


#define TP_NONALBUMTRACKS_NAME "[non-album tracks]"

#endif
