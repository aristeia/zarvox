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

   $Id: semaphore.h 1191 2003-09-09 23:58:26Z robert $

----------------------------------------------------------------------------*/
#ifndef __SEMAPHORE_H__
#define __SEMAPHORE_H__

#include <pthread.h>

class Semaphore
{
     public:

                     Semaphore(const char *name = NULL);
             virtual ~Semaphore(void);

             virtual void signal      (void);
             virtual bool wait        (void);
             virtual bool timedWait   (int ms); // time in milliseconds

     private:

             int             count;
             pthread_mutex_t semMutex;
             pthread_cond_t  semCond;
             char            *name;
};

#endif
