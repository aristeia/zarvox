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

   $Id: mutex.h 1110 2003-06-23 09:27:19Z robert $

----------------------------------------------------------------------------*/
#ifndef __MUTEX_H__
#define __MUTEX_H__

#include <pthread.h>

class Mutex
{
      public:

                    Mutex(void);
           virtual ~Mutex(void);

           virtual void acquire(void);
           virtual void release(void);

      private:

           pthread_t       owner;
           pthread_mutex_t mutex;
           pthread_cond_t  cond;
           int             busyCount;
};

#endif
