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

   $Id: tunepimp.h 8359 2006-08-07 20:34:50Z luks $

----------------------------------------------------------------------------*/
#ifndef __TUNEPIMP_H__
#define __TUNEPIMP_H__

#include <vector>
#include <map>

#include "defs.h"
#include "mutex.h"
#include "track.h"
#include "context.h"
#include "filecache.h"
#include "analyzer.h"
#include "write.h"
#include "readmeta.h"
#include "plugins.h"

class TPCallback
{
    public:

                  TPCallback(void) {};
        virtual  ~TPCallback(void) {};

        virtual   void notify(TunePimp *pimp, TPCallbackEnum, int fileId, TPFileStatus status) = 0;
        virtual   void status(TunePimp *pimp, const std::string &status) = 0;
};

class TunePimp
{
    public:

                  TunePimp(const string &appName, const std::string &appVersion, 
                           int startThreads = TP_THREAD_ALL, const char *pluginDir = NULL);
        virtual  ~TunePimp(void);

        // Setup functions -------------------------------------------------
        void      getVersion            (int &major, int &minor, int &rev);
        void      setMusicDNSClientId   (const std::string &clientId);
        string   &getMusicDNSClientId   (void);

        void      setServer             (const std::string &server, short port);
        void      setProxy              (const std::string &proxyServer, short proxyPort);
        void      getServer             (std::string &server, short &port);
        void      getProxy              (std::string &proxyServer, short &proxyPort);

        void      getSupportedExtensions(vector<string> &extList);

        void      setAnalyzerPriority   (TPThreadPriorityEnum pri);
        TPThreadPriorityEnum getAnalyzerPriority(void);

        // When a function fails, call this function to get an error string.
        void      getError              (std::string &error);

        // Call with true if you want to print server query/response info
        void      setDebug              (bool debug);
        bool      getDebug              (void);

        // Callback functions --------------------------------------------------
        void      setCallback           (TPCallback *callback);
      TPCallback *getCallback           (void);

        bool      getNotifyMessage      (TPCallbackEnum type, TPFileStatus status, int fileId);
        bool      getStatusMessage      (std::string &status);

        // File functions --------------------------------------------------

        // Returns a fileId number that can be used to reference the tracks later
        int       addFile               (const std::string &fileName, bool readMetadataNow = false);
        int       addDir                (const std::string &dirPath);
        void      remove                (int fileId);

        int       getNumFiles           (void);
        int       getNumUnsavedItems    (void);
        void      getFileIds            (std::vector<int> &ids);
        Track    *getTrack              (int fileId);
        void      releaseTrack          (Track *track);
        void      getTrackCounts        (std::map<TPFileStatus, int> &counts);

        // User feedback functions -----------------------------------------
        TPError   selectResult          (Track *track, int resultIndex);
        void      misidentified         (int fileId);
        void      identifyAgain         (int fileId);

        // Writing functions ----------------------------------
        int       getRecognizedFileList (int threshold, vector<int> &fileIds);
        bool      writeTags             (std::vector<int> *fileIds = NULL);

        // Config options ----------------------------------
        void      setRenameFiles          (bool rename);
        bool      getRenameFiles          (void);
        void      setMoveFiles            (bool move);
        bool      getMoveFiles            (void);
        void      setWriteID3v1           (bool writeID3v1);
        bool      getWriteID3v1           (void);
        void      setWriteID3v2_3         (bool writeID3v2_3);
        bool      getWriteID3v2_3         (void);
        std::string   &getFileNameEncoding     (void);
        void      setFileNameEncoding     (const std::string &encoding);
        void      setID3Encoding          (TPID3Encoding enc);
        TPID3Encoding getID3Encoding      (void);
        void      setClearTags            (bool clearTags);
        bool      getClearTags            (void);
        void      setFileMask             (const std::string &fileMask);
        std::string &  getFileMask             (void);
        void      setVariousFileMask      (const std::string &variousFileMask);
        std::string &  getVariousFileMask      (void);
        void      setNonAlbumFileMask     (const std::string &nonAlbumFileMask);
        std::string &  getNonAlbumFileMask     (void);
        void      setAllowedFileCharacters(const std::string &allowedFileCharacters);
        std::string &  getAllowedFileCharacters(void);
        void      setWinSafeFileNames     (bool winSafeFileNames);
        bool      getWinSafeFileNames     (void);
        void      setDestDir              (const std::string &destDir);
        std::string &  getDestDir              (void);
        void      setTopSrcDir            (const std::string &topSrcDir);
        std::string &  getTopSrcDir            (void);
        void      setAutoSaveThreshold    (int autoSaveThreshold);
        int       getAutoSaveThreshold    (void);
        void      setMaxFileNameLen       (int maxFileNameLen);
        int       getMaxFileNameLen       (void);
        void      setAutoRemoveSavedFiles (bool autoRemoveSavedFiles);
        bool      getAutoRemoveSavedFiles (void);

        // Stoopid windows socket setup functions --------------------------
#ifdef WIN32
        void      WSAInit               (void);
        void      WSAStop               (void);
#endif

        // This is public for easy access. Everyone should have access to it.
        Context           context;

    private:

        Plugins          *plugins;
        FileCache        *cache;
        Analyzer         *analyzer;
        WatchdogThread   *watchdog;
        WriteThread      *write;
        ReadThread       *read;
        std::string            server, proxyServer;
        short             port, proxyPort;
        std::string            err;
        std::vector<string>    extList;
        TPCallback       *callback;

    public:

        // These functions are for internal use only
        void     wake             (Track *track);
        void     setStatus        (const std::string &status);
        void     writeTagsComplete(bool error);
        void     trackRemoved     (int fileId);
        void     analyzerDied     (int analyzerFile);
        void     trackChangedStatus(Track *track);
};

#endif
