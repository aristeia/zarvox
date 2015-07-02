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

   $Id: dirsearch.h 1442 2006-01-07 19:19:38Z luks $

----------------------------------------------------------------------------*/
#ifndef __DIRSEARCH_H__
#define __DIRSEARCH_H__

#ifdef WIN32
#if _MSC_VER == 1200
#pragma warning(disable:4786)
#endif
#endif

#include <vector>
#include <string>
using namespace std;

enum FileType
{
    eFile,
    eDir,
    eOther,
    ePathNotFound
};

class TunePimp;
class DirSearch
{
   public:

                  DirSearch(TunePimp *pimp, const vector<string> &extList);
                 ~DirSearch(void);

         int      recurseDir(const char *path);
         void     getFiles(vector<string> &fileList) { fileList = this->fileList; };

   private:

#ifdef WIN32
         FileType        checkFileType(const char *path, bool wide = true);
#else
         FileType        checkFileType(const char *path);
#endif
         vector<string>  fileList;
         vector<string>  extList;
         TunePimp       *pimp;
};

#endif
