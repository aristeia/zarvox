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

   $Id: thread.cpp 1212 2003-10-07 00:54:28Z robert $

----------------------------------------------------------------------------*/
#include "thread.h"

Thread::Thread(bool createSuspended)
{
    isRunning = false;
    threadId = 0;
    thread = (HANDLE)NULL;
}

Thread::~Thread(void)
{
}

bool Thread::start(bool detach)
{
    if (isRunning)
        return false;

    thread = (HANDLE)_beginthreadex(NULL, 0, (unsigned int (__stdcall *)(void *))Thread::threadMainStatic, 
                            this, 0, (unsigned int *)&threadId);
    if (!thread)
        return false;

    isRunning = true;

    return true;
}

void Thread::join(void)
{
    WaitForSingleObject(thread, INFINITE);
}

void Thread::kill(void)
{
    TerminateThread(thread, 0);
}

void Thread::terminate(void)
{
    _endthread();
}

void *Thread::getId(void)
{
    return (void *)thread;
}

void *Thread::getThreadId(void)
{
    return (void *)threadId;
}

bool Thread::isThreadAlive(void *threadId)
{
    return WaitForSingleObject((HANDLE)threadId, 0) == WAIT_TIMEOUT;
}

void Thread::setPriority(TPThreadPriorityEnum pri)
{
    switch(pri)
    {
        case eIdle:
            SetThreadPriority(thread, THREAD_PRIORITY_IDLE);
            break;
        case eLowest:
            SetThreadPriority(thread, THREAD_PRIORITY_LOWEST);
            break;
        case eLow:
            SetThreadPriority(thread, THREAD_PRIORITY_BELOW_NORMAL);
            break;
        case eNormal:
            SetThreadPriority(thread, THREAD_PRIORITY_NORMAL);
            break;
        case eHigh:
            SetThreadPriority(thread, THREAD_PRIORITY_ABOVE_NORMAL);
            break;
        case eHigher:
            SetThreadPriority(thread, THREAD_PRIORITY_HIGHEST);
            break;
        case eTimeCritical:
            SetThreadPriority(thread, THREAD_PRIORITY_TIME_CRITICAL);
            break;
    }
}

TPThreadPriorityEnum Thread::getPriority(void)
{
    int pri;
    
    pri = GetThreadPriority(thread);
    switch(pri)
    {
        case THREAD_PRIORITY_IDLE:
            return eIdle;
        case THREAD_PRIORITY_LOWEST:
            return eLowest;
        case THREAD_PRIORITY_BELOW_NORMAL:
            return eLow;
        case THREAD_PRIORITY_NORMAL:
            return eNormal;
        case THREAD_PRIORITY_ABOVE_NORMAL:
            return eHigh;
        case THREAD_PRIORITY_HIGHEST:
            return eHigher;
        case THREAD_PRIORITY_TIME_CRITICAL:
            return eTimeCritical;
    }

    return eNormal;
}

DWORD WINAPI	Thread::threadMainStatic(void*	ptr)
{
	Thread*	threadClass = reinterpret_cast< Thread* >( ptr );
    threadClass->threadMain();
    return 0;
}
