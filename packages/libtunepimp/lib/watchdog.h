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

   $Id: watchdog.h 1195 2003-09-12 20:11:41Z robert $

----------------------------------------------------------------------------*/
#ifndef __WATCHDOG_H__
#define __WATCHDOG_H__

#include "thread.h"
#include "semaphore.h"
#include "mutex.h"

class TunePimp;
class FileCache;

class WatchdogThread : public Thread
{
    public:

                 WatchdogThread(TunePimp     *tunePimp);
        virtual ~WatchdogThread(void);

        void     stop(void);
        void     threadMain(void);
        void     setAnalyzerThread(void *threadId);
        void     setAnalyzerTask(int fileId);

    private:

        TunePimp       *tunePimp;
        Semaphore      *sem;
        Mutex           mutex;
        bool            exitThread;
        void           *analyzerThread;
        int             analyzerFile;
};

#endif

