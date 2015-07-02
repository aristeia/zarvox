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

   $Id: dirsearch.cpp 1461 2006-01-16 15:08:55Z luks $

----------------------------------------------------------------------------*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../config.h"
#include "dirsearch.h"
#include "tunepimp.h"
#include "utf8/utf8util.h"

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/stat.h>
#include <unistd.h>
#include <sys/types.h>
#include <dirent.h>
#endif

DirSearch::DirSearch(TunePimp *pimp, const vector<string> &extList)
{
   this->extList = extList;
   this->pimp = pimp;
}

DirSearch::~DirSearch(void)
{
}

#ifdef WIN32

FileType DirSearch::checkFileType(const char *path, bool wide)
{
    unsigned type = (unsigned)-1;

    if (wide)
    {
	string fileName = string("\\\\?\\") + string(path);
	LPWSTR wFileName = new WCHAR[fileName.size() + 1];
	MultiByteToWideChar(CP_UTF8, 0, fileName.c_str(), -1, wFileName, fileName.size() + 1);
	type = (int)GetFileAttributesW(wFileName);
	delete [] wFileName;
    }
    else
    {
	LPSTR fileName = NULL;
	if (!utf8_decode(path, &fileName))
	{
	    type = (int)GetFileAttributesA(fileName);
	    free(fileName);
	}
    }
   
    if ((int)type < 0)
	return ePathNotFound;
    
    if (type & FILE_ATTRIBUTE_DIRECTORY)
	return eDir;
    
    if ((type & FILE_ATTRIBUTE_HIDDEN) ||
	(type & FILE_ATTRIBUTE_OFFLINE) ||
	(type & FILE_ATTRIBUTE_TEMPORARY))
	return eOther;
    
    return eFile;
}

int DirSearch::recurseDir(const char *path)
{
   union {
       WIN32_FIND_DATAW w;
       WIN32_FIND_DATAA a;
   } find;
   HANDLE             hFind = INVALID_HANDLE_VALUE;
   int                count = 0, j;
   char               newPath[MAX_PATH], savedPath[MAX_PATH];
   FileType           type;
   static bool        wide = GetVersion() < 0x80000000;
   
   pimp->setStatus(string("Searching ") + string(path));

   strcpy(newPath, path);
   if (newPath[strlen(newPath) - 1] == '\\')
      newPath[strlen(newPath) - 1] = 0;

   strcpy(savedPath, newPath);

   type = checkFileType(newPath, wide);
   
   /* if a path was specified, then add a \*.* */
   if (type == eDir)
      strcat(newPath, "\\*.*");

   if (wide)
   {
       string fileName = string("\\\\?\\") + string(newPath);
       LPWSTR wFileName = new WCHAR[fileName.size() + 1];
       MultiByteToWideChar(CP_UTF8, 0, fileName.c_str(), -1, wFileName, fileName.size() + 1);
       hFind = FindFirstFileW(wFileName, &find.w);
       delete [] wFileName;
   }
   else
   {
       LPSTR fileName = NULL;
       if (!utf8_decode(newPath, &fileName))
       {
	   hFind = FindFirstFileA(fileName, &find.a);
	   free(fileName);
       }

   }

   if (hFind == INVALID_HANDLE_VALUE)
       return -1;

   /* If its not a directory, then remove everything after the last slash */
   if (type != eDir)
   {
      char *ptr;

      ptr = strrchr(savedPath, '\\');
      if (ptr)
         *ptr = 0;
   }

   for(j = 0;; j++)
   {
       LPSTR fileName = NULL;

       if (wide)
       {
	   if (j > 0)
	       if (!FindNextFileW(hFind, &find.w))
		   break;

	   /* get file name in utf8 */
	   fileName = new CHAR[MAX_PATH];
	   WideCharToMultiByte(CP_UTF8, 0, find.w.cFileName, -1, fileName, MAX_PATH, NULL, NULL);
       }
       else
       {
	   if (j > 0)
	       if (!FindNextFileA(hFind, &find.a))
		   break;

	   if (utf8_encode(find.a.cFileName, &fileName))
	     continue;
       }

       /* Skip the . and .. dirs */
       if (strcmp(fileName, ".") == 0 ||
           strcmp(fileName, "..") == 0)
          continue;

       sprintf(newPath, "%s\\%s", savedPath, fileName);
       type = checkFileType(newPath, wide);
       
       if (type == eDir)
          count += recurseDir(newPath);

       if (type == eFile)
       {
           vector<string>::iterator   i;
           char                      *ptr;

           ptr = strrchr(newPath, '.');
           if (ptr == NULL)
               continue;

           for(i = extList.begin(); i != extList.end(); i++)
           {
               if (strcasecmp((*i).c_str(), ptr) == 0)
               { 
                   fileList.push_back(string(newPath));
		   count++;
                   break;
               }
           }
       }

       if (wide)
	   delete [] fileName;
       else
	   free(fileName);
   }
   FindClose(hFind);

   return count;
}


#else

// check the type and do the long name lookup on the file
FileType DirSearch::checkFileType(const char *path)
{
   struct stat sbuf;

   if (lstat(path, &sbuf) == 0)
   {
       if (S_ISCHR(sbuf.st_mode) || S_ISBLK(sbuf.st_mode) || 
           S_ISFIFO(sbuf.st_mode) || S_ISSOCK(sbuf.st_mode))
          return eOther;

       if (S_ISREG(sbuf.st_mode))
          return eFile;
       else
       if (S_ISDIR(sbuf.st_mode) && !S_ISLNK(sbuf.st_mode))
          return eDir;
       else
          return eOther;
   }
   else
       return ePathNotFound;
}

int DirSearch::recurseDir(const char *path)
{
   DIR           *dir;
   struct dirent *entry;
   char           newPath[1024];
   struct stat    sbuf;
   string           encoding;

   encoding = pimp->context.getFileNameEncoding();

   pimp->setStatus(string("Searching ") + string(path));
   dir = opendir(path);
   if (dir == NULL)
   {
       return 0;
   }

   for(;;)
   {
       entry = readdir(dir);
       if (!entry)
          break;

       /* Skip the . and .. dirs */
       if (strcmp(entry->d_name, ".") == 0 ||
           strcmp(entry->d_name, "..") == 0)
          continue;

       sprintf(newPath, "%s/%s", path, entry->d_name);
       if (lstat(newPath, &sbuf) == 0)
       {
           if (S_ISDIR(sbuf.st_mode) && !S_ISLNK(sbuf.st_mode))
           {
               recurseDir(newPath);
           }
           else
           if (S_ISREG(sbuf.st_mode))
           {
               vector<string>::iterator   i;
               char                      *ptr;

               ptr = strrchr(entry->d_name, '.');
               if (ptr == NULL)
                   continue;

               for(i = extList.begin(); i != extList.end(); i++)
               {
                   if (strcasecmp((*i).c_str(), ptr) == 0)
                   { 
                       fileList.push_back(utf8FromEncoding(string(newPath), encoding));
                       break;
                   }
               }
           }
       }
   }
   closedir(dir);

   return fileList.size();
}

#endif
