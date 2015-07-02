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

   $Id: analyzer.h 8359 2006-08-07 20:34:50Z luks $

----------------------------------------------------------------------------*/
#ifndef __ANALYZER_H__
#define __ANALYZER_H__

#include "thread.h"
#include "semaphore.h"
#include "track.h"
#include "plugin.h"

#define ANALYZER_REDO_STRING "<redo>"

enum PUIDResult
{
    eOk,
    eFileNotFound,
    eDecodeError,
    eCannotConnect,
    eOutOfMemory,
    eNoPUID,
    eNoClientId,
    eOtherError
};

class TunePimp;
class FileCache;
class SubmitInfo;
class WatchdogThread;
class Plugins;
class Track;

class Analyzer : public Thread
{
    public:
                 Analyzer(TunePimp       *tunePimp,
                          Plugins        *plugins,
                          FileCache      *cache,
                          WatchdogThread *watchdog);
        virtual ~Analyzer(void);

        void     wake(void);
        void     threadMain(void);

        void     setProxy(const std::string &proxyServer, short proxyPort)
                  {
                       this->proxyServer = proxyServer;
                       this->proxyPort = proxyPort;
                  };

    private:

        PUIDResult calculatePUID(Plugin *plugin, const std::string &fileName, std::string &err, 
                               std::string &puidId, unsigned long &duration, Metadata &mdata);
        void      setError(Track *track, PUIDResult retVal);

        TunePimp             *tunePimp;
        Plugins              *plugins;
        FileCache            *cache;
        bool                  exitThread;
        Semaphore            *sem;
        unsigned              lastWake;
        SubmitInfo           *submitInfo;
        std::string                proxyServer;
        short                 proxyPort;
        WatchdogThread       *dog;
};

#endif
 
