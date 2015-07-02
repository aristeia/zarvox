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

   $Id: track.h 8359 2006-08-07 20:34:50Z luks $

----------------------------------------------------------------------------*/
#ifndef __TRACK_H__
#define __TRACK_H__

#include <string>

#include "mutex.h"
#include "metadata.h"
#include "context.h"

class Track
{
    public:

                   Track(Context *context) 
                   { this->context = context; sim = 0; changed = false; };
        virtual ~Track(void) 
                   { };

        TPFileStatus getStatus      (void)                    {  return status; };
        void       setStatus        (const TPFileStatus status);

        void       getFileName      (std::string &fileName)        { fileName = this->fileName; };
        void       setFileName      (const std::string &fileName)  { this->fileName = fileName; };
 
        void       getPUID           (std::string &puid)             { puid = this->puid; };
        void       setPUID           (const std::string &puid);

        void       getLocalMetadata (Metadata &mdata)         { mdata = local; };
        void       setLocalMetadata (const Metadata &mdata);

        void       getServerMetadata(Metadata &mdata)         { mdata = server; };
        void       setServerMetadata(const Metadata &mdata);

        void       getError         (std::string &error)           { error = this->error; };
        void       setError         (const std::string &error)     { this->error = error; };
        
        int        getSimilarity    (void)                    { return sim; };
        bool       hasChanged       (void)                    { return changed; };
        void       setChanged       (void)                    { changed = true; };

        void       lock             (void);
        void       unlock           (void);

    private:

        TPFileStatus        status;
        std::string              fileName;
        std::string              puid;
        Metadata            local, server;
        std::string              error;
        bool                changed;
        int                 sim;
        Mutex               mutex;
        Context            *context;
};

#endif
