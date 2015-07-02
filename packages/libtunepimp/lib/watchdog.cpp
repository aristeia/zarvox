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

   $Id: watchdog.cpp 1279 2004-04-21 23:57:57Z robert $

----------------------------------------------------------------------------*/
#ifdef WIN32
#	if _MSC_VER == 1200
#		pragma warning(disable:4786)
#	endif
#else
#	include <unistd.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <signal.h>
#include <time.h>
#ifndef WIN32
#include <unistd.h>
#endif
#include <errno.h>
#include <string.h>

#include "watchdog.h"
#include "tunepimp.h"

#define DB printf("%s:%d\n", __FILE__, __LINE__);

#ifndef WIN32
extern "C"
{
    void handler(int sig)
    {
        signal(sig, handler);
        pthread_exit(NULL);
    }
}
#endif

//---------------------------------------------------------------------------

WatchdogThread::WatchdogThread(TunePimp *tunePimpArg) : Thread()
{
#ifndef WIN32
    signal(SIGSEGV, handler);
    signal(SIGBUS, handler);
    signal(SIGFPE, handler);
#endif

    tunePimp = tunePimpArg;
    analyzerThread = NULL;
    analyzerFile = -1;
    exitThread = false;
    sem = new Semaphore();
}

//---------------------------------------------------------------------------

WatchdogThread::~WatchdogThread(void)
{
    if (!exitThread)
    {
        exitThread = true;
        sem->signal();
        join();
    }
    delete sem;
}

//---------------------------------------------------------------------------

void WatchdogThread::stop(void)
{
    exitThread = true;
    sem->signal();
    join();
}

//---------------------------------------------------------------------------

void WatchdogThread::setAnalyzerThread(void *threadId)
{
    analyzerThread = threadId;
}

//---------------------------------------------------------------------------

void WatchdogThread::setAnalyzerTask(int fileId)
{
    mutex.acquire();
    analyzerFile = fileId;
    mutex.release();
}

//---------------------------------------------------------------------------

void WatchdogThread::threadMain(void)
{
    void *thread;
    int   file;

    for(; !exitThread;)
    {
        // Wait for 1/10th of a second.
        if (!sem->timedWait(100))
        {
            mutex.acquire();
            thread = analyzerThread;
            file = analyzerFile;
            mutex.release();

            if (thread == NULL)
                continue;

            if (!isThreadAlive(thread))
            {
                printf("Analyzer thread died!!!\n");
                mutex.acquire();
                analyzerThread = NULL;
                analyzerFile = -1;
                mutex.release();

                tunePimp->analyzerDied(file);
            }
        }
    }
}
