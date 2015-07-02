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

   $Id: readmeta.h 1331 2004-08-16 06:09:28Z robert $

----------------------------------------------------------------------------*/
#ifndef __READMETA_H__
#define __READMETA_H__

#include <string>
using namespace std;
#include "thread.h"
#include "semaphore.h"
#include "track.h"
#include "plugin.h"

class TunePimp;
class FileCache;
class Plugins;
class Track;

class ReadThread : public Thread
{
    public:
                 ReadThread(TunePimp       *tunePimp,
                            FileCache      *cache,
                            Plugins        *plugins);
        virtual ~ReadThread(void);

        void     wake(void);
        void     threadMain(void);

        bool     readMetadata(Track *track, bool calcDuration = true);

    private:

        void     parseFileName(const string &fileName, Metadata &data);
        void     trimWhitespace(string &field);

        TunePimp             *tunePimp;
        Plugins              *plugins;
        FileCache            *cache;
        bool                  exitThread;
        Semaphore            *sem;
};

#endif
 
