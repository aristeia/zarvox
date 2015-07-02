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

   $Id: readmeta.cpp 9816 2008-04-22 08:06:09Z luks $

----------------------------------------------------------------------------*/
#ifdef WIN32
#if _MSC_VER == 1200
#pragma warning(disable:4786)
#endif
#endif

#include <stdio.h>
#include <cstdlib>

#ifndef WIN32
#include <unistd.h>
#endif
#include "../config.h"
#include "readmeta.h"
#include "tunepimp.h"
#include "plugin.h"
#include "watchdog.h"
#include "utf8/utf8util.h"

const int iDataFieldLen = 255;

#define DB printf("%s:%d\n", __FILE__, __LINE__);

//---------------------------------------------------------------------------

ReadThread::ReadThread(TunePimp       *tunePimpArg,
                           FileCache      *cacheArg,
                           Plugins        *pluginsArg) : Thread()
{
   tunePimp = tunePimpArg;
   plugins = pluginsArg;
   cache = cacheArg;
   exitThread = false;
   sem = new Semaphore();
}

//---------------------------------------------------------------------------

ReadThread::~ReadThread(void)
{
   exitThread = true;
   sem->signal();
   join();
   delete sem;
}

//---------------------------------------------------------------------------

void ReadThread::wake(void)
{
    sem->signal();
}

//---------------------------------------------------------------------------

void ReadThread::threadMain(void)
{
    Track        *track;

    for(; !exitThread;)
    {
        Metadata data;

        track = cache->getNextItem(eMetadataRead);
        if (track == NULL)
        {

           sem->wait();
           continue;
        }

        readMetadata(track, true);
        tunePimp->wake(track);
        cache->release(track);
    }
}

//---------------------------------------------------------------------------
bool  ReadThread::readMetadata(Track *track, bool calcDuration)
{
    string        fileName, ext;
    Metadata      data, fileNameData;
    char         *ptr;
    bool          ret = true;
    Plugin       *plugin = NULL;
    metadata_t    mdata;
    TPFileStatus  status;
    unsigned long duration = 0;
    int           flags = 0;

    track->lock();
    track->setError("");
    track->getFileName(fileName);
    ptr = strrchr((char *)fileName.c_str(), '.');

    // For the initial values, try to parse the filename and see what we can get 
    // from it.
    parseFileName(fileName, fileNameData);

    if (ptr)
        plugin = plugins->get(string(ptr), TP_PLUGIN_FUNCTION_METADATA);
    if (plugin)
    {
        bool   ret;
        string err, encoding;
    
        try
        {
            track->unlock();

            flags = 0;
            encoding = tunePimp->context.getFileNameEncoding();
            if (tunePimp->context.getWriteID3v2_3())
                flags |= TP_PLUGIN_FLAGS_MP3_USE_ID3V23;

            ret = plugin->readMetadata(&mdata, fileName.c_str(), flags, encoding.c_str());
            if (ret && calcDuration)
            {
                duration = plugin->getDuration(fileName.c_str(), flags, encoding.c_str());
            }

            track->lock();
        }   
        catch(...)
        {
            ret = false;
        }
        
        if (ret)
            data.readFromC(&mdata);
        else
        { 
            err = string(plugin->getError());
            track->setStatus(eError);
            track->setError(string("Could not read metadata from track: ") + string(err));
            track->unlock();
            return false;
        }
    }   
    else
    {
        // If the plugin doesn't support metadata reading, then at least fill in the format
        string::size_type pos;
        pos = fileName.rfind(".", fileName.length() - 1);
        if (pos != string::npos)
            data.fileFormat = fileName.substr(pos + 1);
    }

    if (duration > 0)
        data.duration = duration;
    if (data.artist.empty())
        data.artist = fileNameData.artist;
    if (data.album.empty())
        data.album = fileNameData.album;
    if (data.track.empty())
        data.track = fileNameData.track;
    if (data.trackNum <= 0)
        data.trackNum = fileNameData.trackNum;

    if (!data.trackId.empty())
    {
        // Yup, toss it into saved
        track->setServerMetadata(data);
        if (track->hasChanged())
            status = eRecognized;
        else
            status = eSaved;
    }
    else
        status = eUnrecognized;

    track->setStatus(status);
    track->setLocalMetadata(data);
    track->unlock();

    return ret;
}

void ReadThread::parseFileName(const string &fileName, Metadata &data)
{
    FileNameMaker maker(&tunePimp->context);
    string        name, encoding;
    int           ret;
    char          field1[iDataFieldLen], field2[iDataFieldLen];
    char          field3[iDataFieldLen], field4[iDataFieldLen];

    name = maker.extractFileBase(fileName);
    ret = sscanf(name.c_str(), "%254[^-]-%254[^-]-%254[^-]-%254[^\n\r]",
            field1, field2, field3, field4);

    encoding = tunePimp->context.getFileNameEncoding();
    switch(ret)
    {
        case 4:
            data.artist = utf8FromEncoding(field1, encoding);
            data.album = utf8FromEncoding(field2, encoding);
            data.trackNum = atoi(field3);
            data.track = utf8FromEncoding(field4, encoding);
            break;
        case 3:
            data.artist = utf8FromEncoding(field1, encoding);
            if (atoi(field2) > 0)
                data.trackNum = atoi(field2);
            else
                data.album = utf8FromEncoding(field2, encoding);
            data.track = utf8FromEncoding(field3, encoding);
            break;
        case 2:
            data.artist = utf8FromEncoding(field1, encoding);
            data.track = utf8FromEncoding(field2, encoding);
            break;
        case 1:
            data.track = utf8FromEncoding(field1, encoding);
            break;
        default:
            break;
    }

    trimWhitespace(data.artist);
    trimWhitespace(data.album);
    trimWhitespace(data.track);
}

void ReadThread::trimWhitespace(string &field)
{
    for(; field.size() > 0;)
        if (field[0] == ' ' || field[0] == '\t' || field[0] == '\r')
            field.erase(0, 1);
        else
            break;

    for(; field.size() > 0;)
    {
        int last = field.size() - 1;
        if (field[last] == ' ' || field[last] == '\t' || field[last] == '\r')
            field.erase(last, 1);
        else
            break;
    }
}
