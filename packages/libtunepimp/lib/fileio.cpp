/*----------------------------------------------------------------------------

   libtunepimp -- The MusicBrainz tagging library.  
                  Let a thousand taggers bloom!
   
   Copyright (C) Robert Kaye 2003
   
   This file is part of libtunepimp.

   libtunepimp is free software you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation either version 2 of the License, or
   (at your option) any later version.

   libtunepimp is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with libtunepimp if not, write to the Free Software
   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

   $Id: fileio.cpp 9816 2008-04-22 08:06:09Z luks $

----------------------------------------------------------------------------*/

#include <assert.h>
#include <errno.h>
#include <string>
#include <cstring>
#include <cstdlib>
#ifndef WIN32
#include <unistd.h>
#endif
#include <sys/stat.h>
#include <sys/types.h>
using namespace std;

#include "utf8/utf8util.h"
#include "fileio.h"

static int uniqueId = 0;

#define DB printf("%s:%d\n", __FILE__, __LINE__);

#ifdef __cplusplus
extern "C"
{
#endif

static const char *dirSep = "/";
static const char dirSepChar = '/';

static int copyAndDelete(const char *from, const char *to, const char *encoding);
#define BUF_SIZE 4096

TFILE   *topen(const char *path, const char *mode, const char *encoding)
{
    return (TFILE *)fopen(utf8ToEncoding(path, encoding).c_str(), mode);
}

size_t   tread(void *ptr, size_t size, size_t nmemb, TFILE *stream)
{
    return fread(ptr, size, nmemb, (FILE *)stream);
}

size_t   twrite(const void *ptr, size_t size, size_t nmemb, TFILE *stream)
{
    return fwrite(ptr, size, nmemb, (FILE *)stream);
}

int      tseek(TFILE *stream, long offset, int whence)
{
    return fseek((FILE *)stream, offset, whence);
}

long     ttell(TFILE *stream)
{
    return ftell((FILE *)stream);
}

int      tclose(TFILE *stream)
{
    return fclose((FILE*)stream);
}

int      tflush(TFILE *stream)
{
    return fflush((FILE *)stream);
}

int      tunlink(const char *pathname, const char *encoding)
{
    return unlink(utf8ToEncoding(pathname, encoding).c_str());
}

int trename(const char *oldpath, const char *newpath, const char *encoding)
{
    int ret;

    ret = rename(utf8ToEncoding(oldpath, encoding).c_str(), utf8ToEncoding(newpath, encoding).c_str());
    if (ret && errno == EXDEV)
        return copyAndDelete(oldpath, newpath, encoding);

    return ret;
}

int tmkdir(const char *pathname, const char *encoding)
{
    return mkdir(utf8ToEncoding(pathname, encoding).c_str(), 0755);
}

int trmdir(const char *pathname, const char *encoding)
{
    return rmdir(utf8ToEncoding(pathname, encoding).c_str());
}

int taccess(const char *pathname, int mode, const char *encoding)
{
    assert(mode == F_OK);
    return access(utf8ToEncoding(pathname, encoding).c_str(), mode);
}

void tmktempname(const char *path, char *newPath, int newPathLen)
{
    char *ptr, *temp;

    temp = (char *)malloc(strlen(path) + 32);
    ptr = strrchr(path, dirSepChar);
    if (ptr)
    {
        int len = (int)(ptr - path);
        strncpy(temp, path, len);
        temp[len] = 0;
    }
    else
        strcpy(temp, ".");

    strcat(temp, dirSep);
    sprintf(temp + strlen(temp), "libtp%d%d.temp", (int)getpid(), uniqueId++);
    strncpy(newPath, temp, newPathLen - 1);
    newPath[newPathLen - 1] = 0;
    free(temp);
}

//---------------------------------------------------------------------------
static int copyAndDelete(const char *from, const char *to, const char *encoding)
{
    TFILE *in, *out;
    int    ret = 0;

    errno = 0;
    in = topen(from, "rb", encoding);
    if (in == NULL)
        return -1;

    out = topen(to, "wb", encoding);
    if (out == NULL)
    {
        tclose(in);
        return -1;
    }

    char *buf = new char[BUF_SIZE];
    for(;;)
    {
        int numRead = tread(buf, sizeof(char), BUF_SIZE, in);
        if (numRead <= 0)
            break;

        int numWritten = twrite(buf, sizeof(char), numRead, out);
        if (numWritten != numRead)
        {
            //err = string("Could not write file to destination directory. Disk full?");
            ret = -1;
            break;
        }
    }
    tclose(in);
    tclose(out);
    delete [] buf;

    if (ret == 0)
    {
        ret = tunlink(from, encoding);
        if (ret < 0)
        {
            //err = string("Could remove old file: '") + from + string("'.");
            tunlink(to, encoding);
        }
    }

    return ret;
}

#ifdef __cplusplus
}
#endif
