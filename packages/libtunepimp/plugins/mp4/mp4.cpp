/*----------------------------------------------------------------------------

   libtunepimp -- The MusicBrainz tagging library.  
                  Let a thousand taggers bloom!
   
   Copyright (C) 2005 Lukas Lalinsky
   
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

   $Id: mp4.cpp 8497 2006-09-29 21:26:44Z luks $

----------------------------------------------------------------------------*/

#include <string.h>
#include <stdio.h>
#include <mp4.h>
#include "metadata.h"
#include "plugin.h"
#ifndef WIN32
#include "../../lib/utf8/utf8util.h"
#endif

using namespace std;

#ifndef WIN32
#define initPlugin mp4InitPlugin
#endif

#define PLUGIN_VERSION "1.0.0"
#define PLUGIN_NAME    "MP4 metadata reader/writer"

static char *formats[][2] = {
  { ".aac", "AAC/MP4" },
  { ".mp4", "MP4" },
  { ".m4a", "MP4" },
  { ".m4b", "MP4" },
  { ".m4p", "MP4" },
};

#define NUM_FORMATS 5

static char *errorString = "";

static void
mp4Shutdown()
{
  if (strlen(errorString))
    free(errorString);
}

static const char *
mp4GetVersion()
{
  return PLUGIN_VERSION;
}

static const char *
mp4GetName()
{
  return PLUGIN_NAME;
}

static int
mp4GetNumFormats(void)
{
  return NUM_FORMATS;
}

static int
mp4GetFormat(int i, char ext[TP_EXTENSION_LEN],
		char desc[TP_PLUGIN_DESC_LEN],int *functions)
{
  if (i < 0 || i >= NUM_FORMATS)
    return 0;
  
  strcpy(ext, formats[i][0]);
  strcpy(desc, formats[i][0]);
  *functions = TP_PLUGIN_FUNCTION_METADATA;

  return 1;
}

static const char *
mp4GetError()
{
  return errorString;
}

static int
mp4ReadMetadata(metadata_t *mdata, const char *fileName, int flags, const char *encoding)
{
  char *value;
  u_int16_t numval, numval2;
  u_int8_t numval3;
  u_int32_t size;
  MP4FileHandle mp4file;
  
#ifndef WIN32
  mp4file = MP4Read(utf8ToEncoding(fileName, encoding).c_str());
#else  
  mp4file = MP4Read(fileName);
#endif  

  if (mp4file == MP4_INVALID_FILE_HANDLE) 
    return 0;
 
  memset(mdata, 0, sizeof(metadata_t));
  
  if (MP4GetMetadataName(mp4file, &value) && value != NULL) {
    strcpy(mdata->track, value);
    free(value);
  }

  if (MP4GetMetadataArtist(mp4file, &value) && value != NULL) {
    strcpy(mdata->artist, value);
    free(value);
  }

  if (MP4GetMetadataYear(mp4file, &value) && value != NULL) {
    mdata->releaseYear = strtol(value, NULL, 0);
    free(value);
  }

  if (MP4GetMetadataAlbum(mp4file, &value) && value != NULL) {
    strcpy(mdata->album, value);
    free(value);
  }  
  
  if (MP4GetMetadataTrack(mp4file, &numval, &numval2)) {
    mdata->trackNum = numval;
    mdata->totalInSet = numval2;
  }

  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Sortname", (u_int8_t **)&value, &size) && value != NULL) {
    strcpy(mdata->sortName, value);
    free(value);
  }
  
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Track Id", (u_int8_t **)&value, &size) && value != NULL) {
    strcpy(mdata->trackId, value);
    free(value);
  }
  
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Album Id", (u_int8_t **)&value, &size) && value != NULL) {
    strcpy(mdata->albumId, value);
    free(value);
  }
  
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Artist Id", (u_int8_t **)&value, &size) && value != NULL) {
    strcpy(mdata->artistId, value);
    free(value);
  }

  if (MP4GetMetadataFreeForm(mp4file, "MusicIP PUID", (u_int8_t **)&value, &size) && value != NULL) {
    strcpy(mdata->filePUID, value);
    free(value);
  }
  
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Album Artist Id", (u_int8_t **)&value, &size) && value != NULL) {
    strcpy(mdata->albumArtistId, value);
    free(value);
  }
  
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Album Artist Sortname", (u_int8_t **)&value, &size) && value != NULL) {
    strcpy(mdata->albumArtistSortName, value);
    free(value);
  }
  
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Album Artist", (u_int8_t **)&value, &size) && value != NULL) {
    strcpy(mdata->albumArtist, value);
    free(value);
  }
  
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Album Type", (u_int8_t **)&value, &size) && value != NULL) {
    mdata->albumType = convertToAlbumType(value);
    free(value);
  }
    
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Album Status", (u_int8_t **)&value, &size) && value != NULL) {
    mdata->albumStatus = convertToAlbumStatus(value);
    free(value);
  }
    
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Album Release Date", (u_int8_t **)&value, &size) && value != NULL) {
    int year = 0, month = 0, day = 0;
    if (sscanf(value, "%04d-%02d-%02d", &year, &month, &day) > 0) {
      mdata->releaseYear  = year;
      mdata->releaseMonth = month;
      mdata->releaseDay   = day;
    }
    free(value);
  }
  
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Album Release Country", (u_int8_t **)&value, &size) && value != NULL) {
    strcpy(mdata->releaseCountry, value);
    free(value);
  }
  
  u_int32_t numTracks = MP4GetNumberOfTracks(mp4file);
  for (u_int32_t i = 0; i < numTracks; i++) {
    MP4TrackId trackId = MP4FindTrackId(mp4file, i);
    const char *trackType = MP4GetTrackType(mp4file, trackId);
    if (!strcmp(trackType, MP4_AUDIO_TRACK_TYPE)) {
      MP4Duration trackDuration = MP4GetTrackDuration(mp4file, trackId); 
      mdata->duration = (unsigned long)MP4ConvertFromTrackDuration(mp4file, trackId, trackDuration, MP4_MSECS_TIME_SCALE);    
    }
  }  

  if (MP4GetMetadataCompilation(mp4file, &numval3)) {
    mdata->variousArtist = numval3;
  }
  
  if (MP4GetMetadataFreeForm(mp4file, "MusicBrainz Non-Album", (u_int8_t **)&value, &size) && value != NULL) {
    mdata->nonAlbum = atoi(value);
    free(value);
  }
  
  strcpy(mdata->fileFormat, fileName + strlen(fileName) - 3); 
  
  if (!MP4Close(mp4file))
    return 0;
  
  return 1;
}

static int
mp4WriteMetadata(const metadata_t *mdata, const char *fileName, int flags,
		   const char *encoding)
{
  char temp[256];
  string temp2;
  MP4FileHandle mp4file;
  
#ifndef WIN32
  mp4file = MP4Modify(utf8ToEncoding(fileName, encoding).c_str());
#else  
  mp4file = MP4Modify(fileName);
#endif  

  if (mp4file == MP4_INVALID_FILE_HANDLE)
    return 0;

  if ((flags & TP_PLUGIN_FLAGS_GENERAL_CLEAR_TAGS) != 0)
    MP4MetadataDelete(mp4file);
  
  MP4SetMetadataName(mp4file, mdata->track);
  
  MP4SetMetadataArtist(mp4file, mdata->artist);
  
  sprintf(temp, "%04d", mdata->releaseYear);
  MP4SetMetadataYear(mp4file, temp);
  
  MP4SetMetadataAlbum(mp4file, mdata->album);
  
  MP4SetMetadataTrack(mp4file, mdata->trackNum, mdata->totalInSet);
  
  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Sortname", (u_int8_t *)mdata->sortName, strlen(mdata->sortName) + 1);
  
  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Track Id", (u_int8_t *)mdata->trackId, strlen(mdata->trackId) + 1);
  
  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Album Id", (u_int8_t *)mdata->albumId, strlen(mdata->albumId) + 1);
  
  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Artist Id", (u_int8_t *)mdata->artistId, strlen(mdata->artistId) + 1);

  MP4SetMetadataFreeForm(mp4file, "MusicIP PUID", (u_int8_t *)mdata->filePUID, strlen(mdata->filePUID) + 1);

  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Album Artist Id", (u_int8_t *)mdata->albumArtistId, strlen(mdata->albumArtistId) + 1);

  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Album Artist Sortname", (u_int8_t *)mdata->albumArtistSortName, strlen(mdata->albumArtistSortName) + 1);

  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Album Artist", (u_int8_t *)mdata->albumArtist, strlen(mdata->albumArtist) + 1);

  convertFromAlbumType(mdata->albumType, temp2);
  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Album Type", (u_int8_t *)temp2.c_str(), temp2.length() + 1);
  
  convertFromAlbumStatus(mdata->albumStatus, temp2);
  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Album Status", (u_int8_t *)temp2.c_str(), temp2.length() + 1);
  
  if (mdata->releaseYear > 0) {
    if (mdata->releaseMonth > 0) {
      if (mdata->releaseDay > 0) {
        sprintf(temp, "%04d-%02d-%02d", mdata->releaseYear, mdata->releaseMonth, mdata->releaseDay);
      }
      else {
        sprintf(temp, "%04d-%02d", mdata->releaseYear, mdata->releaseMonth);
      }
    }
    else { 
      sprintf(temp, "%04d", mdata->releaseYear);
    }
  }
  else {
    strcpy(temp, "");
  }
  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Album Release Date", (u_int8_t *)temp, strlen(temp) + 1);
  
  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Album Release Country", (u_int8_t *)mdata->releaseCountry, strlen(mdata->releaseCountry) + 1);

  MP4SetMetadataCompilation(mp4file, mdata->variousArtist ? 1 : 0);

  sprintf(temp, "%d", mdata->nonAlbum);  
  MP4SetMetadataFreeForm(mp4file, "MusicBrainz Non-Album", (u_int8_t *)temp, strlen(temp) + 1);
  
  if (!MP4Close(mp4file))
    return 0;

#ifndef WIN32
  if (!MP4Optimize(utf8ToEncoding(fileName, encoding).c_str()))
#else  
  if (!MP4Optimize(fileName))
#endif    
    return 0;
  
  return 1;
}

static unsigned long
mp4GetDuration(const char *fileName, int flags, const char *encoding)
{
  return 0;
}

static Plugin methods = {
  mp4Shutdown,
  mp4GetVersion,
  mp4GetName,
  mp4GetNumFormats,
  mp4GetFormat,
  mp4GetError,
  mp4ReadMetadata,
  mp4WriteMetadata,
  mp4GetDuration,
  NULL,
  NULL,
  NULL,
  NULL
};

extern "C" Plugin *
initPlugin()
{
  return &methods;
}

#ifdef WIN32

#include <sys/timeb.h>

extern "C" int
gettimeofday (struct timeval *t, void *foo)
{
	struct _timeb temp;
	_ftime(&temp);
	t->tv_sec = temp.time;
	t->tv_usec = temp.millitm * 1000;
	return (0);
}

#endif

