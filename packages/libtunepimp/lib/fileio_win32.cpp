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

   $Id: fileio_win32.cpp 7953 2006-06-27 21:56:47Z luks $

----------------------------------------------------------------------------*/

#include <assert.h>
#include <errno.h>
#include <string>
#include <windows.h>
#include <io.h>
#include <direct.h>
using namespace std;

#include "../config_win32.h"
#include "utf8/utf8.h"
#include "fileio.h"

static int uniqueId = 0;

#define DB printf("%s:%d\n", __FILE__, __LINE__);

static inline int
unicodeFileNames(void)
{
    static int canusewide = -1;
    if (canusewide == -1) {
	/* As per doc for ::GetVersion(), this is the correct test for
	   the Windows NT family. */
	canusewide = (GetVersion() < 0x80000000) ? 1 : 0;
    }
    return canusewide;
} 

static inline string
makeUnicodePath(const char *path)
{
    if ((path[0] == '\\') && (path[1] == '\\'))
        return string("\\\\?\\UNC\\") + string(path);
    else
        return string("\\\\?\\") + string(path);
}

#ifdef __cplusplus
extern "C"
{
#endif

static const char *dirSep = "\\";
static const char dirSepChar = '\\';

static int copyAndDelete(const char *from, const char *to, const char *encoding);
#define BUF_SIZE 4096

// For some reason MSVC++ can't find the prototype for this function
//int access(const char *, int);
#define F_OK 0

typedef struct _modeMapping
{
    char *code;
    int   flags;
    int   dwCreationDispositionIsALousyName;
} modeMapping;

const int numModeMappings = 6;
const modeMapping modeMappings[numModeMappings] =
{
    { "r",  GENERIC_READ,                 OPEN_EXISTING },
    { "r+", GENERIC_READ | GENERIC_WRITE, OPEN_EXISTING }, 
    { "w",  GENERIC_WRITE,                CREATE_ALWAYS },
    { "w+", GENERIC_READ | GENERIC_WRITE, CREATE_ALWAYS },
    { "a",  GENERIC_WRITE,                OPEN_ALWAYS   },
    { "a+", GENERIC_READ | GENERIC_WRITE, OPEN_ALWAYS   }
};

TFILE   *topen(const char *path, const char *modeArg, const char *encoding)
{
    HANDLE  fh = INVALID_HANDLE_VALUE;
    int     i;
    char   *ptr, mode[12];

    strcpy(mode, modeArg);
    ptr = strchr(mode, 'b');
    if (ptr)		
        memmove(ptr, ptr+1, strlen(ptr));

    for(i = 0; i < numModeMappings; i++)
        if (strcmp(mode, modeMappings[i].code) == 0)
            break;
    assert(i != numModeMappings);

    // NT/2k/XP
    if (unicodeFileNames())
    {
	string fileName = makeUnicodePath(path);
	LPWSTR wFileName = new WCHAR[fileName.size() + 1];
	MultiByteToWideChar(CP_UTF8, 0, fileName.c_str(), -1, wFileName, fileName.size() + 1);

	fh = CreateFileW(wFileName, modeMappings[i].flags, 0, NULL, 
			 modeMappings[i].dwCreationDispositionIsALousyName, 0, NULL);
	delete [] wFileName;
    }
    // Me/9x
    else
    {
	LPSTR fileName = NULL;
	if (!utf8_decode(path, &fileName))
	{
	    fh = CreateFileA(fileName, modeMappings[i].flags, 0, NULL, 
			     modeMappings[i].dwCreationDispositionIsALousyName, 0, NULL);
	    free(fileName);
	}
    }

    if (fh == INVALID_HANDLE_VALUE)
        return (TFILE*)NULL;

    if (strchr(mode, 'a'))
	SetFilePointer(fh, 0, NULL, FILE_END);

    return (TFILE *)fh;
}

size_t   tread(void *ptr, size_t size, size_t nmemb, TFILE *stream)
{
    DWORD numRead;
    if (nmemb == 0)
       return 0;

    ReadFile((HANDLE)stream, ptr, (DWORD)size * (DWORD)nmemb, &numRead, NULL);
    return numRead / (DWORD)size;
}

size_t   twrite(const void *ptr, size_t size, size_t nmemb, TFILE *stream)
{
    DWORD numRead;
    if (nmemb == 0)
       return 0;

    WriteFile((HANDLE)stream, ptr, (DWORD)size * (DWORD)nmemb, &numRead, NULL);
    return numRead / (DWORD)size;
}

int      tseek(TFILE *stream, long offset, int whence)
{
    DWORD newPos;
    newPos = SetFilePointer((HANDLE)stream, offset, NULL, whence);
    if (newPos == INVALID_SET_FILE_POINTER)
	return -1;
    return 0;
}

long     ttell(TFILE *stream)
{
    DWORD ret;
    ret = SetFilePointer((HANDLE)stream, 0, NULL, FILE_CURRENT);
    if (ret == INVALID_SET_FILE_POINTER)
	return -1;
    return ret;
}

int      tclose(TFILE *stream)
{
    return (int)CloseHandle((HANDLE)stream) - 1;
}

int      tflush(TFILE *stream)
{
    return (int)FlushFileBuffers((HANDLE)stream) - 1;
}

int      tunlink(const char *pathname, const char *encoding)
{
    int ret = 0;

    // NT/2k/XP
    if (unicodeFileNames())
    { 
	string newFileName = makeUnicodePath(pathname);
	LPWSTR wFileName = new WCHAR[newFileName.size() + 1];
	MultiByteToWideChar(CP_UTF8, 0, newFileName.c_str(), -1, wFileName, newFileName.size() + 1);
	ret = (int)DeleteFileW(wFileName);
	delete [] wFileName;
    }
    // Me/9x
    else
    {
	LPSTR fileName;
	if (!utf8_decode(pathname, &fileName))
	{
	    ret = (int)DeleteFileA(fileName);
	    free(fileName);
	}
    }

    return ret - 1;
}

int trename(const char *oldpath, const char *newpath, const char *encoding)
{
    int ret = 0;

    // NT/2k/XP
    if (unicodeFileNames())
    {
	string newFileName = makeUnicodePath(newpath);
	string oldFileName = makeUnicodePath(oldpath);
	LPWSTR wNewFileName = new WCHAR[newFileName.size() + 1];
	LPWSTR wOldFileName = new WCHAR[oldFileName.size() + 1];
	MultiByteToWideChar(CP_UTF8, 0, newFileName.c_str(), -1, wNewFileName, newFileName.size() + 1);
	MultiByteToWideChar(CP_UTF8, 0, oldFileName.c_str(), -1, wOldFileName, oldFileName.size() + 1);
	ret = MoveFileW(wOldFileName, wNewFileName);
	delete [] wNewFileName;
	delete [] wOldFileName;
    }
    // Me/9x
    else
    {
	LPSTR newFileName = NULL;
	LPSTR oldFileName = NULL;
	if (!utf8_decode(newpath, &newFileName))
	{
	    if (!utf8_decode(oldpath, &oldFileName))
	    {
		ret = MoveFileA(oldFileName, newFileName);
		free(oldFileName);
	    }
	    free(newFileName);
	}
    }

    if (!ret && GetLastError() == ERROR_FILE_EXISTS)
        errno = EEXIST;

    if (!ret && GetLastError() == ERROR_NOT_SAME_DEVICE)
        return copyAndDelete(oldpath, newpath, encoding);

    return (int)ret - 1;
}

int tmkdir(const char *pathname, const char *encoding)
{
    int ret = 0;

    // NT/2k/XP
    if (unicodeFileNames())
    { 
	string newFileName = makeUnicodePath(pathname);
	LPWSTR wFileName = new WCHAR[newFileName.size() + 1];
	MultiByteToWideChar(CP_UTF8, 0, newFileName.c_str(), -1, wFileName, newFileName.size() + 1);
	ret = (int)CreateDirectoryW(wFileName, NULL);
	delete [] wFileName;
    }
    // Me/9x
    else
    {
	LPSTR fileName;
	if (!utf8_decode(pathname, &fileName))
	{
	    ret = (int)CreateDirectoryA(fileName, NULL);
	    free(fileName);
	}
    }

    if (ret == 0 && GetLastError() == ERROR_ALREADY_EXISTS)
	ret = 1;

    return (int)ret - 1;
}

int trmdir(const char *pathname, const char *encoding)
{
    int ret = 0;

    // NT/2k/XP
    if (unicodeFileNames())
    { 
	string newFileName = makeUnicodePath(pathname);
	LPWSTR wFileName = new WCHAR[newFileName.size() + 1];
	MultiByteToWideChar(CP_UTF8, 0, newFileName.c_str(), -1, wFileName, newFileName.size() + 1);
	ret = (int)RemoveDirectoryW(wFileName);
	delete [] wFileName;
    }
    // Me/9x
    else
    {
	LPSTR fileName;
	if (!utf8_decode(pathname, &fileName))
	{
	    ret = (int)RemoveDirectoryA(fileName);
	    free(fileName);
	}
    }

    return (int)ret - 1;
}

int taccess(const char *pathname, int mode, const char *encoding)
{
    DWORD ret = INVALID_FILE_ATTRIBUTES;
    
    assert(mode == F_OK);

    // NT/2k/XP
    if (unicodeFileNames())
    {
	string newFileName = makeUnicodePath(pathname);
	LPWSTR wFileName = new WCHAR[newFileName.size() + 1];
	MultiByteToWideChar(CP_UTF8, 0, newFileName.c_str(), -1, wFileName, newFileName.size() + 1);
	ret = GetFileAttributesW(wFileName);
	delete [] wFileName;
    }
    // Me/9x
    else
    {
	LPSTR fileName;
	if (!utf8_decode(pathname, &fileName))
	{
	    ret = (int)GetFileAttributesA(fileName);
	    free(fileName);
	}
    }

    return (ret == INVALID_FILE_ATTRIBUTES) ? -1 : 0;
}

void tmktempname(const char *path, char *newPath, int newPathLen)
{
    char *ptr, *temp;

    temp = (char *)malloc(strlen(path) + 32);
    ptr = strrchr((char *)path, dirSepChar);
    if (ptr)
    {
        int len = (int)(ptr - path);
        strncpy(temp, path, len);
        temp[len] = 0;
    }
    else
        strcpy(temp, ".");

    strcat(temp, dirSep);
    sprintf(temp + strlen(temp), "libtp%d%d.temp", (int)GetCurrentProcessId(), uniqueId++);
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
