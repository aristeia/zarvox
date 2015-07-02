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

   $Id: filecache.cpp 1311 2004-05-29 23:47:46Z robert $

----------------------------------------------------------------------------*/
#ifdef WIN32
#if _MSC_VER == 1200
#pragma warning(disable:4786)
#endif
#endif

#include "filecache.h"
#include "tunepimp.h"

// Speedup notes:
//   Add reverse indexes on fileName, track id
//   Create given a state, return all items in that state.
//   Keep count of unsaved items

FileCache::FileCache(TunePimp *pimp)
{
    numUnsaved = 0;
    serialNum = 0;
    this->pimp = pimp;
}

FileCache::~FileCache(void)
{
}

int FileCache::add(const string &fileName)
{
    map<unsigned, pair<Track *, int> >::iterator  i;
    Track                                   *track = NULL;
    string                                   temp;
    int                                      ret;
    pair<Track *, int>                       p;

    mutex.acquire();
    for(i = cache.begin(); i != cache.end(); i++)
    {
        (*i).second.first->getFileName(temp);
        if (temp == fileName)
        {
            ret = (*i).first;
            mutex.release();
            return ret;
        }
    }

    track = new Track(&pimp->context);
    track->setStatus(eMetadataRead);
    track->setFileName(fileName);

    p.first = track;
    p.second = 0;
    cache[serialNum] = p;
    xref[track] = serialNum++;

    mutex.release();

    return serialNum - 1;
}


void FileCache::getFileIds(vector<int> &ids)
{
    map<unsigned, pair<Track *, int> >::iterator  i;

    ids.clear();
    mutex.acquire();
    for(i = cache.begin(); i != cache.end(); i++)
        ids.push_back((*i).first);

    mutex.release();
}

int FileCache::getFileIdFromTrack(Track *track)
{
    map<Track *, int>::iterator j;
    int                         fileId = -1;

    mutex.acquire();

    j = xref.find(track);
    if (j != xref.end())
        fileId = (*j).second;

    mutex.release();

    return fileId;
}

int FileCache::getNumItems(void)
{
    int count;

    mutex.acquire();
    count = cache.size();
    mutex.release();

    return count;
}

// TODO: Optimize the next two function by keeping a mutexed counter
int FileCache::getNumUnsavedItems(void)
{
    map<unsigned, pair<Track *, int> >::iterator  i;
    int                                      count = 0;

    mutex.acquire();
    for(i = cache.begin(); i != cache.end(); i++)
        if ((*i).second.first->getStatus() == eRecognized ||
			(*i).second.first->getStatus() == eError)
        {
            if ((*i).second.first->hasChanged())
                count++;
        }
    mutex.release();

    return count;
}

// An array of hash maps to index all the counts for the next two functions
void FileCache::getCounts(map<TPFileStatus, int> &counts)
{
    map<unsigned, pair<Track *, int> >::iterator  i;

    mutex.acquire();
    for(i = cache.begin(); i != cache.end(); i++)
        counts[(*i).second.first->getStatus()]++;
    mutex.release();
}

void FileCache::getTracksFromStatus(TPFileStatus status, vector<Track *> &tracks)
{
    map<unsigned, pair<Track *, int> >::iterator  i;

    tracks.clear();
    mutex.acquire();
    for(i = cache.begin(); i != cache.end(); i++)
        if ((*i).second.first->getStatus() == status)
        {
            (*i).second.second++;
            tracks.push_back((*i).second.first);
        }
    mutex.release();
}

int FileCache::getRecognizedFileList (int threshold, vector<int> &fileIds)
{
    map<unsigned, pair<Track *, int> >::iterator  i;
    int                                      count = 0;

    fileIds.clear();
    mutex.acquire();
    for(i = cache.begin(); i != cache.end(); i++)
    {
        if ((*i).second.first->getStatus() == eRecognized)
        {
            fileIds.push_back((*i).first);
            if ((*i).second.first->getSimilarity() < threshold)
                count++;
        }
    }

    mutex.release();
    return count;
}

void FileCache::remove(int index)
{
    map<unsigned, pair<Track *, int> >::iterator  i;

    mutex.acquire();

    i = cache.find(index);
    if (i != cache.end())
    {
        if ((*i).second.second == 0)
            cache.erase(i);
        else
        {
            Track *track;

            track = (*i).second.first;
            track->lock();
            track->setStatus(eDeleted);
            track->unlock();
        }
    }
    mutex.release();
}
Track *FileCache::getNextItem(TPFileStatus status)
{
    map<unsigned, pair<Track *, int> >::iterator  i, saved = cache.end();
    Track                                   *track = NULL;
    unsigned                                 id = 0xFFFFFFFF;
    string temp;

    mutex.acquire();
    for(i = cache.begin(); i != cache.end(); i++)
        if ((*i).second.first->getStatus() == status)
		{			
			if (saved == cache.end() || id > (unsigned)(*i).first)
			{
				id = (*i).first;
				saved = i;
			}
		}

    if (saved != cache.end())
    {
        (*saved).second.second++;
        track = (*saved).second.first;
    }
    mutex.release();

    return track;
}

// This will need a reverse index on name
Track *FileCache::getTrackFromFileName(const string &fileName)
{
    map<unsigned, pair<Track *, int> >::iterator  i;
    Track                                   *track = NULL;
    string                                   temp;

    mutex.acquire();
    for(i = cache.begin(); i != cache.end(); i++)
    {
        (*i).second.first->getFileName(temp);
        if (temp == fileName)
        {
            (*i).second.second++;
            track = (*i).second.first;
            break;
        }
    }
    mutex.release();

    return track;
}

// reverse index on trackId
Track *FileCache::getTrackFromTrackId(const string &trackId)
{
    map<unsigned, pair<Track *, int> >::iterator  i;
    Track                                   *track = NULL;
    Metadata                                 data;

    mutex.acquire();
    for(i = cache.begin(); i != cache.end(); i++)
    {
        (*i).second.first->getServerMetadata(data);
        if (data.trackId == trackId)
        {
            (*i).second.second++;
            track = (*i).second.first;
            break;
        }
    }
    mutex.release();

    return track;
}

Track *FileCache::getTrack(int fileId)
{
    map<unsigned, pair<Track *, int> >::iterator  i;
    Track                       *track = NULL;

    mutex.acquire();

    i = cache.find(fileId);
    if (i != cache.end())
    {
        (*i).second.second++;
        track = (*i).second.first;
    }

    mutex.release();

    return track;
}

void FileCache::release(Track *track)
{
    map<unsigned, pair<Track *, int> >::iterator  i;
    map<Track *, int>::iterator              j;
    TPFileStatus                               status;
    int                                      index;

    mutex.acquire();

    j = xref.find(track);
    if (j != xref.end())
    {
        index = (*j).second;

        i = cache.find(index);
        if (i != cache.end())
        {
            (*i).second.second--;
            if ((*i).second.second == 0)
            {
                track->lock();
                status = track->getStatus();
                track->unlock();

                if (status == eDeleted)
                {
                    cache.erase(i);
                    xref.erase(j);        
                    pimp->trackRemoved(index);
                }
            }
        }
    }

    mutex.release();
}

#if 0
void FileCache::dump(void)
{
    map<unsigned, pair<Track *, int> >::iterator  i;
    Track                                   *track = NULL;
	string                                   fileName;

    mutex.acquire();
    for(i = cache.begin(); i != cache.end(); i++)
    {
        track = (*i).second.first;
        track->getFileName(fileName);
    }
    mutex.release();
}
#endif
