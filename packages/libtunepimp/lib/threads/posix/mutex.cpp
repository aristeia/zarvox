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

   $Id: mutex.cpp 1110 2003-06-23 09:27:19Z robert $

----------------------------------------------------------------------------*/
#include <pthread.h>
#include <string.h>
#include "mutex.h"

Mutex::Mutex()
{
    pthread_mutexattr_t attribGoToJail;
    busyCount = 0;
    owner = 0;

    memset(&mutex, 0, sizeof(pthread_mutex_t));
    pthread_mutexattr_init(&attribGoToJail);
    pthread_cond_init(&cond, NULL);
    pthread_mutex_init(&mutex, &attribGoToJail);
    pthread_mutexattr_destroy(&attribGoToJail);
}

Mutex::~Mutex(void)
{
    pthread_mutex_destroy(&mutex);
    pthread_cond_destroy(&cond);
}

void Mutex::acquire(void)
{
    pthread_mutex_lock(&mutex);

    if (busyCount != 0)
    {
        if (owner != pthread_self())
        {
            for(; busyCount != 0;)
                pthread_cond_wait(&cond, &mutex);
        }
    }

    owner = pthread_self();
    busyCount++;
    pthread_mutex_unlock(&mutex);
}

void Mutex::release(void)
{
    int busy;

    pthread_mutex_lock(&mutex);
    busy = --busyCount;
    pthread_mutex_unlock(&mutex);

    if (busy == 0)
        pthread_cond_signal(&cond);
}
