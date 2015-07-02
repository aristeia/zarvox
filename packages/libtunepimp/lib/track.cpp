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

   $Id: track.cpp 7216 2006-04-14 23:10:49Z robert $

----------------------------------------------------------------------------*/
#include "../config.h"
#include "track.h"
#include "tunepimp.h"
#include "write.h"

void Track::setStatus(const TPFileStatus status) 
{ 
    this->status = status; 
    context->getTunePimp()->trackChangedStatus(this); 
}

void Track::setLocalMetadata(const Metadata &data)
{
    MetadataCompare comp;

    local = data;
    sim = comp.compare(server, local);
    changed = !(server == local);

    if (!changed && (context->getRenameFiles() || context->getMoveFiles()))
    {
        FileNameMaker maker(context);
        string        newName;

        newName = fileName;
        maker.makeNewFileName(local, newName, 0);
#ifdef WIN32
        if (stricmp(newName.c_str(), fileName.c_str()))
#else
        if (strcmp(newName.c_str(), fileName.c_str()))
#endif
            changed = true;
    }
}

void Track::setServerMetadata(const Metadata &data)
{
    MetadataCompare comp;

    server = data;
    sim = comp.compare(server, local);
    changed = !(server == local);

    if (!changed && (context->getRenameFiles() || context->getMoveFiles()))
    {
        FileNameMaker maker(context);
        string        newName;

        newName = fileName;
        maker.makeNewFileName(server, newName, 0);
#ifdef WIN32
        if (stricmp(newName.c_str(), fileName.c_str()))
#else
        if (strcmp(newName.c_str(), fileName.c_str()))
#endif
            changed = true;
    }
}

void Track::setPUID(const string &puid)
{ 
    this->puid = puid; 
}

void Track::lock(void)
{
    mutex.acquire();
}

void Track::unlock(void)
{
    mutex.release();
}
