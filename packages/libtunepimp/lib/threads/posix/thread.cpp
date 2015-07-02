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

   $Id: thread.cpp 1427 2005-10-11 02:08:24Z luks $

----------------------------------------------------------------------------*/
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <sched.h>                                                                                              
#include <signal.h>                                                                                              
#include "thread.h"

#define DB printf("%s:%d\n", __FILE__, __LINE__);

const int threadPriorityRange = 100;

Thread::Thread(void)
{
    isRunning = false;
    threadId = 0;
    thread = (pthread_t)NULL;
}

Thread::~Thread(void)
{
}

bool Thread::start(bool detach)
{
    int ret;

    if (isRunning)
        return false;

    ret = pthread_create(&thread, NULL, Thread::threadMainStatic, this);
    if (ret)
        return false;

    isRunning = true;

    if (detach)
        pthread_detach(thread);

    return true;
}

void Thread::join(void)
{
    if (isRunning)
        pthread_join(thread, NULL);
}

void Thread::kill(void)
{
    if (isRunning)
        pthread_cancel(thread);
}

void Thread::terminate(void)
{
    pthread_exit(NULL);
}

void *Thread::getId(void)
{
    return (void *)thread;
}

bool Thread::isThreadAlive(void *threadId)
{
    return pthread_kill((pthread_t)threadId, 0) != ESRCH;
}

void  Thread::setPriority(TPThreadPriorityEnum pri)
{
}

TPThreadPriorityEnum Thread::getPriority(void)
{
    return eNormal;
}

void *Thread::threadMainStatic(void *threadArg)
{
    Thread *thread = (Thread *)threadArg;
    thread->threadMain();
    return NULL;
}
