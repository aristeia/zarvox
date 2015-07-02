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

   $Id: tunepimp.cpp 9816 2008-04-22 08:06:09Z luks $

----------------------------------------------------------------------------*/
#ifdef WIN32
#if _MSC_VER == 1200
#pragma warning(disable:4786)
#endif
#endif

#include <stdio.h>
#include <cstdlib>
#include <map>
using namespace std;

#ifdef WIN32
#include <winsock.h>
#endif

#include "../config.h"
#include "tunepimp.h"
#include "watchdog.h"
#include "dirsearch.h"

#define DB         printf("%s:%d\n", __FILE__, __LINE__);
#ifndef WIN32
#ifndef PLUGIN_DIR
#define PLUGIN_DIR PREFIX"/lib/tunepimp/plugins"
#endif
#endif

TunePimp::TunePimp(const string &appName, const string &appVersion, int startThreads, const char *pluginDir)
{
    context.setTunePimp(this);

    callback = NULL;
    proxyPort = 0;

    plugins = new Plugins();

#ifndef WIN32
    if (pluginDir)
        plugins->load(pluginDir, 0);
    else
    {
        char *ptr = getenv("HOME");
        if (ptr)
        {
            string path(ptr);

            path += string("/.tunepimp/plugins");
            plugins->load(path.c_str(), 0);
        }
        plugins->load("plugins", 0);
        plugins->load(PLUGIN_DIR, 0);
    }
#else
    string path;

    if (pluginDir)
        plugins->load(pluginDir, 0);
    else
        plugins->load("plugins", 0);
#endif

    cache = new FileCache(this);

    if (startThreads & TP_THREAD_ANALYZER)
    {
        watchdog = new WatchdogThread(this);
        analyzer = new Analyzer(this, plugins, cache, watchdog);
    }
    else
    {
        watchdog = NULL;
        analyzer = NULL;
    }

    if (startThreads & TP_THREAD_READ)
        read = new ReadThread(this, cache, plugins);
    else
        read = NULL;

    if (startThreads & TP_THREAD_WRITE)
        write = new WriteThread(this, cache, plugins);
    else
        write = NULL;

    plugins->getSupportedExtensions(extList);

    if (analyzer)
       analyzer->start();
    if (read)
       read->start();
    if (write)
       write->start();

    if (watchdog)
       watchdog->start();
}

TunePimp::~TunePimp(void)
{
    Analyzer         *aTemp;
    WriteThread      *rTemp;
    WatchdogThread   *wTemp;
    ReadThread       *mTemp;

    // Turn the watchdog thread off to make sure it doesn't spawn a new analyzer
    if (watchdog)
        watchdog->stop();

    if (analyzer)
    {
        aTemp = analyzer;
        analyzer = NULL;
        delete aTemp;
    }

    if (read)
    {
        mTemp = read;
        read = NULL;
        delete mTemp;
    }
    if (write)
    {
        rTemp = write;
        write = NULL;
        delete rTemp;
    }

    if (watchdog)
    {
        wTemp = watchdog;
        watchdog = NULL;
        delete wTemp;
    }

    delete cache;

    plugins->unload();
    delete plugins;
}

// Get the version of the library
void TunePimp::getVersion(int &major, int &minor, int &rev)
{
    sscanf(VERSION, "%d.%d.%d", &major, &minor, &rev);
}

string &TunePimp::getFileNameEncoding(void)
{
    return context.getFileNameEncoding();
}

void TunePimp::setFileNameEncoding(const string &encoding)
{
    context.setFileNameEncoding(encoding);
}

void TunePimp::setServer(const string &server, short port)
{
    this->server = server;
    this->port = port;
}

void TunePimp::setProxy(const string &proxyServer, short proxyPort)
{
    this->proxyServer = proxyServer;
    this->proxyPort = proxyPort;
}

void TunePimp::getServer(string &server, short &port)
{
    server = this->server;
    port = this->port;
}

void TunePimp::getProxy(string &proxyServer, short &proxyPort)
{
    proxyServer = this->proxyServer;
    proxyPort = this->proxyPort;
}

void TunePimp::getSupportedExtensions(vector<string> &extList)
{
    extList = this->extList;
}

void TunePimp::setWriteID3v1(bool writeID3v1)
{
    context.setWriteID3v1(writeID3v1);
}

bool TunePimp::getWriteID3v1(void)
{
    return context.getWriteID3v1();
}

void TunePimp::setWriteID3v2_3(bool writeID3v2_3)
{
    context.setWriteID3v2_3(writeID3v2_3);
}

bool TunePimp::getWriteID3v2_3(void)
{
    return context.getWriteID3v2_3();
}

void TunePimp::setID3Encoding(TPID3Encoding enc)
{
    context.setID3Encoding(enc);
}

TPID3Encoding TunePimp::getID3Encoding(void)
{
    return context.getID3Encoding();
}

void TunePimp::setClearTags(bool clearTags)
{
    context.setClearTags(clearTags);
}

bool TunePimp::getClearTags(void)
{
    return context.getClearTags();
}

void TunePimp::setWinSafeFileNames(bool winSafeFileNames)
{
    context.setWinSafeFileNames(winSafeFileNames);
}

bool TunePimp::getWinSafeFileNames(void)
{
    return context.getWinSafeFileNames();
}

void TunePimp::setDestDir(const string &destDir)
{
    context.setDestDir(destDir);
}

string &TunePimp::getDestDir(void)
{
    return context.getDestDir();
}

void TunePimp::setFileMask(const string &fileMask)
{
    context.setFileMask(fileMask);
}

string &TunePimp::getFileMask(void)
{
    return context.getFileMask();
}

void TunePimp::setAllowedFileCharacters(const string &allowedChars)
{
    context.setAllowedFileCharacters(allowedChars);
}

string &TunePimp::getAllowedFileCharacters(void)
{
    return context.getAllowedFileCharacters();
}

void TunePimp::setVariousFileMask(const string &variousFileMask)
{
    context.setVariousFileMask(variousFileMask);
}

string &TunePimp::getVariousFileMask(void)
{
    return context.getVariousFileMask();
}

void TunePimp::setNonAlbumFileMask(const string &nonAlbumFileMask)
{
    context.setNonAlbumFileMask(nonAlbumFileMask);
}

string &TunePimp::getNonAlbumFileMask(void)
{
    return context.getNonAlbumFileMask();
}

void TunePimp::setTopSrcDir(const string &srcDir)
{
    context.setTopSrcDir(srcDir);
}

string &TunePimp::getTopSrcDir(void)
{
    return context.getTopSrcDir();
}

void TunePimp::setMoveFiles(bool moveFiles)
{
    context.setMoveFiles(moveFiles);
}

bool TunePimp::getMoveFiles(void)
{
    return context.getMoveFiles();
}

void TunePimp::setRenameFiles(bool renameFiles)
{
    context.setRenameFiles(renameFiles);
}

bool TunePimp::getRenameFiles(void)
{
    return context.getRenameFiles();
}

void TunePimp::setAutoSaveThreshold(int autoSaveThreshold)
{
    context.setAutoSaveThreshold(autoSaveThreshold);
}

int TunePimp::getAutoSaveThreshold(void)
{
    return context.getAutoSaveThreshold();
}

void TunePimp::setMaxFileNameLen(int maxFileNameLen)
{
    context.setMaxFileNameLen(maxFileNameLen);
}

int TunePimp::getMaxFileNameLen(void)
{
    return context.getMaxFileNameLen();
}

void TunePimp::setAutoRemoveSavedFiles(bool autoRemoveSavedFiles)
{
    context.setAutoRemoveSavedFiles(autoRemoveSavedFiles);
}

bool TunePimp::getAutoRemoveSavedFiles(void)
{
    return context.getAutoRemoveSavedFiles();
}

void TunePimp::setAnalyzerPriority(TPThreadPriorityEnum pri)
{
    if (analyzer)
        analyzer->setPriority(pri);
    context.setAnalyzerPriority(pri);
}

TPThreadPriorityEnum TunePimp::getAnalyzerPriority(void)
{
    if (analyzer == NULL)
	return eNormal;

    return analyzer->getPriority();
}

void TunePimp::setCallback(TPCallback *callback)
{
    this->callback = callback;
}

TPCallback *TunePimp::getCallback(void)
{
    return callback;
}

void TunePimp::getError(string &error)
{
    error = err;
}

// Set the debug option -- if enabled debug output will be printed to stdout
void TunePimp::setDebug(bool debug)
{
    context.setDebug(debug);
}

bool TunePimp::getDebug(void)
{
    return context.getDebug();
}

void TunePimp::setMusicDNSClientId(const string &clientId)
{
    context.setMusicDNSClientId(clientId);
}

string &TunePimp::getMusicDNSClientId(void)
{
    return context.getMusicDNSClientId();
}

// Stoopid windows helper functions to init the winsock layer.
#ifdef WIN32
void TunePimp::WSAInit(void)
{
    WSADATA sGawdIHateMicrosoft;
    WSAStartup(0x0002,  &sGawdIHateMicrosoft);
}

void TunePimp::WSAStop(void)
{
    WSACleanup();
}
#endif

int TunePimp::addFile(const string &fileName, bool readMetadataNow)
{
    int          fileId;

    fileId = cache->add(fileName);
    if (fileId < 0)
	return fileId;

    if (readMetadataNow)
    {
        ReadThread   *read;
        Metadata      mdata;
        Track        *track;

        read = new ReadThread(this, cache, plugins);
        track = cache->getTrack(fileId);
        if (track)
        {
            track->lock();
            read->readMetadata(track, true);
            track->unlock();
            cache->release(track);
        }
        delete read;
    }
    else
    {
        if (callback)
            callback->notify(this, tpFileAdded, fileId, eMetadataRead);

        if (read)
           read->wake();
    }

    return fileId;
}

int TunePimp::addDir(const string &dirPath)
{
    DirSearch search(this, extList);
    int       count, fileId;

    count = search.recurseDir(dirPath.c_str());
    if (count > 0)
    {
        vector<string>           fileList;
        vector<string>::iterator i;
        search.getFiles(fileList);
        for(i = fileList.begin(); i != fileList.end(); i++)
        {
            fileId = cache->add(*i);
            if (callback)
                callback->notify(this, tpFileAdded, fileId, eMetadataRead);
        }
        if (read)
            read->wake();
    }

    return count;
}

int TunePimp::getNumUnsavedItems(void)
{
    return cache->getNumUnsavedItems();
}

void TunePimp::getTrackCounts(map<TPFileStatus, int> &counts)
{
    return cache->getCounts(counts);
}

void TunePimp::remove(int fileId)
{
    Metadata  data;
    Track    *track;

    // When removing a track, nuke the track id from the submit list
    track = cache->getTrack(fileId);
    if (track)
    {
        track->lock();
        track->getServerMetadata(data);
        track->unlock();
        cache->release(track);
    }

    cache->remove(fileId);
    if (callback)
        callback->notify(this, tpFileRemoved, fileId, eDeleted);
}

void TunePimp::getFileIds(vector<int> &ids)
{
    cache->getFileIds(ids);
}

int TunePimp::getNumFiles(void)
{
    return cache->getNumItems();
}

Track *TunePimp::getTrack(int fileId)
{
    return cache->getTrack(fileId);
}

void TunePimp::releaseTrack(Track *track)
{
    cache->release(track);
}

// Since this function blocks, the track is assumed to be locked
// and should not be unlocked.
void TunePimp::wake(Track *track)
{
    if (callback)
    {
        int fileId;

        fileId = cache->getFileIdFromTrack(track);
        if (fileId >= 0)
            callback->notify(this, tpFileChanged, fileId, track->getStatus());
    }

    if (analyzer)
        analyzer->wake();

    if (read)
        read->wake();

    if (write)
        write->wake();
}

void TunePimp::writeTagsComplete(bool error)
{
    if (callback)
        callback->notify(this, tpWriteTagsComplete, (int)error, eError);
}

void TunePimp::trackRemoved(int fileId)
{
    if (callback)
        callback->notify(this, tpFileRemoved, fileId, eDeleted);
}

void TunePimp::setStatus(const string &status)
{
    if (callback)
        callback->status(this, status);
}

int TunePimp::getRecognizedFileList (int threshold, vector<int> &fileIds)
{
    return cache->getRecognizedFileList(threshold, fileIds);
}

bool TunePimp::writeTags(vector<int> *fileIds)
{
    vector<Track *>            tracks;
    vector<Track *>::iterator  i;
    vector<int>::iterator      j;
    Track                     *track;

    if (fileIds)
    {
        for(j = fileIds->begin(); j != fileIds->end(); j++)
        {
            track = cache->getTrack(*j);
            if (!track)
            {
                err = "Invalid track in write tags list.";
                return false;
            }
            if (track->getStatus() != eRecognized)
            {
                err = "All tracks must be recognized before writing tags.";
                return false;
            }
            tracks.push_back(track);
        }
    }
    else
        cache->getTracksFromStatus(eRecognized, tracks);

    // First, change all the states 
    for(i = tracks.begin(); i != tracks.end(); i++)
    {
        (*i)->lock();
        (*i)->setStatus(eVerified);
        (*i)->unlock();
    }

    // And then wake all the tracks
    for(i = tracks.begin(); i != tracks.end(); i++)
    {
        wake(*i);
        cache->release(*i);
    }
    write->wake();

    return true;
}

void TunePimp::misidentified(int fileId)
{
    Track        *track;
    TPFileStatus  status;

    track = cache->getTrack(fileId);
    if (track)
    {
        string   puid;
        Metadata data;

        track->lock();
        track->getPUID(puid);
        track->getServerMetadata(data);

        if (puid.empty())
        {
            track->setPUID(ANALYZER_REDO_STRING);
            track->setStatus(ePending);
            status = ePending;
        }
        else
        {
            track->setStatus(eUnrecognized);
            status = eUnrecognized;
        }

        string format = data.fileFormat;
        data.clear();
        data.fileFormat = format;

        track->setServerMetadata(data);
        track->setError("");
        track->unlock();
        wake(track);
        cache->release(track);

        if (callback)
            callback->notify(this, tpFileChanged, fileId, status);
    }
}

void TunePimp::identifyAgain(int fileId)
{
    Track *track;

    track = cache->getTrack(fileId);
    if (track)
    {
        string   puid;
        Metadata data;

        track->lock();
        track->getPUID(puid);
        track->getServerMetadata(data);

        data.clear();
        track->setPUID(ANALYZER_REDO_STRING);
        track->setServerMetadata(data);
        track->setError("");
        track->setStatus(ePending);
        track->unlock();
        wake(track);
        cache->release(track);

        if (callback)
            callback->notify(this, tpFileChanged, fileId, ePending);
    }
}

void TunePimp::analyzerDied(int fileId)
{
    Track  *track;
    Analyzer *oldAnalyzer;

    if (analyzer == NULL)
        return;

    track = cache->getTrack(fileId);
    if (track)
    {
        track->lock();
        track->setStatus(eError);
        track->setError("Cannot decode file. (Decoder crashed)");
        track->unlock();
        wake(track);

        // Here we need to call release TWICE since the crashed
        // analyzer had a reference on the track. 
        cache->release(track);
        cache->release(track);

        if (callback)
            callback->notify(this, tpFileChanged, fileId, eError);
    }

    oldAnalyzer = analyzer;
    analyzer = new Analyzer(this, plugins, cache, watchdog);
    analyzer->start();

    delete oldAnalyzer;
}

// I'm not sure this function can be completely uncommented. But for now we'll go with it.
void TunePimp::trackChangedStatus(Track *track)
{
#if 0
    int fileId;

    if (callback)
    {
        fileId = cache->getFileIdFromTrack(track);
        if (fileId >= 0)
            callback->notify(this, tpFileChanged, fileId, track->getStatus());
    }
#endif
}
