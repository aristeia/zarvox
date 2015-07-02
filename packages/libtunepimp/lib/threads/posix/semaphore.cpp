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

   $Id: semaphore.cpp 1192 2003-09-10 17:36:06Z robert $

----------------------------------------------------------------------------*/
#include <stdio.h>
#include <string.h>
#include <sys/time.h>
#include <stdlib.h>
#include <errno.h>
#include "semaphore.h"


Semaphore::Semaphore(const char *name)
{
    this->count = 1;
    pthread_cond_init(&semCond, NULL);
    pthread_mutex_init(&semMutex, NULL);
    if (name)
        this->name = strdup(name);
    else 
        this->name = NULL;
}

Semaphore::~Semaphore(void)
{
    pthread_mutex_destroy(&semMutex);
    pthread_cond_destroy(&semCond);
    if (name)
        free(name);
}

void Semaphore::signal(void)
{
    pthread_mutex_lock(&semMutex);
    count++;
    pthread_mutex_unlock(&semMutex);
    pthread_cond_signal(&semCond);
}

bool Semaphore::wait(void)
{
    pthread_mutex_lock(&semMutex);
    count--;
    while(count <= 0)
        pthread_cond_wait(&semCond, &semMutex);

    pthread_mutex_unlock(&semMutex);

    return true;
}

bool Semaphore::timedWait(int ms)
{
    struct timespec timeout;
    struct timeval  tv;
    bool            ret = true;
                                                                                
    pthread_mutex_lock(&semMutex);
                                                                                
    gettimeofday(&tv, NULL);
    timeout.tv_nsec = (tv.tv_usec * 1000) + (ms * 1000000);
    timeout.tv_sec = tv.tv_sec + (timeout.tv_nsec / 1000000000);
    timeout.tv_nsec %= 1000000000;
                                                                                
    count--;
    while (count <=0)
    {
        if (pthread_cond_timedwait(&semCond,&semMutex, &timeout) == ETIMEDOUT)
        {
            count++;
            ret = false;
            break;
        }
    }
                                                                                
    pthread_mutex_unlock(&semMutex);
            
    return ret;
}
