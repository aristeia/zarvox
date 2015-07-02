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

   $Id: context.h 8359 2006-08-07 20:34:50Z luks $

----------------------------------------------------------------------------*/
#ifndef CONTEXT_H
#define CONTEXT_H

#include "defs.h"

class TunePimp;

class Context
{
    public:

                 Context(void)
                   {
#if WIN32
                       fileMask = "%sortname\\%album\\%sortname-%album-%0num-%track";
                       variousFileMask = "Various Artists\\%album\\%album-%0num-%artist-%track";
                       nonAlbumFileMask = "%sortname\\%album\\%sortname-%track";
#else
                       fileMask = "%artist/%album/%artist-%album-%0num-%track";
                       variousFileMask = "Various Artists/%album/%album-%0num-%artist-%track";
                       nonAlbumFileMask = "%artist/%album/%artist-%track";
#endif
                       allowedFileCharacters = ""; // Allow all as per filesystem
                       destDir = "MyMusic";
                       topSrcDir = ".";
                       renameFiles = true;
                       moveFiles = true;
                       writeID3v1 = true;
                       autoSaveThreshold = 90;
                       debug = false;
                       clearTags = false;
                       winSafeFileNames = false;
                       pimp = NULL;
                       analyzerPriority = eNormal;
                       autoRemoveSavedFiles = false;
                       maxFileNameLen = -1;
                       writeID3v2_3 = false;
                       id3Encoding = eUTF8;
                       fileNameEncoding = "UTF-8";
                       clientId = "";
                   };

        virtual  ~Context(void) {};

        void      setDestDir (const std::string &destDir)
                    { this->destDir = destDir; };
        std::string   &getDestDir (void)
                    { return destDir; };
                
        void      setTopSrcDir (const std::string &topSrcDir)
                    { this->topSrcDir = topSrcDir; };
        std::string   &getTopSrcDir (void)
                    { return topSrcDir; };
                
        void      setFileMask (const std::string &fileMask)
                    { this->fileMask = fileMask; };
        std::string   &getFileMask (void)
                    { return fileMask; };
                
        void      setVariousFileMask (const std::string &variousFileMask)
                    { this->variousFileMask = variousFileMask; };
        std::string   &getVariousFileMask (void)
                    { return variousFileMask; };

        void      setNonAlbumFileMask (const std::string &nonAlbumFileMask)
                    { this->nonAlbumFileMask = nonAlbumFileMask; };
        std::string   &getNonAlbumFileMask (void)
                    { return nonAlbumFileMask; };
                
        void      setAllowedFileCharacters (const std::string &allowedFileCharacters)
                    { this->allowedFileCharacters = allowedFileCharacters; };
        std::string   &getAllowedFileCharacters (void)
                    { return allowedFileCharacters; };
                
        void      setWinSafeFileNames (bool winSafeFileNames)
                    { this->winSafeFileNames = winSafeFileNames; };
        bool      getWinSafeFileNames (void)
                    { return winSafeFileNames; };
                
        void      setRenameFiles (bool renameFiles)
                    { this->renameFiles = renameFiles; };
        bool      getRenameFiles (void)
                    { return renameFiles; };
                
        void      setMoveFiles (bool moveFiles)
                    { this->moveFiles = moveFiles; };
        bool      getMoveFiles (void)
                    { return moveFiles; };
                
        void      setWriteID3v1 (bool writeID3v1)
                    { this->writeID3v1 = writeID3v1; };
        bool      getWriteID3v1 (void)
                    { return writeID3v1; };
                
        void      setWriteID3v2_3 (bool writeID3v2_3)
                    { this->writeID3v2_3 = writeID3v2_3; };
        bool      getWriteID3v2_3 (void)
                    { return writeID3v2_3; };

        void      setID3Encoding (TPID3Encoding enc)
                    { this->id3Encoding = enc; };
        TPID3Encoding getID3Encoding (void)
                    { return id3Encoding; };
                
        void      setDebug (bool debug)
                    { this->debug = debug; };
        bool      getDebug (void)
                    { return debug; };
                
        void      setAutoSaveThreshold (int autoSaveThreshold)
                    { this->autoSaveThreshold = autoSaveThreshold; };
        int       getAutoSaveThreshold (void)
                    { return autoSaveThreshold; };
                
        void      setClearTags (bool clearTags)
                    { this->clearTags = clearTags; };
        bool      getClearTags (void)
                    { return clearTags; };
                
        void      setTunePimp (TunePimp *pimp)
                    { this->pimp = pimp; };
        TunePimp *getTunePimp (void)
                    { return pimp; };

        void      setAnalyzerPriority (TPThreadPriorityEnum pri)
                    { analyzerPriority = pri; }
        TPThreadPriorityEnum getAnalyzerPriority (void)
                    { return analyzerPriority; };

        void      setFileNameEncoding (const std::string &encoding)
                    { fileNameEncoding = encoding; };
        std::string   &getFileNameEncoding (void)
                    { return fileNameEncoding; };
                
        void      setMaxFileNameLen (int maxFileNameLen)
                    { this->maxFileNameLen = maxFileNameLen; };
        int       getMaxFileNameLen (void)
                    { return maxFileNameLen; };
                
        void      setAutoRemoveSavedFiles (bool autoRemoveSavedFiles)
                    { this->autoRemoveSavedFiles = autoRemoveSavedFiles; };
        bool      getAutoRemoveSavedFiles (void)
                    { return autoRemoveSavedFiles; };
                
        void      setMusicDNSClientId(const std::string &clientId)
                    { this->clientId = clientId; }

        std::string   &getMusicDNSClientId(void)
                    { return this->clientId; }

    private:

        std::string                fileMask, variousFileMask, 
                              nonAlbumFileMask, destDir, clientId,
                              topSrcDir, allowedFileCharacters, fileNameEncoding;
        bool                  moveFiles, renameFiles, debug, winSafeFileNames;
        bool                  writeID3v1, clearTags, autoRemoveSavedFiles, writeID3v2_3;
        int                   puidThreshold, autoSaveThreshold, minThreshold, maxFileNameLen;
        TPID3Encoding         id3Encoding;
        TunePimp             *pimp;
        TPThreadPriorityEnum  analyzerPriority;
};

#endif
