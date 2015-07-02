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

   $Id: wma.cpp 9816 2008-04-22 08:06:09Z luks $

----------------------------------------------------------------------------*/

#include <string.h>
#include <stdio.h>
#include <cstdlib>
#include <wmafile.h>
#include "metadata.h"
#include "plugin.h"
#ifndef WIN32
#include "../../lib/utf8/utf8util.h"
#endif

using namespace std;

#ifndef WIN32
#define initPlugin wmaInitPlugin
#endif

#define PLUGIN_VERSION "1.0.0"
#define PLUGIN_NAME    "WMA metadata reader/writer"

static char *formats[][2] = {
  { ".wma", "Windows Media Audio" },
  { ".asf", "ASF" },
};

#define NUM_FORMATS 2

static char *errorString = "";

static void
wmaShutdown()
{
  if (strlen(errorString))
    free(errorString);
}

static const char *
wmaGetVersion()
{
  return PLUGIN_VERSION;
}

static const char *
wmaGetName()
{
  return PLUGIN_NAME;
}

static int
wmaGetNumFormats(void)
{
  return NUM_FORMATS;
}

static int
wmaGetFormat(int i, char ext[TP_EXTENSION_LEN],
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
wmaGetError()
{
  return errorString;
}

static int
wmaReadMetadata(metadata_t *mdata, const char *fileName, int flags, const char *encoding)
{
  memset(mdata, 0, sizeof(metadata_t));

#ifndef WIN32
  TagLib::WMA::File f(utf8ToEncoding(fileName, encoding).c_str());
#else
  TagLib::WMA::File f(fileName);
#endif  

  if (f.isOpen() && f.isValid()) {
      
    TagLib::WMA::Tag *tag = f.WMATag();
    const TagLib::WMA::AttributeMap &attrMap = tag->attributeMap(); 

    strcpy(mdata->artist, tag->artist().to8Bit(true).c_str());
    strcpy(mdata->track, tag->title().to8Bit(true).c_str());
    strcpy(mdata->album, tag->album().to8Bit(true).c_str());
    mdata->trackNum = tag->track();
    mdata->releaseYear = tag->year();

    TagLib::AudioProperties *properties = f.audioProperties();
    if (properties)
      mdata->duration = properties->length() * 1000;
 
    if (attrMap.contains("MusicBrainz/TrackId")) 
      strcpy(mdata->trackId, attrMap["MusicBrainz/TrackId"].toString().toCString(true));   
    
    if (attrMap.contains("MusicIP/PUID")) 
      strcpy(mdata->filePUID, attrMap["MusicIP/PUID"].toString().toCString(true));   
    
    if (attrMap.contains("MusicBrainz/ArtistId")) 
      strcpy(mdata->artistId, attrMap["MusicBrainz/ArtistId"].toString().toCString(true));   
    
    if (attrMap.contains("MusicBrainz/AlbumId")) 
      strcpy(mdata->albumId, attrMap["MusicBrainz/AlbumId"].toString().toCString(true));   

    if (attrMap.contains("MusicBrainz/AlbumArtistId")) 
      strcpy(mdata->albumArtistId, attrMap["MusicBrainz/AlbumArtistId"].toString().toCString(true));

    if (attrMap.contains("MusicBrainz/AlbumArtist")) 
      strcpy(mdata->albumArtist, attrMap["MusicBrainz/AlbumArtist"].toString().toCString(true));

    if (attrMap.contains("MusicBrainz/AlbumArtistSortName")) 
      strcpy(mdata->albumArtistSortName, attrMap["MusicBrainz/AlbumArtistSortName"].toString().toCString(true));

    if (attrMap.contains("MusicBrainz/SortName")) 
      strcpy(mdata->sortName, attrMap["MusicBrainz/SortName"].toString().toCString(true));   

    if (attrMap.contains("MusicBrainz/AlbumType")) 
      mdata->albumType = convertToAlbumType(attrMap["MusicBrainz/AlbumType"].toString().toCString(true));

    if (attrMap.contains("MusicBrainz/AlbumStatus")) 
      mdata->albumStatus = convertToAlbumStatus(attrMap["MusicBrainz/AlbumStatus"].toString().toCString(true));

    if (attrMap.contains("MusicBrainz/AlbumReleaseCountry")) 
      strcpy(mdata->releaseCountry, attrMap["MusicBrainz/AlbumReleaseCountry"].toString().toCString(true));

    if (attrMap.contains("MusicBrainz/AlbumReleaseDate")) {
      int year = 0, month = 0, day = 0;
      if (sscanf(attrMap["MusicBrainz/AlbumReleaseDate"].toString().toCString(true), "%04d-%02d-%02d", &year, &month, &day) > 0) {
        mdata->releaseYear  = year;
        mdata->releaseMonth = month;
        mdata->releaseDay   = day;
      }
    }

    if (attrMap.contains("MusicBrainz/NonAlbum")) 
      mdata->nonAlbum = attrMap["MusicBrainz/NonAlbum"].toInt();   
    
    if (attrMap.contains("MusicBrainz/VariousArtists")) 
      mdata->variousArtist = attrMap["MusicBrainz/VariousArtists"].toInt();   
    
    if (attrMap.contains("MusicBrainz/TotalTracks")) 
      mdata->totalInSet = attrMap["MusicBrainz/TotalTracks"].toInt();   
    
    strcpy(mdata->fileFormat, fileName + strlen(fileName) - 3); 
  
    return 1;
  }
  
  return 0;
}

static int
wmaWriteMetadata(const metadata_t *mdata, const char *fileName, int flags,
		   const char *encoding)
{
  string temp;
  
#ifndef WIN32
  TagLib::WMA::File f(utf8ToEncoding(fileName, encoding).c_str());
#else
  TagLib::WMA::File f(fileName);
#endif  

  if (f.isOpen() && f.isValid()) {
      
    TagLib::WMA::Tag *tag = f.WMATag(); 
    
    tag->setArtist(TagLib::String(mdata->artist, TagLib::String::UTF8));
    tag->setAlbum(TagLib::String(mdata->album, TagLib::String::UTF8));
    tag->setTitle(TagLib::String(mdata->track, TagLib::String::UTF8));
    tag->setTrack(mdata->trackNum);
    tag->setYear(mdata->releaseYear);
    
    tag->setAttribute("MusicBrainz/TrackId", TagLib::String(mdata->trackId, TagLib::String::UTF8));
    tag->setAttribute("MusicIP/PUID", TagLib::String(mdata->filePUID, TagLib::String::UTF8));
    tag->setAttribute("MusicBrainz/ArtistId", TagLib::String(mdata->artistId, TagLib::String::UTF8));
    tag->setAttribute("MusicBrainz/AlbumId", TagLib::String(mdata->albumId, TagLib::String::UTF8));
    tag->setAttribute("MusicBrainz/SortName", TagLib::String(mdata->sortName, TagLib::String::UTF8));
    tag->setAttribute("MusicBrainz/AlbumArtistId", TagLib::String(mdata->albumArtistId, TagLib::String::UTF8));
    tag->setAttribute("MusicBrainz/AlbumArtist", TagLib::String(mdata->albumArtist, TagLib::String::UTF8));
    tag->setAttribute("MusicBrainz/AlbumArtistSortName", TagLib::String(mdata->albumArtistSortName, TagLib::String::UTF8));
    
    convertFromAlbumType(mdata->albumType, temp);
    tag->setAttribute("MusicBrainz/AlbumType", TagLib::String(temp, TagLib::String::UTF8));
    
    convertFromAlbumStatus(mdata->albumStatus, temp);
    tag->setAttribute("MusicBrainz/AlbumStatus", TagLib::String(temp, TagLib::String::UTF8));
    
    if (mdata->releaseYear > 0) {
      char temp[16];
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
      tag->setAttribute("MusicBrainz/AlbumReleaseDate", TagLib::String(temp, TagLib::String::UTF8));
    }
    
    tag->setAttribute("MusicBrainz/AlbumReleaseCountry", TagLib::String(mdata->releaseCountry, TagLib::String::UTF8));

    tag->setAttribute("MusicBrainz/NonAlbum",
                      TagLib::WMA::Attribute("MusicBrainz/NonAlbum", mdata->nonAlbum == 1));
    
    tag->setAttribute("MusicBrainz/VariousArtists",
                      TagLib::WMA::Attribute("MusicBrainz/VariousArtists", mdata->variousArtist == 1));

    tag->setAttribute("MusicBrainz/TotalTracks", TagLib::String::number(mdata->totalInSet));

    return f.save() ? 1 : 0;
  }
  
  return 0;
}

static unsigned long
wmaGetDuration(const char *fileName, int flags, const char *encoding)
{
  return 0;
}

static Plugin methods = {
  wmaShutdown,
  wmaGetVersion,
  wmaGetName,
  wmaGetNumFormats,
  wmaGetFormat,
  wmaGetError,
  wmaReadMetadata,
  wmaWriteMetadata,
  wmaGetDuration,
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


