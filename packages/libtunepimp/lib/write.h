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

   $Id: write.h 7216 2006-04-14 23:10:49Z robert $

----------------------------------------------------------------------------*/
#ifndef WRITE_H
#define WRITE_H

#include "thread.h"
#include "semaphore.h"
#include "track.h"
#include "context.h"
#include "plugins.h"

class TunePimp;
class FileCache;

class FileNameMaker
{
    public:

                 FileNameMaker(Context *context) 
                 { this->context = context; }
        virtual ~FileNameMaker(void) {};

        void     makeNewFileName(const Metadata &data,
                                 string         &fileName,
                                 int             index);

        string   extractFileExt (const string &path);
        string   extractFileName(const string &path);
        string   extractFilePath(const string &file);
        string   extractFileBase(const string &file);
        string   extractVolume  (const string &file);

    protected:

	void     toLower(string &text);
	void     toUpper(string &text);

        const string  sanitize     (const string &str);
        void          trimToMaxSize(string &name);
	string        shortenString(const string &in, int &len);

        Context *context;
};

class WriteThread : public Thread, FileNameMaker
{
    public:

                 WriteThread(TunePimp     *tunePimp,
                             FileCache    *cache,
                             Plugins      *plugins);
        virtual ~WriteThread(void);
        void     wake       (void);
        void     threadMain (void);

    private:

        bool     writeTrack     (Track *track, const Metadata &data);
        bool     createPath     (const string &path);
        void     cleanPath      (const string &pathArg);

        unsigned long fileOpenTest (const string &fileName);
        bool          diskSpaceTest(const string &fileName, 
                                    unsigned long fileSize);

        TunePimp       *tunePimp;
        FileCache      *cache;
        bool            exitThread;
        Semaphore      *sem;
        Plugins        *plugins;
};

#endif
