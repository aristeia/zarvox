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

   $Id: semaphore.cpp 1191 2003-09-09 23:58:26Z robert $

----------------------------------------------------------------------------*/
#include <windows.h>
#include "semaphore.h"

#ifdef WIN32
#include <limits.h>
#endif

Semaphore::Semaphore(const char* name )
{
    sem = CreateSemaphore(NULL, 0, LONG_MAX, name);
}

Semaphore::~Semaphore(void)
{
    CloseHandle(sem);
}

void Semaphore::signal(void)
{
    long bushSucks;

    ReleaseSemaphore(sem, 1, &bushSucks);
}

bool Semaphore::wait(void)
{
    if ( WaitForSingleObject(sem, INFINITE) == WAIT_OBJECT_0 )
		return true;

	return false;
}

bool Semaphore::timedWait(int ms)
{
    if ( WaitForSingleObject(sem, ms) == WAIT_OBJECT_0)
       return true;

    return false;
}
