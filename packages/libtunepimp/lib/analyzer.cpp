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

   $Id: analyzer.cpp 9816 2008-04-22 08:06:09Z luks $

----------------------------------------------------------------------------*/
#ifdef WIN32
#if _MSC_VER == 1200
#pragma warning(disable:4786)
#endif
#endif

#include <stdio.h>
#include <cstring>
#ifndef WIN32
#include <unistd.h>
#endif
#include "ofa1/ofa.h"
#include "../config.h"
#include "analyzer.h"
#include "tunepimp.h"
#include "watchdog.h"
#include "protocol.h"

const long chunkSize = 8192;

// supposedly we only need 130 seconds, but I will add a little extra in case we have silence at the beginning
const int PUIDDecodeSeconds = 135;

#define DB printf("%s:%d\n", __FILE__, __LINE__);

//---------------------------------------------------------------------------

Analyzer::Analyzer(TunePimp       *tunePimpArg,
                   Plugins        *plugins, 
                   FileCache      *cacheArg,
                   WatchdogThread *watchdog) : Thread()
{
   tunePimp = tunePimpArg;
   this->plugins = plugins;
   cache = cacheArg;
   dog = watchdog;
   exitThread = false;
   sem = new Semaphore();
}

//---------------------------------------------------------------------------

Analyzer::~Analyzer(void)
{
   exitThread = true;
   sem->signal();
   join();
   delete sem;
}

//---------------------------------------------------------------------------

void Analyzer::wake(void)
{
    sem->signal();
}

//---------------------------------------------------------------------------

void Analyzer::threadMain(void)
{
    string  fileName, status, puid;
    Track  *track;

    dog->setAnalyzerThread(getId());
    setPriority(tunePimp->context.getAnalyzerPriority());
    for(; !exitThread;)
    {
        unsigned long  duration = 0;
        char          *ptr;
        Plugin        *plugin;
        PUIDResult     ret = eOtherError;
        puid = "";

        track = cache->getNextItem(ePending);
        if (track == NULL)
        {
           sem->wait();
           continue;
        }

        track->lock();

        dog->setAnalyzerTask(cache->getFileIdFromTrack(track));
        
        track->getFileName(fileName);

        // Check to see if we pulled up a musicbrainz id
        Metadata data, id3;
        track->getServerMetadata(data);
        track->getLocalMetadata(id3);
        track->getPUID(puid);
        if (puid == string(ANALYZER_REDO_STRING))
        {
            data.clear();
            data.trackId = "";
            track->setServerMetadata(data);

            track->getLocalMetadata(id3);
            id3.trackId = "";
            track->setLocalMetadata(id3);
        }

        ptr = strrchr((char *)fileName.c_str(), '.');
        if (ptr)
            plugin = plugins->get(string(ptr), TP_PLUGIN_FUNCTION_DECODE);
        else
            plugin = NULL;

        if (plugin)
        {
            string err;

            track->unlock();
            status = "Analyzing " + fileName;
            tunePimp->setStatus(status);
            ret = calculatePUID(plugin, fileName, err, puid, duration, id3);
            track->lock();

            // Check to make sure no one has messed with this track since we started
            if (track->getStatus() == ePending)
            {
                if (duration > 0)
                {
                    Metadata fileData;

                    track->getLocalMetadata(fileData);
                    fileData.duration = duration;
                    track->setLocalMetadata(fileData);
                }

                if (ret != eOk)
                {
                    if (ret == eNoPUID)
                        track->setStatus(eUnrecognized);
                    else
                    {
                        tunePimp->setStatus("Failed to generate puid from " + fileName);
                        if (err.empty())
                            setError(track, ret);
                        else
                            track->setError(err);
                        track->setStatus(eError);
                    }
                    tunePimp->setStatus(string(" "));
                }
                else
                {
                    track->setPUID(puid);
                    track->setStatus(ePUIDLookup);
                }
            }
        }
        else
        {
            string err;

            if (ptr)
                err = string("Fingerprinting of ") + string(ptr) + (" files is not supported.");
            else
                err = string(fileName) + string(": cannot determine filetype.");
            tunePimp->setStatus(err);
            track->setStatus(eError);
            track->setError(err);
        }
        track->unlock();
        tunePimp->wake(track);
        cache->release(track);
        dog->setAnalyzerTask(-1);
    }
}

//---------------------------------------------------------------------------

void Analyzer::setError(Track *track, PUIDResult retVal)
{
    switch(retVal)
    {
        case eFileNotFound:
           track->setError("Audio file not found.");
           break;
        case eDecodeError:
           track->setError("Cannot decode audio file.");
           break;
        case eCannotConnect:
           track->setError("Cannot connect to the PUID signature server.");
           break;
        case eOutOfMemory:
           track->setError("Out of memory while creating acoustic fingerprint.");
           break;
        case eNoClientId:
           track->setError("No MusicDNS client id was provided.");
           break;
        case eNoPUID:
           track->setError("There is no PUID available for this track.");
           break;
        default:
           track->setError("Unknown error. Sorry, this program sucks.");
           break;
    }
}

//---------------------------------------------------------------------------

PUIDResult Analyzer::calculatePUID(Plugin *plugin, const string &fileName, string &err, 
                                   string &puid, unsigned long &duration, Metadata &mdata)
{
    PUIDResult  ret = eOk;
    void       *decode;
    string      print;

    if (tunePimp->context.getMusicDNSClientId().length() == 0)
        return eNoClientId;

    // The only thing the try block should catch is something
    // we know nothing about or a segfault and even then only
    // under windows. Thus, exit the thread and let the
    // watchdog skip this file and start a new analyzer.
    try
    {
        unsigned int samplesPerSecond, bitsPerSample, channels;
        int      numRead;
        string   proxyServer, encoding;
        int      flags = 0;

        encoding = tunePimp->context.getFileNameEncoding();

        decode = plugin->decodeStart(fileName.c_str(), flags, encoding.c_str());
        if (!decode)
        {
            err = string(plugin->getError());
            ret = eDecodeError;
        }
        else
        {
            if (!plugin->decodeInfo(decode, &duration, &samplesPerSecond, &bitsPerSample, &channels))
            {
                err = string(plugin->getError());
                ret = eDecodeError;
            }
            else
            {
                long size = PUIDDecodeSeconds * samplesPerSecond * (bitsPerSample / 8) * channels;
                // Round this block up to the next nearest chunk size!
                long blockSize = ((size / chunkSize) + 1) * chunkSize;

                unsigned char *buffer = new unsigned char[blockSize];
                if (!buffer)
                {
                    plugin->decodeEnd(decode);
                    return eOutOfMemory;
                }

                long readOffset = 0, bytesLeft = size;
                while(bytesLeft > 0)
                {
                    long thisBlock = min(bytesLeft, chunkSize);
                    numRead = plugin->decodeRead(decode, (char *)(buffer + readOffset), thisBlock);
                    if (numRead < 0)
                    {
                        err = string(plugin->getError());
                        ret = eDecodeError;
                        break;
                    }
                    readOffset += numRead;
                    bytesLeft -= numRead;
                    if (numRead == 0)
                        break;
                }

                if (ret == eOk)
                {
                    AudioData data(tunePimp->context.getMusicDNSClientId(), "libtunepimp-" VERSION);

                    data.setData(buffer, OFA_LITTLE_ENDIAN, readOffset / sizeof(short), samplesPerSecond, channels == 2);
                    // TODO: report correct bitrate
                    data.info.setBitrate(0);

                    data.info.setFormat(mdata.fileFormat);
                    data.info.setLengthInMS(duration);
                    data.info.setArtist(mdata.artist);
                    data.info.setTrack(mdata.track);
                    data.info.setAlbum(mdata.album);
                    data.info.setTrackNum(mdata.trackNum);
                    char year[5];
                    sprintf(year, "%d", mdata.releaseYear);
                    data.info.setYear(year);
                    data.info.setMetadataFlag(true);
                    if (data.createPrint())
                    {
                        delete [] buffer;
                        if (retrieve_metadata(&data.info))
                        {
                            puid = data.info.getPUID();
                            if (puid.length() == 0)
                            {
                                ret = eNoPUID;
                            }
                        }
                        else
                            ret = eNoPUID;
                    }
                    else
                    {
                        delete [] buffer;
                        ret = eNoPUID;
                    }
                }
                else
                {
                    delete [] buffer;
                }
            }
        }

        plugin->decodeEnd(decode);
    }
    catch(...)
    {
        terminate();
    }

    return ret;
}
