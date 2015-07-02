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

   $Id: thread.h 1316 2004-06-11 02:27:36Z robert $

----------------------------------------------------------------------------*/
#ifndef __THREAD_H_
#define __THREAD_H_

#include <windows.h>
#include <process.h>

#include "defs.h"

class Thread
{
      public:

                    Thread(bool createSuspended = false);
           virtual ~Thread(void);

           virtual bool  start(bool detach = false);
           virtual void  join (void);
           virtual void  kill (void);
           virtual void  terminate(void);
           virtual void *getId(void);
		   virtual void *getThreadId(void);
           virtual bool  isThreadAlive(void *threadId);

           virtual void  setPriority(TPThreadPriorityEnum pri);
           virtual TPThreadPriorityEnum  getPriority(void);

           static  DWORD WINAPI	threadMainStatic(void*); 
           virtual void			threadMain(void) = 0;

      private:

           bool          isRunning;
           HANDLE        thread;
           unsigned long threadId;
};

#endif
