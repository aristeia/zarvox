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

$Id: flac_meta.cpp 8716 2006-12-15 19:55:24Z luks $

----------------------------------------------------------------------------*/
  // ---------------------------------------------------------------------------
  // This code is based on vorbis.cpp and vorbis.cpp from FreeAmp. EMusic.com
  // has released this code into the Public Domain. 
  // (Thanks goes to Brett Thomas, VP Engineering Emusic.com)
  // ---------------------------------------------------------------------------
  // Portions (c) Copyright Kristian G. Kvilekval, and permission to use in
  // LGPL
  // library granted on February 25th, 2003

#ifdef WIN32
#       if _MSC_VER == 1200
#               pragma warning(disable:4786)
#       endif
#else
#       include <unistd.h>
#endif

#include <stdio.h>
#include <math.h>
#include <assert.h>
#include <string>
#include <locale.h>
#include <ctype.h>
#include <map>
#include <algorithm>

using namespace std;

#include <musicbrainz/mb_c.h>
#include "flac_meta.h"
#include <FLAC/metadata.h>
#include "../../lib/utf8/utf8.h"
#include "../../lib/utf8/utf8util.h"

#ifdef WIN32
#include "../../config_win32.h"
#endif

typedef   multimap < string, string > tagmap_t;

static    bool
add_comment(tagmap_t & tagmap,
            const string & tag, const string & val, bool singleton = true)
{
   if (val.size() == 0)
      return false;
   // case 1: when a singleton, erase all existing values.
   if (singleton)
      tagmap.erase(tag);

   tagmap.insert(pair < string, string > (tag, val));
   return true;
}

/** Find a value from in the tag table returning true when it exists 
 *  
 */
static    bool
get_comment(tagmap_t & tagmap, const string & tag, string & val)
{
   tagmap_t::iterator it;
   it = tagmap.find(tag);
   if (it != tagmap.end())
   {
      val = (*it).second;
      return true;
   }
   return false;
}

/** Load all tags from the comment structure into the given map. */
static void
load_tags(FLAC__StreamMetadata * metadata, tagmap_t & tagmap)
{
   string    entry;
   string    key;
   string    val;
   FLAC__StreamMetadata_VorbisComment *vc = &metadata->data.vorbis_comment;

   for (unsigned i = 0; i < vc->num_comments; i++)
   {
      entry.assign(reinterpret_cast < char *>(vc->comments[i].entry),
                   vc->comments[i].length);

      string::size_type sep = entry.find('=');
      key = entry.substr(0, sep);
      val = entry.substr(sep+1, string::npos);
      transform(key.begin(), key.end(), key.begin(), (int (*)(int)) &toupper);
      tagmap.insert(pair < string, string > (key, val));
   }
}

/** Save the tags in the map to the given comment structure.
 *  NOTE:  This will not enforce vorbis tag recommenation singleton
 * or values, so use with care 
 */
static void
save_tags(FLAC__StreamMetadata * metadata, tagmap_t & tagmap)
{

   string    comment;
   string    key, val;

   while(metadata->data.vorbis_comment.num_comments > 0)
      FLAC__metadata_object_vorbiscomment_delete_comment(metadata, 0);

   for (tagmap_t::iterator it = tagmap.begin(); it != tagmap.end(); it++)
   {
      key = (*it).first;
      val = (*it).second;
      transform(key.begin(),key.end(),key.begin(),(int(*)(int))&toupper);
      comment = key + '=' + val;

      FLAC__StreamMetadata_VorbisComment_Entry entry;

      entry.entry = (FLAC__byte *) comment.c_str();
      entry.length = comment.size();
      FLAC__metadata_object_vorbiscomment_insert_comment(metadata, 0, entry, true);
   }
}

bool
FLAC::read(const string & fileName, Metadata & metadata)
{
   char     *ptr;

   // We will support only id3-like tags.  For a more complete list see
   // http://reactor-core.org/ogg-tag-standard.html

   ptr = strrchr((char *)fileName.c_str(), '.');
   if (ptr == NULL)
      return false;

   if (strcmp(ptr, ".flac"))
      return false;

   FLAC__Metadata_SimpleIterator *it = FLAC__metadata_simple_iterator_new();

#ifndef WIN32
   if (!FLAC__metadata_simple_iterator_init(it, utf8ToEncoding(fileName, encoding).c_str(), true, false))
#else   
   if (!FLAC__metadata_simple_iterator_init(it, fileName.c_str(), true, false))
#endif   
      return false;

   FLAC__MetadataType blocktype;

   // Search looking for a comment block
   while (((blocktype = FLAC__metadata_simple_iterator_get_block_type(it)) !=
           FLAC__METADATA_TYPE_VORBIS_COMMENT) &&
          FLAC__metadata_simple_iterator_next(it)) ;

   if (blocktype != FLAC__METADATA_TYPE_VORBIS_COMMENT)
      return true;

   FLAC__StreamMetadata *md_block =
      FLAC__metadata_simple_iterator_get_block(it);

   tagmap_t  tagmap;
   string    val;

   load_tags(md_block, tagmap);

   if (get_comment(tagmap, "TITLE", val))
      metadata.track = string(val.c_str());
   if (get_comment(tagmap, "ARTIST", val))
      metadata.artist = string(val.c_str());
   if (get_comment(tagmap, "ALBUM", val)) 
      metadata.album = string(val.c_str());
   if (get_comment(tagmap, "TRACKNUMBER", val))
      metadata.trackNum = atoi(val.c_str());
   if (get_comment(tagmap, "TRACKTOTAL", val))
      metadata.totalInSet = atoi(val.c_str());
   if (get_comment(tagmap, "MUSICBRAINZ_TRACKID", val))
      metadata.trackId = string(val.c_str());
   if (get_comment(tagmap, "MUSICBRAINZ_ARTISTID", val))
      metadata.artistId = string(val.c_str());
   if (get_comment(tagmap, "MUSICBRAINZ_ALBUMID", val))
      metadata.albumId = string(val.c_str());
   if (get_comment(tagmap, "MUSICBRAINZ_ALBUMTYPE", val))
      metadata.albumType = convertToAlbumType(val.c_str());
   if (get_comment(tagmap, "MUSICBRAINZ_ALBUMSTATUS", val))
      metadata.albumStatus = convertToAlbumStatus(val.c_str());
   if (get_comment(tagmap, "MUSICBRAINZ_SORTNAME", val))
      metadata.sortName = string(val.c_str());
   if (get_comment(tagmap, "DATE", val))
   {
       int num, month, day, year;
   
       num = sscanf(val.c_str(), "%d-%d-%d", &year, &month, &day);
       if (num == 3)
       {
            metadata.releaseYear = year;
            metadata.releaseMonth = month;
            metadata.releaseDay = day;
       }
       if (num == 2)
       {
            metadata.releaseYear = year;
            metadata.releaseMonth = month;
            metadata.releaseDay = 0;
       }
       if (num == 1)
       {
            metadata.releaseYear = year;
            metadata.releaseMonth = 0;
            metadata.releaseDay = 0;
       }
   }
   if (get_comment(tagmap, "MUSICBRAINZ_ALBUMARTISTID", val))
   {
      metadata.variousArtist =
         strcasecmp(val.c_str(), MBI_VARIOUS_ARTIST_ID) == 0;
      metadata.albumArtistId = string(val.c_str());
      if (get_comment(tagmap, "MUSICBRAINZ_ALBUMARTIST", val))
          metadata.albumArtist = string(val.c_str());
      if (get_comment(tagmap, "MUSICBRAINZ_ALBUMARTISTSORTNAME", val))
          metadata.albumArtistSortName = string(val.c_str());
   }
   if (get_comment(tagmap, "MUSICIP_PUID", val))
      metadata.filePUID = string(val.c_str());
   if (get_comment(tagmap, "RELEASECOUNTRY", val))
      metadata.releaseCountry = string(val.c_str());
    if (get_comment(tagmap, "MUSICBRAINZ_NONALBUM", val))
        metadata.nonAlbum = atoi(val.c_str());
    if (get_comment(tagmap, "MUSICBRAINZ_VARIOUSARTISTS", val))
        metadata.variousArtist = atoi(val.c_str());

   metadata.fileFormat = "flac";

   FLAC__metadata_simple_iterator_delete(it);

   return true;
}

/** Write out FLAC metadata.    */
bool
FLAC::write(const string & fileName, const Metadata & metadata, bool clear)
{
   char  *ptr;
   char   dummy[20];
   string temp;

   // cout << "Called FLAC::write" << endl;
   // We will support only id3-like tags.  For a more complete list see
   // http://reactor-core.org/ogg-tag-standard.html

   ptr = strrchr((char *)fileName.c_str(), '.');
   if (ptr == NULL)
      return false;

   if (strcmp(ptr, ".flac"))
      return false;

   FLAC__Metadata_SimpleIterator *it = FLAC__metadata_simple_iterator_new();

#ifndef WIN32
   if (!FLAC__metadata_simple_iterator_init(it, utf8ToEncoding(fileName, encoding).c_str(), false, false))
#else   
   if (!FLAC__metadata_simple_iterator_init(it, fileName.c_str(), false, false))
#endif   
      return false;

   FLAC__MetadataType blocktype;

   // Search looking for a comment block
   while (((blocktype = FLAC__metadata_simple_iterator_get_block_type(it)) !=
           FLAC__METADATA_TYPE_VORBIS_COMMENT) &&
          FLAC__metadata_simple_iterator_next(it)) ;

   if (blocktype != FLAC__METADATA_TYPE_VORBIS_COMMENT)
      return true;

   FLAC__StreamMetadata *md_block =
      FLAC__metadata_simple_iterator_get_block(it);

   tagmap_t  tagmap;

   if (!clear)
      load_tags(md_block, tagmap);

   add_comment(tagmap, "TITLE", metadata.track.c_str());
   add_comment(tagmap, "ARTIST", metadata.artist.c_str());
   add_comment(tagmap, "ALBUM", metadata.album.c_str());
   add_comment(tagmap, "MUSICBRAINZ_SORTNAME", metadata.sortName.c_str());
   add_comment(tagmap, "MUSICBRAINZ_TRACKID", metadata.trackId.c_str());
   add_comment(tagmap, "MUSICBRAINZ_ALBUMID", metadata.albumId.c_str());
   if (metadata.albumType != eAlbumType_Error)
   {
       convertFromAlbumType(metadata.albumType, temp);
       add_comment(tagmap, "MUSICBRAINZ_ALBUMTYPE", temp.c_str());
   }
   if (metadata.albumStatus != eAlbumStatus_Error)
   {
       convertFromAlbumStatus(metadata.albumStatus, temp);
       add_comment(tagmap, "MUSICBRAINZ_ALBUMSTATUS", temp.c_str());
   }
   add_comment(tagmap, "MUSICBRAINZ_ARTISTID", metadata.artistId.c_str());
   add_comment(tagmap, "MUSICIP_PUID", metadata.filePUID.c_str());
   if (!metadata.albumArtistId.empty())
   {
        add_comment(tagmap, "MUSICBRAINZ_ALBUMARTISTID", metadata.albumArtistId.c_str());
        add_comment(tagmap, "MUSICBRAINZ_ALBUMARTIST", metadata.albumArtist.c_str());
        add_comment(tagmap, "MUSICBRAINZ_ALBUMARTISTSORTNAME", metadata.albumArtistSortName.c_str());
   }
   else if (metadata.variousArtist)
   {
        add_comment(tagmap, "MUSICBRAINZ_ALBUMARTISTID", 
                    MBI_VARIOUS_ARTIST_ID);
   }
   if (metadata.trackNum > 0)
   {
      sprintf(dummy, "%d", metadata.trackNum);
      add_comment(tagmap, "TRACKNUMBER", dummy);
   }
   if (metadata.totalInSet > 0)
   {
      sprintf(dummy, "%d", metadata.totalInSet);
      add_comment(tagmap, "TRACKTOTAL", dummy);
   }

   if (metadata.releaseYear > 0)
   {
       char temp[16];

       if (metadata.releaseMonth > 0 && metadata.releaseDay > 0)
           sprintf(temp, "%04d-%02d-%02d", metadata.releaseYear, metadata.releaseMonth, metadata.releaseDay);
       else if (metadata.releaseMonth > 0)
           sprintf(temp, "%04d-%02d", metadata.releaseYear, metadata.releaseMonth);
       else
           sprintf(temp, "%04d", metadata.releaseYear);
       add_comment(tagmap, "DATE", temp);
   }
   if (metadata.releaseCountry.length())
       add_comment(tagmap, "RELEASECOUNTRY", metadata.releaseCountry);

   sprintf(dummy, "%d", metadata.nonAlbum);
   add_comment(tagmap, "MUSICBRAINZ_NONALBUM", dummy);
    
   sprintf(dummy, "%d", metadata.variousArtist);
   add_comment(tagmap, "MUSICBRAINZ_VARIOUSARTISTS", dummy);
   
   save_tags(md_block, tagmap);
   bool      result = true;

   result = FLAC__metadata_simple_iterator_set_block(it, md_block, true);
   FLAC__metadata_simple_iterator_delete(it);

   return result;
}
