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

   $Id: c_wrapper.cpp 9816 2008-04-22 08:06:09Z luks $

----------------------------------------------------------------------------*/
#include "tunepimp.h"
#include "mutex.h"
#include "tp_c.h"
#include "astrcmp.h"

#define DB printf("%s:%d\n", __FILE__, __LINE__);

#define TP_OBJ_CHECK(o) TunePimp *obj = (TunePimp *)o; \
                        if (obj == NULL) return 0;
#define TP_OBJ_CHECKV(o) TunePimp *obj = (TunePimp *)o; \
                         if (obj == NULL) return;
#define TP_OBJ_CHECKN(o) TunePimp *obj = (TunePimp *)o; \
                         if (obj == NULL) return NULL;
#define TR_OBJ_CHECK(o) Track *obj = (Track *)t; \
                        if (obj == NULL) return 0;
#define TR_OBJ_CHECKV(o) Track *obj = (Track *)t; \
                         if (obj == NULL) return;

#include <deque>
#include <cstdlib>

class NotifyData
{
    public:

        bool operator==(const NotifyData &other)
        {
            return status == other.status && type == other.type && fileId == other.fileId;
        }
        void operator=(const NotifyData &other)
        {
            status = other.status;
            type = other.type;
            fileId = other.fileId;
        }

        TPFileStatus   status;
        TPCallbackEnum type;
        int            fileId;

};

class Callback : public TPCallback
{
    public:

        Callback(void)
        {
            notifyCallback = NULL;
            statusCallback = NULL;
            notifyData = statusData = NULL;
        };
        virtual ~Callback(void) {};

        void notify(TunePimp *pimp, TPCallbackEnum type, int fileId, TPFileStatus status)
        {
            notifyMutex.acquire();
            if (notifyCallback)
                (*notifyCallback)((tunepimp_t)pimp, notifyData, type, fileId, status);
            else
            {
                NotifyData   p, top;
                bool         add = true;

                if (notifyQueue.size() > 0)
                {
                    top = notifyQueue.front();
                    if (top.type == type && top.fileId == fileId && top.status == status)
                        add = false; 
                }

                if (add)
                {
                    p.type = type;
                    p.fileId = fileId;
                    p.status = status;
                    notifyQueue.push_back(p);
                }
            }
            notifyMutex.release();
        };
        void status(TunePimp *pimp, const string &status)
        {
            statusMutex.acquire();
            if (statusCallback)
                (*statusCallback)((tunepimp_t)pimp, statusData, status.c_str());
            else
                statusQueue.push_back(status);
            statusMutex.release();
        };
        bool getNotification(TPCallbackEnum &type, int &fileId, TPFileStatus &status)
        {
            bool ret = false;

            notifyMutex.acquire();
            if (notifyQueue.size() > 0)
            {
                NotifyData p;

                p = notifyQueue.front();
                notifyQueue.pop_front();

                type = p.type;
                fileId = p.fileId;
                status = p.status;

                ret = true;
            }
            notifyMutex.release();

            return ret;
        }
        bool getStatus(string &status)
        {
            bool ret = false;

            statusMutex.acquire(); 
            if (statusQueue.size() > 0)
            {
                status = statusQueue.front();
                statusQueue.pop_front();
                ret = true;
            }
            statusMutex.release();
            return ret;
        }

        tp_notify_callback  notifyCallback;
        tp_status_callback  statusCallback;
        void               *notifyData, *statusData;

    private:

        TunePimp          *tunePimp;
        deque<NotifyData>  notifyQueue;
        deque<string>      statusQueue;
        Mutex              statusMutex, notifyMutex;
};

extern "C"
{

tunepimp_t tp_New(const char *appName, const char *appVersion)
{
    TunePimp *pimp = new TunePimp(appName, appVersion);
    Callback *cb = new Callback();

    pimp->setCallback(cb);

    return (tunepimp_t)pimp;
}

tunepimp_t tp_NewWithArgs(const char *appName, const char *appVersion, 
                          int startThreads, const char *pluginDir)
{
    TunePimp *pimp = new TunePimp(appName, appVersion, startThreads, pluginDir);
    Callback *cb = new Callback();

    pimp->setCallback(cb);

    return (tunepimp_t)pimp;
}

void tp_Delete(tunepimp_t o)
{
    Callback *old;

    TP_OBJ_CHECKV(o);

    old = (Callback *)obj->getCallback();
    delete (TunePimp *)obj;
    delete old;
}

void tp_SetNotifyCallback(tunepimp_t o, tp_notify_callback callback, void *data)
{
    Callback *cb;

    TP_OBJ_CHECKV(o);

    cb = (Callback *)obj->getCallback();
    cb->notifyCallback = callback;
    cb->notifyData = data;
}

tp_notify_callback tp_GetNotifyCallback(tunepimp_t o)
{
    Callback *cb;

    TP_OBJ_CHECKN(o);

    cb = (Callback *)obj->getCallback();
    return cb->notifyCallback;
}

void tp_SetStatusCallback(tunepimp_t o, tp_status_callback callback, void *data)
{
    Callback *cb;

    TP_OBJ_CHECKV(o);

    cb = (Callback *)obj->getCallback();
    cb->statusCallback = callback;
    cb->statusData = data;
}

tp_status_callback tp_GetStatusCallback(tunepimp_t o)
{
    Callback *cb;

    TP_OBJ_CHECKN(o);

    cb = (Callback *)obj->getCallback();
    return cb->statusCallback;
}

int tp_GetNotification(tunepimp_t o, TPCallbackEnum *type, int *fileId, TPFileStatus *status)
{
    Callback *cb;

    TP_OBJ_CHECK(o);

    cb = (Callback *)obj->getCallback();
    return (int)cb->getNotification(*type, *fileId, *status);
}

int tp_GetStatus(tunepimp_t o, char *status, int statusLen)
{
    Callback *cb;
    string    s;

    TP_OBJ_CHECK(o);

    cb = (Callback *)obj->getCallback();
    if (cb->getStatus(s))
    {
        strncpy(status, s.c_str(), statusLen - 1);
        status[statusLen - 1] = 0;
        return 1;
    }
    return 0;
}

void tp_GetVersion(tunepimp_t o, int *major, int *minor, int *rev)
{
    *major = *minor = *rev = 0;

    TP_OBJ_CHECKV(o);

    obj->getVersion(*major, *minor, *rev);
}

void tp_SetServer(tunepimp_t o, const char *serverAddr, short serverPort)
{
    TP_OBJ_CHECKV(o);

    obj->setServer(string(serverAddr), serverPort);
}

void tp_GetServer(tunepimp_t o,
                    char *serverAddr, int maxLen,
                    short *serverPort)
{
    string tmpServerAddr;

    TP_OBJ_CHECKV(o);

    obj->getServer(tmpServerAddr, *serverPort);
    strncpy(serverAddr, tmpServerAddr.c_str(), maxLen - 1);
    serverAddr[maxLen - 1] = 0;
}

void tp_SetDebug(tunepimp_t o, int debug)
{
    TP_OBJ_CHECKV(o);

    obj->setDebug((bool)debug);
}

int tp_GetDebug(tunepimp_t o)
{
    TP_OBJ_CHECK(o);

    return obj->getDebug();
}

void tp_SetProxy(tunepimp_t o, const char *proxyAddr, short proxyPort)
{
    TP_OBJ_CHECKV(o);

    string addr = "";
    if (proxyAddr)
        addr = proxyAddr;
    obj->setProxy(addr, proxyPort);
}

void tp_GetProxy(tunepimp_t o,
                 char *proxyAddr, int maxLen,
                 short *proxyPort)
{
    string tmpProxyAddr;

    TP_OBJ_CHECKV(o);

    obj->getProxy(tmpProxyAddr, *proxyPort);
    strncpy(proxyAddr, tmpProxyAddr.c_str(), maxLen - 1);
    proxyAddr[maxLen - 1] = 0;
}

void tp_SetFileNameEncoding(tunepimp_t o, const char *encoding)
{
    TP_OBJ_CHECKV(o);
    obj->setFileNameEncoding(string(encoding));
}

void tp_GetFileNameEncoding(tunepimp_t o, char *encoding, int maxEncodingLen)
{
    string temp;
    TP_OBJ_CHECKV(o);
    temp = obj->getFileNameEncoding();
    strncpy(encoding, temp.c_str(), maxEncodingLen - 1);
    encoding[maxEncodingLen - 1] = 0;
}

void tp_SetMusicDNSClientId(tunepimp_t o, const char *clientId)
{
    TP_OBJ_CHECKV(o);
    obj->setMusicDNSClientId(clientId);
}

void tp_GetMusicDNSClientId(tunepimp_t o, char *clientId, int maxClientIdLen)
{
    string tmpClientId;

    TP_OBJ_CHECKV(o);

    tmpClientId = obj->getMusicDNSClientId();
    strncpy(clientId, tmpClientId.c_str(), maxClientIdLen - 1);
    clientId[maxClientIdLen - 1] = 0;
}

int tp_GetNumSupportedExtensions(tunepimp_t o)
{
    vector<string> extList;

    TP_OBJ_CHECK(o);

    obj->getSupportedExtensions(extList);

    return extList.size();
}

void tp_GetSupportedExtensions(tunepimp_t o, char extensions[][TP_EXTENSION_LEN])
{
    vector<string>            extList;
    vector<string>::iterator  i;
    int                       count;

    TP_OBJ_CHECKV(o);

    obj->getSupportedExtensions(extList);
    for(i = extList.begin(), count = 0; i != extList.end(); i++, count++)
       strcpy(extensions[count], (*i).c_str());
}

void tp_SetAnalyzerPriority(tunepimp_t o, TPThreadPriorityEnum priority)
{
    TP_OBJ_CHECKV(o);
    obj->setAnalyzerPriority(priority);
}

TPThreadPriorityEnum tp_GetAnalyzerPriority(tunepimp_t o)
{
    TunePimp *obj = (TunePimp *)o;

    if (o == NULL)
        return eNormal;

    return obj->getAnalyzerPriority();
}

void tp_GetError(tunepimp_t o, char *error, int maxLen)
{
    string err;

    TP_OBJ_CHECKV(o);

    obj->getError(err);
    strncpy(error, err.c_str(), maxLen - 1);
    error[maxLen - 1] = 0;
}

int tp_AddFile(tunepimp_t o, const char *fileName, int readMetadataNow)
{
    TP_OBJ_CHECK(o);
    return (int)obj->addFile(fileName, readMetadataNow);
}

int tp_AddDir(tunepimp_t o, const char *dirPath)
{
    TP_OBJ_CHECK(o);
    return (int)obj->addDir(dirPath);
}

void tp_Remove(tunepimp_t o, int fileId)
{
    TP_OBJ_CHECKV(o);
    obj->remove(fileId);
}

void tp_Wake(tunepimp_t o, track_t track)
{
    TP_OBJ_CHECKV(o);
    obj->wake((Track *)track);
}

int tp_GetNumFiles(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getNumFiles();
}

int tp_GetTrackCounts(tunepimp_t o, int *counts, int maxCounts)
{
    map<TPFileStatus, int> countMap;
    int                    i;

    TP_OBJ_CHECK(o);

    obj->getTrackCounts(countMap);

    for(i = 0; i < maxCounts && i < (int)eLastStatus; i++)
        counts[i] = countMap[(TPFileStatus)i];

    return i - 1;
}

int tp_GetNumUnsavedItems(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getNumUnsavedItems();
}

int tp_GetNumFileIds(tunepimp_t o)
{
    vector<int> ids;

    TP_OBJ_CHECK(o);

    obj->getFileIds(ids);
    return ids.size();
}

void tp_GetFileIds(tunepimp_t o, int *ids, int numIds)
{
    vector<int>           vec;
    vector<int>::iterator i;

    TP_OBJ_CHECKV(o);

    obj->getFileIds(vec);
    for(i = vec.begin(); i != vec.end() && numIds > 0; i++, ids++, numIds--)
        *ids = *i;
}

track_t tp_GetTrack(tunepimp_t o, int fileId)
{
    TP_OBJ_CHECKN(o);
    return (track_t)obj->getTrack(fileId);
}

void tp_ReleaseTrack(tunepimp_t o, track_t track)
{
    TP_OBJ_CHECKV(o);

    if (track == NULL)
        return;

    obj->releaseTrack((Track *)track);
}

void tp_Misidentified(tunepimp_t o, int fileId)
{
    TP_OBJ_CHECKV(o);
    obj->misidentified(fileId);
}

void tp_IdentifyAgain(tunepimp_t o, int fileId)
{
    TP_OBJ_CHECKV(o);
    obj->identifyAgain(fileId);
}

int tp_GetRecognizedFileList(tunepimp_t o, int threshold, int **fileIds, int *numIds)
{
    vector<int>           ids;
    vector<int>::iterator i;
    int                   ret, *ptr;

    TP_OBJ_CHECK(o);
    ret = obj->getRecognizedFileList(threshold, ids);

    if (ids.size() > 0)
    {
        *fileIds = (int *)malloc(sizeof(int) * ids.size());
        
        for(i = ids.begin(), ptr = *fileIds; i != ids.end(); i++, ptr++)
            *ptr = *i;
        *numIds = ids.size();
    }
    else
    {
        *numIds = 0;
        *fileIds = NULL;
    }

    return ret;
}

void tp_DeleteRecognizedFileList(tunepimp_t o, int *fileIds)
{
    if (fileIds)
        free(fileIds);
}

int tp_WriteTags(tunepimp_t o, int *fileIds, int numFileIds)
{
    vector<int> ids;

    TP_OBJ_CHECK(o);

    if (!fileIds)
        return obj->writeTags(NULL);

    for(; numFileIds > 0; numFileIds--, fileIds++)
        ids.push_back(*fileIds);

    return obj->writeTags(&ids);
}

void tp_SetRenameFiles(tunepimp_t o, int rename)
{
    TP_OBJ_CHECKV(o);
    obj->setRenameFiles((bool)rename);
}

int tp_GetRenameFiles(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getRenameFiles();
}

void tp_SetMoveFiles(tunepimp_t o, int move)
{
    TP_OBJ_CHECKV(o);
    obj->setMoveFiles((bool)move);
}

int tp_GetMoveFiles(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getMoveFiles();
}

void tp_SetWriteID3v1(tunepimp_t o, int writeID3v1)
{
    TP_OBJ_CHECKV(o);
    obj->setWriteID3v1((bool)writeID3v1);
}

int tp_GetWriteID3v1(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getWriteID3v1();
}

void tp_SetWriteID3v2_3(tunepimp_t o, int writeID3v2_3)
{
    TP_OBJ_CHECKV(o);
    obj->setWriteID3v2_3(writeID3v2_3);
}

int tp_GetWriteID3v2_3(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getWriteID3v2_3();
}

void tp_SetID3Encoding(tunepimp_t o, TPID3Encoding encoding)
{
    TP_OBJ_CHECKV(o);
    obj->setID3Encoding(encoding);
}

TPID3Encoding tp_GetID3Encoding(tunepimp_t o)
{
    TunePimp *obj = (TunePimp *)o;
    if (obj == NULL) 
        return eEncodingError;

    return obj->getID3Encoding();
}

void tp_SetClearTags(tunepimp_t o, int clearTags)
{
    TP_OBJ_CHECKV(o);
    obj->setClearTags((bool)clearTags);
}

int tp_GetClearTags(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getClearTags();
}

void tp_SetWinSafeFileNames(tunepimp_t o, int winSafeFileNames)
{
    TP_OBJ_CHECKV(o);
    obj->setWinSafeFileNames((bool)winSafeFileNames);
}

int tp_GetWinSafeFileNames(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getWinSafeFileNames();
}

void tp_SetFileMask(tunepimp_t o, const char *fileMask)
{
    TP_OBJ_CHECKV(o);
    obj->setFileMask(fileMask);
}

void tp_GetFileMask(tunepimp_t o, char *fileMask, int maxLen)
{
    string tmpFileMask;

    TP_OBJ_CHECKV(o);

    tmpFileMask = obj->getFileMask();
    strncpy(fileMask, tmpFileMask.c_str(), maxLen - 1);
    fileMask[maxLen - 1] = 0;
}

void tp_SetVariousFileMask(tunepimp_t o, const char *variousFileMask)
{
    TP_OBJ_CHECKV(o);
    obj->setVariousFileMask(variousFileMask);
}

void tp_GetVariousFileMask(tunepimp_t o, char *variousFileMask, int maxLen)
{
    string tmpVariousFileMask;

    TP_OBJ_CHECKV(o);

    tmpVariousFileMask = obj->getVariousFileMask();
    strncpy(variousFileMask, tmpVariousFileMask.c_str(), maxLen - 1);
    variousFileMask[maxLen - 1] = 0;
}

void tp_SetNonAlbumFileMask(tunepimp_t o, const char *nonAlbumFileMask)
{
    TP_OBJ_CHECKV(o);
    obj->setNonAlbumFileMask(nonAlbumFileMask);
}

void tp_GetNonAlbumFileMask(tunepimp_t o, char *nonAlbumFileMask, int maxLen)
{
    string tmpNonAlbumFileMask;

    TP_OBJ_CHECKV(o);

    tmpNonAlbumFileMask = obj->getNonAlbumFileMask();
    strncpy(nonAlbumFileMask, tmpNonAlbumFileMask.c_str(), maxLen - 1);
    nonAlbumFileMask[maxLen - 1] = 0;
}

void tp_SetAllowedFileCharacters(tunepimp_t o, const char *allowedCharacters)
{
    TP_OBJ_CHECKV(o);
    obj->setAllowedFileCharacters(allowedCharacters);
}

void tp_GetAllowedFileCharacters(tunepimp_t o, char *allowedCharacters, int maxLen)
{
    string tmpAllowedCharacters;

    TP_OBJ_CHECKV(o);

    tmpAllowedCharacters = obj->getAllowedFileCharacters();
    strncpy(allowedCharacters, tmpAllowedCharacters.c_str(), maxLen - 1);
    allowedCharacters[maxLen - 1] = 0;
}

void tp_SetDestDir(tunepimp_t o, const char *destDir)
{
    TP_OBJ_CHECKV(o);
    obj->setDestDir(destDir);
}

void tp_GetDestDir(tunepimp_t o, char *destDir, int maxLen)
{
    string tmpDestDir;

    TP_OBJ_CHECKV(o);

    tmpDestDir = obj->getDestDir();
    strncpy(destDir, tmpDestDir.c_str(), maxLen - 1);
    destDir[maxLen - 1] = 0;
}

void tp_SetTopSrcDir(tunepimp_t o, const char *topSrcDir)
{
    TP_OBJ_CHECKV(o);
    obj->setTopSrcDir(topSrcDir);
}

void tp_GetTopSrcDir(tunepimp_t o, char *topSrcDir, int maxLen)
{
    string tmpTopSrcDir;

    TP_OBJ_CHECKV(o);

    tmpTopSrcDir = obj->getTopSrcDir();
    strncpy(topSrcDir, tmpTopSrcDir.c_str(), maxLen - 1);
    topSrcDir[maxLen - 1] = 0;
}

void tp_SetAutoSaveThreshold(tunepimp_t o, int autoSaveThreshold)
{
    TP_OBJ_CHECKV(o);
    obj->setAutoSaveThreshold(autoSaveThreshold);
}

int tp_GetAutoSaveThreshold(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getAutoSaveThreshold();
}

void tp_SetMaxFileNameLen(tunepimp_t o, int maxFileNameLen)
{
    TP_OBJ_CHECKV(o);
    obj->setMaxFileNameLen(maxFileNameLen);
}

int tp_GetMaxFileNameLen(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getMaxFileNameLen();
}

int tp_GetAutoRemovedSavedFiles(tunepimp_t o)
{
    TP_OBJ_CHECK(o);
    return obj->getAutoRemoveSavedFiles();
}

void tp_SetAutoRemovedSavedFiles(tunepimp_t o, int autoRemoveSavedFiles)
{
    TP_OBJ_CHECKV(o);
    obj->setAutoRemoveSavedFiles(autoRemoveSavedFiles);
}

#ifdef WIN32
void tp_WSAInit(tunepimp_t o)
{
    TP_OBJ_CHECKV(o);
    obj->WSAInit();
}

void tp_WSAStop(tunepimp_t o)
{
    TP_OBJ_CHECKV(o);
    obj->WSAStop();
}
#endif

/* --------------------------------------------------------------------------
 * Track Interface
 * --------------------------------------------------------------------------*/

TPFileStatus tr_GetStatus(track_t t)
{
    Track *obj = (Track *)t;
    if (t == NULL)
        return eError;

    return obj->getStatus();
}

void tr_GetFileName(track_t t, char *fileName, int maxLen)
{
    string file;

    TR_OBJ_CHECKV(t);

    obj->getFileName(file);
    strncpy(fileName, file.c_str(), maxLen - 1);
    fileName[maxLen - 1] = 0;
}

void tr_GetPUID(track_t t, char *puidArg, int maxLen)
{
    string puid;

    TR_OBJ_CHECKV(t);

    obj->getPUID(puid);
    strncpy(puidArg, puid.c_str(), maxLen - 1);
    puidArg[maxLen - 1] = 0;
}

void tr_GetLocalMetadata(track_t t, metadata_t *mdata)
{
    Metadata data;

    TR_OBJ_CHECKV(t);

    obj->getLocalMetadata(data);
    data.writeToC(mdata);
}

void tr_SetLocalMetadata(track_t t, const metadata_t *mdata)
{
    Metadata data;

    TR_OBJ_CHECKV(t);

    data.readFromC(mdata);
    obj->setLocalMetadata(data);
}

void tr_GetServerMetadata(track_t t, metadata_t *mdata)
{
    Metadata data;

    TR_OBJ_CHECKV(t);

    obj->getServerMetadata(data);
    data.writeToC(mdata);
}

void tr_SetServerMetadata(track_t t, const metadata_t *mdata)
{
    Metadata data;

    TR_OBJ_CHECKV(t);

    data.readFromC(mdata);
    obj->setServerMetadata(data);
}

void tr_GetError(track_t t, char *error, int maxLen)
{
    string err;

    TR_OBJ_CHECKV(t);

    obj->getError(err);
    strncpy(error, err.c_str(), maxLen - 1);
    error[maxLen - 1] = 0;
}

int tr_GetSimilarity(track_t t)
{
    TR_OBJ_CHECK(t);
    return obj->getSimilarity();
}

int tr_HasChanged(track_t t)
{
    TR_OBJ_CHECK(t);
    return (int)obj->hasChanged();
}

void tr_SetChanged(track_t t)
{
    TR_OBJ_CHECKV(t);
    obj->setChanged();
}

void tr_SetStatus(track_t t, const TPFileStatus status)
{
    TR_OBJ_CHECKV(t);
    obj->setStatus(status);
}

void tr_Lock(track_t t)
{
    TR_OBJ_CHECKV(t);
    obj->lock();
}

void tr_Unlock(track_t t)
{
    TR_OBJ_CHECKV(t);
    obj->unlock();
}

/* --------------------------------------------------------------------------
 * Metadata Interface
 * --------------------------------------------------------------------------*/
metadata_t *md_New(void)
{
    return (metadata_t *)calloc(sizeof(metadata_t), 1);
}

void md_Delete(metadata_t *data)
{
    if (!data)
        return;

    free(data);
}

void md_Clear(metadata_t *data)
{
    if (!data)
        return;

    memset(data, 0, sizeof(metadata_t));
}

int md_Compare(const metadata_t *A, const metadata_t *B)
{
    MetadataCompare comp;
    Metadata mdataA, mdataB;

    if (!A || !B)
        return 0;

    mdataA.readFromC(A);
    mdataB.readFromC(B);

    return comp.compare(mdataA, mdataB);
}

TPAlbumStatus md_ConvertToAlbumStatus(const char *albumStatus)
{
    return convertToAlbumStatus(albumStatus);
}

TPAlbumType md_ConvertToAlbumType(const char *albumType)
{
    return convertToAlbumType(albumType);
}

void md_ConvertFromAlbumStatus(TPAlbumStatus status, char *albumStatus, int maxLen)
{
    string statusStr;

    convertFromAlbumStatus(status, statusStr);
    strncpy(albumStatus, statusStr.c_str(), maxLen - 1);
    albumStatus[maxLen - 1] = 0;
}

void md_ConvertFromAlbumType(TPAlbumType type, char *albumType, int maxLen)
{
    string typeStr;

    convertFromAlbumType(type, typeStr);
    strncpy(albumType, typeStr.c_str(), maxLen - 1);
    albumType[maxLen - 1] = 0;
}

float md_Similarity(const char *a, const char *b)
{
    return astrcmp(a, b);
}
}
