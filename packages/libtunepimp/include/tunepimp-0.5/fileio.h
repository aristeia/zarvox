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

   $Id: fileio.h 1402 2005-06-21 05:08:18Z robert $

----------------------------------------------------------------------------*/
#ifndef FILEIO_H
#define FILEIO_H

#include <stdio.h>

#ifdef __cplusplus
extern "C"
{
#endif

typedef unsigned long TFILE;

/* This fopen wrapper will take UTF-8 pathnames and properly call the 
 * right OS function to open a file ensuring that the right filename
 * encoding will be used to open the file.
 */
TFILE   *topen(const char *path, const char *mode, const char *encoding);
size_t   tread(void *ptr, size_t size, size_t nmemb, TFILE *stream);
size_t   twrite(const void *ptr, size_t size, size_t nmemb, TFILE *stream);
int      tseek(TFILE *stream, long offset, int whence);
long     ttell(TFILE *stream);
int      tclose(TFILE *fp);
int      tgetpos(TFILE *stream, fpos_t *pos);
int      tsetpos(TFILE *stream, fpos_t *pos);
int      tflush(TFILE *stream);
void     tclearerr(TFILE *stream);
int      teof(TFILE *stream);
 
int      tmkdir(const char *pathname, const char *encoding);
int      trmdir(const char *pathname, const char *encoding);
int      taccess(const char *pathname, int mode, const char *encoding);
int      tunlink(const char *pathname, const char *encoding);
int      trename(const char *oldpath, const char *newpath, const char *encoding);

void     tmktempname(const char *path, char *newPath, int newPathLen);

#ifdef __cplusplus
}
#endif

#endif
