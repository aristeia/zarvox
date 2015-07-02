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

   $Id: filecache.h 1264 2004-03-15 09:21:25Z robert $

----------------------------------------------------------------------------*/
#ifndef __FILECACHE_H__
#define __FILECACHE_H__

#include <vector>
#include <map>
#include <string>
using namespace std;

#include "mutex.h"
#include "track.h"

class TunePimp;

class FileCache
{
    public:

        FileCache(TunePimp *pimp);
       ~FileCache(void);

        // Returns a fileId
        int    add(const string &fileName);
        void   remove(int index);

        int    getNumItems(void);
        int    getNumUnsavedItems(void);
        void   getCounts(map<TPFileStatus, int> &counts);
        void   getFileIds(vector<int> &ids);
        int    getFileIdFromTrack(Track *);
        int    getRecognizedFileList (int threshold, vector<int> &fileIds);

        // For each tracks returned by the following functions release() needs to
        // be called in order to decrement the refcount
        Track *getTrack(int fileId);
        Track *getNextItem(TPFileStatus status);
        Track *getTrackFromFileName(const string &fileName);
        Track *getTrackFromTrackId(const string &trackId);
        Track *getTrack(const string &fileName);
        void   getTracksFromStatus(TPFileStatus status, vector<Track *> &tracks);

        void   release(Track *track);

    private:

        Mutex                               mutex;
        map<unsigned, pair<Track *, int> >  cache;
        map<Track *, int>                   xref;
        int                                 numUnsaved, serialNum;
        TunePimp                           *pimp;
};

#endif
