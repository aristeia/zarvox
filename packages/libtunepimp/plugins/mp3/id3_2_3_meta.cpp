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

   $Id: id3_2_3_meta.cpp 9816 2008-04-22 08:06:09Z luks $

----------------------------------------------------------------------------*/

#include <stdio.h>
#include <cstdlib>
#include <assert.h>
#include <ctype.h>
#include <musicbrainz/mb_c.h>
#include "mp3.h"
#include "id3_2_3_meta.h"
#include "id3tag/id3tag.h"

const int iDataFieldLen = 255;

//---------------------------------------------------------------------------

ID3_2_3::ID3_2_3(bool writeV1, ID3_Encoding enc, const string &encoding) : MetadataPlugin()
{
    this->writeV1 = writeV1;
    this->enc = enc;
    this->encoding = encoding;
    switch(enc)
    {
        case idUTF16:
            this->id3Encoding = ID3_2_3_FIELD_TEXTENCODING_UTF_16;
            break;
        default:
            this->id3Encoding = ID3_2_3_FIELD_TEXTENCODING_ISO_8859_1;
            break;
    }
}

//---------------------------------------------------------------------------

string ID3_2_3::getText(struct id3_2_3_tag *tag, const char *frameName)
{
    struct              id3_2_3_frame *frame;
    union               id3_2_3_field *field;
    int                 i;
    const id3_2_3_ucs4_t   *unicode;
    string              ret;

    frame = id3_2_3_tag_findframe(tag, frameName, 0);
    if (!frame)
        return ret;

    for(i = 0;; i++)
    {
        field = id3_2_3_frame_field(frame, i);
        if (!field)
            break;

        if (id3_2_3_field_type(field) == ID3_2_3_FIELD_TYPE_STRINGLIST)
        {
            unicode = id3_2_3_field_getstrings(field, 0);
            if (unicode)
            {
                id3_utf8_t *str;
                str = id3_ucs4_utf8duplicate(unicode);
                ret = string((char *)str);
                free(str);
            }
        }
    }

    return ret;
}

//---------------------------------------------------------------------------

string ID3_2_3::getUserText(struct id3_2_3_tag *tag, const char *userTextName)
{
    struct                id3_2_3_frame *frame;
    union                 id3_2_3_field *field;
    int                   i;
    id3_2_3_latin1_t     *str;
    const id3_2_3_ucs4_t *unicode;
    string                ret;

    for(i = 0;; i++)
    {
        frame = id3_2_3_tag_findframe(tag, "TXXX", i);
        if (!frame)
            return ret;

        field = id3_2_3_frame_field(frame, 1);
        if (!field)
            continue; 

        unicode = id3_2_3_field_getstring(field);
        if (unicode)
        {
            str = (id3_2_3_latin1_t *)id3_2_3_ucs4_latin1duplicate(unicode);
            if (strcmp((const char *)str, userTextName) == 0)
            {
                 field = id3_2_3_frame_field(frame, 2);
                 if (!field)
                     continue; 

                 unicode = id3_2_3_field_getstring(field);
                 if (unicode)
                 {
                     id3_utf8_t *ustr;
                     ustr = id3_ucs4_utf8duplicate(unicode);
                     ret = string((const char *)ustr);
                     free(ustr);
                     return ret;
                 }
            }
            free(str);
            continue;
        }
    }
}

//---------------------------------------------------------------------------

string ID3_2_3::getUniqueFileId(struct id3_2_3_tag *tag, const char *ufidName)
{
    struct              id3_2_3_frame *frame;
    union               id3_2_3_field *field;
    int                 i;
    const id3_2_3_latin1_t *text;
    string              ret;

    for(i = 0;; i++)
    {
        frame = id3_2_3_tag_findframe(tag, "UFID", i);
        if (!frame)
            return ret;

        field = id3_2_3_frame_field(frame, 0);
        if (!field)
            continue;

        text = id3_2_3_field_getlatin1(field);
        if (text)
        {
            if (strcmp((const char *)text, ufidName) == 0)
            {
                field = id3_2_3_frame_field(frame, 1);
                if (field)
                {
                    char *temp, *ptr;
                    id3_2_3_length_t len;

                    ptr = (char *)id3_2_3_field_getbinarydata(field, &len);
                    temp = new char[len + 1];
                    memcpy(temp, ptr, len);
                    temp[len] = 0;

                    ret = temp;

                    return ret;
                }
            }
            continue;
        }
    }

    return ret;
}

//---------------------------------------------------------------------------

bool ID3_2_3::setText(struct id3_2_3_tag *tag, const char *frameName, const string &text)
{
    struct id3_2_3_frame *frame;
    union  id3_2_3_field *field, *encField;
    id3_2_3_ucs4_t       *unicode;

    frame = id3_2_3_tag_findframe(tag, frameName, 0);
    if (!frame)
    {
        frame = id3_2_3_frame_new(frameName);
        id3_2_3_tag_attachframe(tag, frame);
    }
    if (frame)
    {
         field = id3_2_3_frame_field(frame, 1);
         if (field)
         {
             // Get the text encoding field
             encField = id3_2_3_frame_field(frame, 0);
             if (!encField)
                 return false;

             id3_2_3_field_settextencoding(encField, id3Encoding);

             unicode = id3_utf8_ucs4duplicate((id3_utf8_t *)text.c_str());
             id3_2_3_field_setstrings(field, 1, &unicode);
             free(unicode);

             return true;
         }
    }

    frame = id3_2_3_frame_new(frameName);

    // Get the text encoding field
    field = id3_2_3_frame_field(frame, 0);
    if (!field)
        return false;

    id3_2_3_field_settextencoding(field, id3Encoding);

    field = id3_2_3_frame_field(frame, 1);
    if (!field)
        return false;

    unicode = id3_utf8_ucs4duplicate((id3_utf8_t *)text.c_str());
    id3_2_3_field_setstrings(field, 1, &unicode);
    free((void *)unicode);

    id3_2_3_tag_attachframe(tag, frame);

    return true;
}

//---------------------------------------------------------------------------

bool ID3_2_3::setUserText(struct id3_2_3_tag *tag, const char *userTextName, const string &text)
{
    struct              id3_2_3_frame *frame;
    union               id3_2_3_field *field;
    int                 i;
    const id3_2_3_ucs4_t   *unicode;

    for(i = 0;; i++)
    {
        frame = id3_2_3_tag_findframe(tag, "TXXX", i);
        if (!frame)
            break;

        // Get the text encoding field
        field = id3_2_3_frame_field(frame, 0);
        if (!field)
            return false;

        id3_2_3_field_settextencoding(field, id3Encoding);

        field = id3_2_3_frame_field(frame, 1);
        if (!field)
            continue; 

        unicode = id3_2_3_field_getstring(field);
        if (unicode)
        {
            id3_2_3_latin1_t *str;

            str = id3_ucs4_latin1duplicate(unicode);
            if (strcmp((const char *)str, userTextName) == 0)
            {
                 free(str);

                 field = id3_2_3_frame_field(frame, 2);
                 if (!field)
                     continue; 

                 unicode = id3_utf8_ucs4duplicate((id3_utf8_t *)text.c_str());
                 id3_2_3_field_setstring(field, unicode);
                 free((void *)unicode);
                 return true;
            }
            free(str);
            continue;
        }
    }

    frame = id3_2_3_frame_new("TXXX");

    field = id3_2_3_frame_field(frame, 0);
    if (!field)
        return false;

    id3_2_3_field_settextencoding(field, id3Encoding);

    field = id3_2_3_frame_field(frame, 1);
    if (!field)
        return false;

    unicode = id3_utf8_ucs4duplicate((id3_utf8_t *)userTextName);
    id3_2_3_field_setstring(field, unicode);
    free((void *)unicode);

    field = id3_2_3_frame_field(frame, 2);
    if (!field)
        return false;

    unicode = id3_utf8_ucs4duplicate((id3_utf8_t *)text.c_str());
    id3_2_3_field_setstring(field, unicode);
    free((void *)unicode);
    
    id3_2_3_tag_attachframe(tag, frame);

    return true;
}

//---------------------------------------------------------------------------

bool ID3_2_3::setUniqueFileId(struct id3_2_3_tag *tag, const char *ufidName, const string &id)
{
    struct              id3_2_3_frame *frame;
    union               id3_2_3_field *field;
    int                 i;
    const id3_2_3_latin1_t *text;
    string              ret;

    for(i = 0;; i++)
    {
        frame = id3_2_3_tag_findframe(tag, "UFID", i);
        if (!frame)
            break;

        field = id3_2_3_frame_field(frame, 0);
        if (!field)
            continue;

        text = id3_2_3_field_getlatin1(field);
        if (text)
        {
            if (strcmp((const char *)text, ufidName) == 0)
            {
                field = id3_2_3_frame_field(frame, 1);
                if (field)
                {
                    id3_2_3_field_setbinarydata(field, (const id3_2_3_byte_t *)id.c_str(), 
                                            id.size());
                    return true;
                }
            }
            continue;
        }
    }

    frame = id3_2_3_frame_new("UFID");

    field = id3_2_3_frame_field(frame, 0);
    if (!field)
        return false;

    id3_2_3_field_setlatin1(field, (id3_2_3_latin1_t*)ufidName);

    field = id3_2_3_frame_field(frame, 1);
    if (!field)
        return false;

    id3_2_3_field_setbinarydata(field, (const id3_2_3_byte_t*)id.c_str(), id.size());
    id3_2_3_tag_attachframe(tag, frame);

    return true;
}

// Check ID3v1 support
bool ID3_2_3::read(const string &fileName, Metadata &data)
{
    struct        id3_2_3_file *file;
    struct        id3_2_3_tag *tag;
    string        temp;

    file = id3_2_3_file_open(fileName.c_str(), ID3_2_3_FILE_MODE_READONLY, encoding.c_str());
    if (file == NULL)
        return false;

    tag = id3_2_3_file_tag(file);
    if (tag == NULL)
    {
        id3_2_3_file_close(file);
        return false;
    }

    data.artist = getText(tag, ID3_2_3_FRAME_ARTIST);
    data.album = getText(tag, ID3_2_3_FRAME_ALBUM);
    data.track = getText(tag, ID3_2_3_FRAME_TITLE);
    data.trackNum = data.totalInSet = 0;
    sscanf(getText(tag, ID3_FRAME_TRACK).c_str(), "%d/%d", &data.trackNum, &data.totalInSet);

    data.sortName = getText(tag, "XSOP");
    if (data.sortName.empty())
       data.sortName = getUserText(tag, "MusicBrainz Artist Sortname");

    data.filePUID = getUserText(tag, "MusicIP PUID");
    data.artistId = getUserText(tag, "MusicBrainz Artist Id");
    data.albumId = getUserText(tag, "MusicBrainz Album Id");
    data.albumArtistId = getUserText(tag, "MusicBrainz Album Artist Id");
    data.albumArtist= getUserText(tag, "MusicBrainz Album Artist");
    data.albumArtistSortName = getUserText(tag, "MusicBrainz Album Artist Sortname");
    data.trackId = getUniqueFileId(tag, "http://musicbrainz.org");
    temp = getUserText(tag, "MusicBrainz Album Type");
    if (temp.length() > 0)
       data.albumType = convertToAlbumType(temp.c_str());
    temp = getUserText(tag, "MusicBrainz Album Status");
    if (temp.length() > 0)
       data.albumStatus = convertToAlbumStatus(temp.c_str());
    data.variousArtist = atoi(getText(tag, "TCMP").c_str());
    data.nonAlbum = atoi(getUserText(tag, "MusicBrainz Non-Album").c_str());
    data.fileFormat = "mp3";

    temp = getText(tag, "TORY");
    if (temp.length())
        data.releaseYear = atoi(temp.c_str());

    temp = getText(tag, "TYER");
    if (temp.length() && (data.releaseYear < 1800 || data.releaseYear > 3000))
        data.releaseYear = atoi(temp.c_str());

    temp = getText(tag, "XDOR");
    if (temp.length())
    {
        int year, month, day;

        year = month = day = 0;
        if (sscanf(temp.c_str(), "%04d-%02d-%02d", &year, &month, &day) > 0)
        {
            data.releaseYear = year;
            data.releaseMonth = month;
            data.releaseDay = day;
        }
    }
    data.releaseCountry = getUserText(tag, "MusicBrainz Album Release Country");

    id3_2_3_file_close(file);

    return true;
}

//---------------------------------------------------------------------------

bool ID3_2_3::write(const string  &fileName,
                const Metadata    &data,
                bool               clear)
{
    struct        id3_2_3_file *file;
    struct        id3_2_3_tag *tag;
    char          temp[20];
    int           ret;
    string        temp2;

    file = id3_2_3_file_open(fileName.c_str(), ID3_2_3_FILE_MODE_READWRITE, encoding.c_str());
    if (file == NULL)
    {
        errString = "Could not open track to write new metadata";
        return false;
    }

    tag = id3_2_3_file_tag(file);
    if (tag == NULL)
    {
        errString = "Could not open track to write new metadata";
        id3_2_3_file_close(file);
        return false;
    }

    if (clear)
        id3_2_3_tag_clearframes(tag);

    setText(tag, ID3_2_3_FRAME_ARTIST, data.artist);
    setText(tag, ID3_2_3_FRAME_ALBUM, data.album);
    setText(tag, ID3_2_3_FRAME_TITLE, data.track);

    /* If we read a position in set value, be careful to write it back out */
    if (data.totalInSet > 0)
        sprintf(temp, "%d/%d", data.trackNum, data.totalInSet);
    else
        sprintf(temp, "%d", data.trackNum);
    setText(tag, ID3_2_3_FRAME_TRACK, string(temp));

    if (!data.sortName.empty())
        setText(tag, "XSOP", data.sortName);

    /* Non-standard "Part of compilation" frame for iTunes */
    if (data.variousArtist) 
        setText(tag, "TCMP", "1");
    else    
        setText(tag, "TCMP", "0");
        
    setUserText(tag, "MusicIP PUID", data.filePUID);
    setUserText(tag, "MusicBrainz Artist Id", data.artistId);
    setUserText(tag, "MusicBrainz Album Id", data.albumId);
    if (data.albumType != eAlbumType_Error)
    {
        convertFromAlbumType(data.albumType, temp2);
        setUserText(tag, "MusicBrainz Album Type", temp2);
    }
    if (data.albumStatus != eAlbumStatus_Error)
    {
        convertFromAlbumStatus(data.albumStatus, temp2);
        setUserText(tag, "MusicBrainz Album Status", temp2);
    }
    if (!data.albumArtistId.empty())
    {
        setUserText(tag, "MusicBrainz Album Artist Id", data.albumArtistId.c_str());
        setUserText(tag, "MusicBrainz Album Artist", data.albumArtist.c_str());
        setUserText(tag, "MusicBrainz Album Artist Sortname", data.albumArtistSortName.c_str());
    }
    else if (data.variousArtist)
    {
        setUserText(tag, "MusicBrainz Album Artist Id", MBI_VARIOUS_ARTIST_ID);
    }
    setUniqueFileId(tag, "http://musicbrainz.org", data.trackId);

    if (data.releaseYear > 0)
    {
        char temp[16];
    
        sprintf(temp, "%02d", data.releaseYear);
        if (data.releaseMonth > 0)
        {
            sprintf(temp + strlen(temp), "-%02d", data.releaseMonth);
            if (data.releaseDay > 0)
                sprintf(temp + strlen(temp), "-%02d", data.releaseDay);
        }
        setText(tag, "XDOR", temp);
    }
    if (data.releaseYear > 0)
    {
        char temp[16];
    
        sprintf(temp, "%d", data.releaseYear);
        setText(tag, "TORY", temp);
        setText(tag, "TYER", temp);
    }
    if (data.releaseCountry.length() > 0)
        setUserText(tag, "MusicBrainz Album Release Country", data.releaseCountry);

    sprintf(temp, "%d", data.nonAlbum);
    setUserText(tag, "MusicBrainz Non-Album", temp);
    
    id3_2_3_tag_options(tag, ID3_2_3_TAG_OPTION_COMPRESSION, 0);
    id3_2_3_tag_options(tag, ID3_2_3_TAG_OPTION_CRC, 0);
    id3_2_3_tag_options(tag, ID3_2_3_TAG_OPTION_UNSYNCHRONISATION, 0);
    id3_2_3_tag_options(tag, ID3_2_3_TAG_OPTION_ID3V1, writeV1 ? ID3_2_3_TAG_OPTION_ID3V1 : 0);
    ret = id3_2_3_file_update(file);
    id3_2_3_file_close(file);

    if (ret)
        errString = "Could not write id3 tag to track.";

    return ret == 0;
}
