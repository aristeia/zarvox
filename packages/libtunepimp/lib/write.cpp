/*i----------------------------------------------------------------------------

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

   $Id: write.cpp 8421 2006-08-14 20:47:24Z luks $

----------------------------------------------------------------------------*/
#ifdef WIN32
#  if _MSC_VER == 1200
#       pragma warning(disable:4786)
#   endif
#  include <io.h>
#  include <direct.h>
#else
#  include <unistd.h>
#  include <sys/stat.h>
#  include <sys/types.h>
#  include <fcntl.h>
#  if defined(__APPLE__) || defined(__NetBSD__) || defined(__FreeBSD__) || defined(__OpenBSD__) || defined(__DragonFly__)
#    include <sys/param.h>
#    include <sys/mount.h>
#    if (defined(__NetBSD__) && __NetBSD_Version__ >= 299000900)
#      define HAVE_STATVFS 1
#    endif
#  else
#    include <sys/vfs.h>
#  endif
#endif


#include <ctype.h>
#include <errno.h>
#include <algorithm>

#include "../config.h"
#include "write.h"
#include "tunepimp.h"
#include "fileio.h"
#include "utf8/utf8util.h"

#if defined(HAVE_STATVFS)
#  define statfs statvfs
#  define f_bsize f_frsize
#endif

#ifdef WIN32
const char *dirSep = "\\";
const char dirSepChar = '\\';
const char *disallowedFileNameChars = "\"*/:<>?|";
#else
const char *dirSep = "/";
const char dirSepChar = '/';
const char *disallowedFileNameChars = "\"*:<>?|";
#endif

#define DB printf("%s:%d\n", __FILE__, __LINE__);

const int   numRepVars = 21;
const char *repVars[numRepVars] = {"%abc3", "%artist", "%country", "%day",
                                   "%format", "%l", "%month", "%0num", "%num",
                                   "%sortname", "%status", "%track", "%type", "%u", "%year", "%abc2", "%abc",
                                   "%albumartistsortname", "%albumartist", "%albumtracks", "%album"};

/* This set of variables removes the %abc2 and %abc3 that are made redundant by the %#%abc notation.
 * Removing these will break backward compatibility with the older tagger.
const int   numRepVars = 16;
const char *repVars[numRepVars] = {"%abc", "%album", "%artist", "%country", "%day",
                                   "%format", "%l", "%month", "%0num", "%num",
                                   "%sortname", "%status", "%track", "%type", "%u", "%year"};
*/

//---------------------------------------------------------------------------

void FileNameMaker::toLower(string &text)
{   
    transform(text.begin(), text.end(), text.begin(), (int(*)(int)) tolower);
}

void FileNameMaker::toUpper(string &text)
{   
    transform(text.begin(), text.end(), text.begin(), (int(*)(int)) toupper);
}

void FileNameMaker::makeNewFileName(const Metadata &dataArg,
                                    string         &fileName,
                                    int             index)
{
    Metadata          data = dataArg;
    string            name, origPath, origFile, ext, allowedFileChars, rep;
    string::size_type i;
    int               numCharsLeft, varCount = 0, varLen;

    origPath = extractFilePath(fileName);
    origFile = extractFileName(fileName);
    ext = extractFileExt(fileName);
    if (data.variousArtist)
        name = context->getVariousFileMask();
    else if (data.nonAlbum)
        name = context->getNonAlbumFileMask();
    else
        name = context->getFileMask();

    allowedFileChars = context->getAllowedFileCharacters();

    if (data.sortName.empty())
        data.sortName = data.artist;

    if (data.albumArtist.empty())
        data.albumArtist = data.album;

    if (data.albumArtistSortName.empty())
        data.albumArtistSortName = data.sortName;

    numCharsLeft = context->getMaxFileNameLen() - ext.length();
    if (numCharsLeft > 0)
    {
        if (context->getMoveFiles())
            numCharsLeft -= context->getDestDir().length() + 1;
        else
            numCharsLeft -= origPath.length() + 1;

        int varLength = 0;
        // Preparse the file spec and see how to allocate space to ensure everything
        // fits into the space we have for a filename.
        for(i = 0; i < name.length(); i++)
        {
            if (name[i] != '%')
            {
                numCharsLeft--;
                continue;
            }

            bool varFound = false;
            for(int j = 0; j != numRepVars && !varFound; j++)
            {
                char num[10];

                if (strncmp(name.c_str() + i, repVars[j], strlen(repVars[j])) == 0)
                {
                    switch(j)
                    {
                        case 0:  // abc3
                            numCharsLeft -= 3;
                            varFound = true;
                            varLength = 0;
                            break;
                        /* this one should replace the one above in the future
                        case 0:  // abc
                            if (varLength > 0)
                                numCharsLeft -= varLength;
                            else
                                varCount++;
                            varFound = true;
                            varLength = 0;
                            break;
                        */
                        case 19:  // albumtracks
                            sprintf(num, "%d", data.totalInSet);
                            numCharsLeft -= strlen(num);
                            varFound = true;
                            varLength = 0;
                            break;
                        case 20:  // album
                            if (varLength > 0)
                                numCharsLeft -= varLength;
                            else
                                varCount++;
                            varFound = true;
                            varLength = 0;
                            break;
                        case 1:  // artist
                            if (varLength > 0)
                                numCharsLeft -= varLength;
                            else
                                varCount++;
                            varFound = true;
                            varLength = 0;
                            break;
                        case 2:  // country
                            numCharsLeft -= 2;
                            varFound = true;
                            varLength = 0;
                            break;
                        case 3:  // day
                            numCharsLeft -= 2;
                            varFound = true;
                            varLength = 0;
                            break;
                        case 4:  // format
                            numCharsLeft -= data.fileFormat.length();
                            varFound = true;
                            varLength = 0;
                            break;
                        case 5:  // l (lowercase)
                            varFound = true;
                            break;
                        case 6:  // month
                            numCharsLeft -= 2;
                            varFound = true;
                            varLength = 0;
                            break;
                        case 7:  // 0num
                            numCharsLeft -= 2;
                            varFound = true;
                            varLength = 0;
                            break;
                        case 8:  // num
                            sprintf(num, "%d", data.trackNum);
                            numCharsLeft -= strlen(num);
                            varFound = true;
                            varLength = 0;
                            break;
                        case 9: // sortname
                            if (varLength > 0)
                                numCharsLeft -= varLength;
                            else
                                varCount++;
                            varFound = true;
                            varLength = 0;
                            break;
                        case 10: // status
                            {
                                if (varLength > 0)
                                    numCharsLeft -= varLength;
                                else
                                {
                                    string status;
                                    convertFromAlbumStatus(data.albumStatus, status);
                                    numCharsLeft -= status.length();
                                }
                                varFound = true;
                                varLength = 0;
                                break;
                            }
                        case 11: // track
                            if (varLength > 0)
                                numCharsLeft -= varLength;
                            else
                                varCount++;
                            varFound = true;
                            varLength = 0;
                            break;
                        case 12: // type
                            {
                                if (varLength > 0)
                                    numCharsLeft -= varLength;
                                else
                                {
                                    string type;
                                    convertFromAlbumType(data.albumType, type);
                                    numCharsLeft -= type.length();
                                }
                                varFound = true;
                                varLength = 0;
                                break;
                            }
                        case 13: // u (uppercase)
                            varFound = true;
                            break;
                        case 14: // year
                            numCharsLeft -= 4;
                            varFound = true;
                            varLength = 0;
                            break;
                        /* the next two should be removed in the future */
                        case 15:  // abc2
                            numCharsLeft -= 2;
                            varFound = true;
                            varLength = 0;
                            break;
                        case 16:  // abc
                            numCharsLeft -= 1;
                            varFound = true;
                            varLength = 0;
                            break;
                        case 18:  // albumartist
                        case 17:  // albumartistsortname
                            if (varLength > 0)
                                numCharsLeft -= varLength;
                            else
                                varCount++;
                            varFound = true;
                            varLength = 0;
                            break;
                    }
                    i += strlen(repVars[j]);
                }
            }
            if (!varFound)
            {
                printf("Found modifier\n");
                /* variable not found, yet we have a "%"
                 * let's see if the user wants to "limit" the amount of chars
                 * in the next variable */
                if (atoi(name.substr(i + 1, 1).c_str()) > 0 && atoi(name.substr(i + 1, 1).c_str()) <= 9)
                {
                    /* seems like the user wants a limited amount of chars
                     * in next variable */
                    varLength = atoi(name.substr(i + 1, 1).c_str());
                    i++;
                }
            }
        }
    }
    else
    {
        numCharsLeft = 999999999;
        varCount = 100;
    }

    bool lowercase = false;
    bool uppercase = false;
    int varLength = 0;
    for(i = 0; i < name.length(); i++)
    {
        if (name[i] != '%')
        {  
            numCharsLeft--;
            lowercase = false;
            uppercase = false;
            continue;
        }

        bool varFound = false;
        for(int j = 0; j != numRepVars && !varFound; j++)
        {
            char num[10];

            if (strncmp(name.c_str() + i, repVars[j], strlen(repVars[j])) == 0)
            {
                switch(j)
                {
                    case 0:  // abc3
                        if (data.variousArtist)
                            rep = data.album.substr(0, 3);
                        else
                            rep = data.sortName.substr(0, 3);
                        varFound = true;
                        varLength = 0;
                        break;
                    /* this one should replace the one above in the future
                    case 0:  // abc
                        if (varLength > 0)
                            if (data.variousArtist)
                                rep = data.album.substr(0, varLength);
                            else
                                rep = data.sortName.substr(0, varLength);
                        else
                        {
                            varLen = numCharsLeft / varCount;
                            varCount--;
                            if (data.variousArtist)
                                rep = data.album;
                            else
                                rep = data.sortName;
                            numCharsLeft -= varLen;
                        }
                        varFound = true;
                        varLength = 0;
                        break;
                    */
                    case 19:  // albumtracks
                        sprintf(num, "%d", data.totalInSet);
                        rep = string(num);
                        varFound = true;
                        varLength = 0;
                        break;
                    case 20:  // album
                        if (varLength > 0)
                            rep = data.album.substr(0, varLength);
                        else
                        {
                            varLen = numCharsLeft / varCount;
                            varCount--;
                            rep = data.album;
                        }
                        varFound = true;
                        varLength = 0;
                        break;
                    case 1:  // artist
                        if (varLength > 0)
                            rep = data.artist.substr(0, varLength);
                        else
                        {
                            varLen = numCharsLeft / varCount;
                            varCount--;
                            rep = data.artist;
                        }
                        varFound = true;
                        varLength = 0;
                        break;
                    case 2:  // country
                        rep = data.releaseCountry;
                        if (rep.length() == 0)
                            rep = "__";
                        varFound = true;
                        varLength = 0;
                        break;
                    case 3:  // day
                        sprintf(num, "%02d", data.releaseDay);
                        rep = string(num);
                        varFound = true;
                        varLength = 0;
                        break;
                    case 4:  // format
                        rep = data.fileFormat;
                        varFound = true;
                        varLength = 0;
                        break;
                    case 5:  // l (lowercase)
                        rep = "";
                        lowercase = true;
                        uppercase = false;
                        /* don't set "varFound = true" as that will cause
                         * lowercase to be "false" too soon*/
                        break;
                    case 6:  // month
                        sprintf(num, "%02d", data.releaseMonth);
                        rep = string(num);
                        varFound = true;
                        varLength = 0;
                        break;
                    case 7:  // 0num
                        sprintf(num, "%02d", data.trackNum);
                        rep = string(num);
                        varFound = true;
                        varLength = 0;
                        break;
                    case 8:  // num
                        sprintf(num, "%d", data.trackNum);
                        rep = string(num);
                        varFound = true;
                        varLength = 0;
                        break;
                    case 9: // sortname
                        if (varLength > 0)
                            rep = data.sortName.substr(0, varLength);
                        else
                        {
                            varLen = numCharsLeft / varCount;
                            varCount--;
                            rep = data.sortName;
                        }
                        varFound = true;
                        varLength = 0;
                        break;
                    case 10: // status
                        {
                            string status;
                            convertFromAlbumStatus(data.albumStatus, status);
                            if (varLength > 0)
                                rep = status.substr(0, varLength);
                            else
                            {
                                varLen = numCharsLeft / varCount;
                                varCount--;
                                rep = status;
                            }
                            varFound = true;
                            varLength = 0;
                            break;
                        }
                    case 11: // track
                        if (varLength > 0)
                            rep = data.track.substr(0, varLength);
                        else
                        {
                            varLen = numCharsLeft / varCount;
                            varCount--;
                            rep = data.track;
                        }
                        varFound = true;
                        varLength = 0;
                        break;
                    case 12: // type
                        {
                            string type;
                            convertFromAlbumType(data.albumType, type);
                            if (varLength > 0)
                                rep = type.substr(0, varLength);
                            else
                            {
                                varLen = numCharsLeft / varCount;
                                varCount--;
                                rep = type;
                            }
                            varFound = true;
                            varLength = 0;
                            break;
                        }
                    case 13: // u (uppercase)
                        rep = "";
                        lowercase = false;
                        uppercase = true;
                        /* don't set "varFound = true" as that will cause
                         * uppercase to be "false" too soon */
                        break;
                    case 14: // year
                        sprintf(num, "%04d", data.releaseYear);
                        rep = string(num);
                        varFound = true;
                        varLength = 0;
                        break;
                    /* the next two should be removed in the future */
                    case 15:  // abc2
                        if (data.variousArtist)
                            rep = data.album.substr(0, 2);
                        else
                            rep = data.sortName.substr(0, 2);
                        varFound = true;
                        varLength = 0;
                        break;
                    case 16:  // abc
                        if (data.variousArtist)
                            rep = data.album.substr(0, 1);
                        else
                            rep = data.sortName.substr(0, 1);
                        varFound = true;
                        varLength = 0;
                        break;
                    case 18:  // albumartist
                        if (varLength > 0)
                            rep = data.albumArtist.substr(0, varLength);
                        else
                        {
                            varLen = numCharsLeft / varCount;
                            varCount--;
                            rep = data.albumArtist;
                        }
                        varFound = true;
                        varLength = 0;
                        break;
                    case 17:  // albumartistsortname
                        if (varLength > 0)
                            rep = data.albumArtistSortName.substr(0, varLength);
                        else
                        {
                            varLen = numCharsLeft / varCount;
                            varCount--;
                            rep = data.albumArtistSortName;
                        }
                        varFound = true;
                        varLength = 0;
                        break;
                }
                rep = sanitize(rep);
                if (lowercase && varFound)
                    toLower(rep);
                if (uppercase && varFound)
                    toUpper(rep);
                name.erase(i, strlen(repVars[j]));
                name.insert(i, rep);
                i += rep.length() - 1;
                rep = "";
            }
        }
        if (!varFound)
        {
            /* variable not found, yet we have a "%"
             * let's see if the user wants to "limit" the amount of chars
             * in the next variable */
            if (atoi(name.substr(i + 1, 1).c_str()) > 0 && atoi(name.substr(i + 1, 1).c_str()) <= 9)
            {
                /* seems like the user wants a limited amount of chars
                 * in next variable */
                varLength = atoi(name.substr(i + 1, 1).c_str());
                /* erase those two chars... */
                name.erase(i, 2);
                /* and make sure it checks the same spot once more */
                i--;
            }
        }
        if (varFound)
        {
            lowercase = false;
            uppercase = false;
        }
    }

#ifdef WIN32
    bool winSafeFileNames = true;
#else
    bool winSafeFileNames = context->getWinSafeFileNames();
#endif    

    if (winSafeFileNames) {
    
        string::size_type pos = 0;
        // Some windows systems can't handle three periods in a row. Fucking lame!
        for(;;)
        {
            pos = name.find(" ...");
            if (pos != string::npos)
                name.erase(pos, 4);
            else
            {
                pos = name.find("...");
                if (pos != string::npos)
                    name.erase(pos, 3);
                else
                    break;
            }
        }

        // Now remove any characters that the filesystem might bitch about
        for(unsigned i = 0; i < name.size(); i++)
        {
            if (strchr(disallowedFileNameChars, name[i]))
            {
                name.erase(i, 1);
                i--;
            }
        }

        for(;;)
        {
            pos = name.find("...");
            if (pos != string::npos)
                name.erase(pos, 3);
            else
                break;
        }

        for(;;)
        {
            pos = name.find("..");
            if (pos != string::npos)
                name.erase(pos, 2);
            else
                break;
        }

        for(;;)
        {
            pos = name.find("  ");
            if (pos != string::npos)
                name.erase(pos, 1);
            else
                break;
        }

        for(;;)
        {
            pos = name.find(" " + string(dirSep));
            if (pos != string::npos)
                name.erase(pos, 1);
            else
                break;
        }

        // remove trailing dot
        for(;;)
        {
            pos = name.find("." + string(dirSep));
            if (pos != string::npos)
                name.erase(pos, 1);
            else
                break;
        }
        
    }

    // Rewrite spaces to underscores if allowedFileNameChars doesn't contain
    // a space character.
    if (!allowedFileChars.empty() && 
        strchr(allowedFileChars.c_str(), ' ') == NULL )
    {
        for (unsigned i = 0; name[i] != '\0'; i++)
        {
            if ( name[i] == ' ' )
                name[i] = '_';
        }
    }

    if (context->getMoveFiles())
    {
        string destDir = context->getDestDir(); 
        if (destDir.size() && destDir[destDir.size() - 1] == dirSepChar) 
            destDir.erase(destDir.size() - 1, 1);
        if (context->getRenameFiles())
            name = destDir + string(dirSep) + name;
        else
            name = destDir + string(dirSep) + extractFilePath(name) +
                       string(dirSep) + extractFileBase(origFile);
    }
    else
    {
        if (context->getRenameFiles())
            name = string(origPath) + string(dirSep) + extractFileName(name);
        else
            name = string(origPath) + string(dirSep) + extractFileBase(origFile);
    }

    // Fix empty directory names (// -> /, \\ -> \)
    for(;;)
    {
        string::size_type pos = name.find(string(dirSep) + string(dirSep));
        if (pos != string::npos)
            name.erase(pos, 1);
        else
            break;
    }

    // Remove leading dots
    for(;;)
    {
        string::size_type pos = name.find(string(dirSep) + ".");
        if (pos != string::npos)
            name.erase(pos + 1, 1);
        else
            break;
    }
	
    // Remove everything from name that isn't in allowedFileChars.
    // However, never remove the directory separator char and also ':' on Windows 
    if (!allowedFileChars.empty())
        for(unsigned i = 0; i < name.size(); i++)
        {
            if (name[i] != dirSepChar &&
#ifdef WIN32
                name[i] != ':' &&
#endif                
                !strchr(allowedFileChars.c_str(), name[i]))
            {
                name.erase(i, 1);
                i--;
            }
        }

    if (index > 0)
    {
        char temp[10];

        sprintf(temp, " (%d)", index);
        fileName = name + string(temp) + string(ext);
    }
    else
        fileName = name + string(ext);
}

//---------------------------------------------------------------------------

string FileNameMaker::extractFilePath(const string &file)
{
    string::size_type pos;
    
    pos = file.rfind(dirSep, file.size() - 1);
    if (pos == string::npos)
        return string(".");

    return file.substr(0, pos);
}

//---------------------------------------------------------------------------

string FileNameMaker::extractFileName(const string &file)
{
    string::size_type pos;
    
    pos = file.rfind(dirSep, file.size() - 1);
    if (pos == string::npos)
        return file;

    return file.substr(pos + 1, file.size());
}

//---------------------------------------------------------------------------

string FileNameMaker::extractFileBase(const string &fileArg)
{
    string            file = fileArg;
    string::size_type pos;

    file = extractFileName(file);
    pos = file.rfind(".", file.size() - 1);
    if (pos == string::npos)
        return file;

    return file.substr(0, pos);
}

//---------------------------------------------------------------------------

string FileNameMaker::extractFileExt(const string &file)
{
    string::size_type pos;
    
    pos = file.rfind(".", file.size() - 1);
    if (pos == string::npos)
        return file;

    return file.substr(pos, file.size());
}

//---------------------------------------------------------------------------

string FileNameMaker::extractVolume(const string &file)
{
#ifdef WIN32
    string::size_type pos;

    if (file.size() > 2 && file[0] == '\\' && file[1] == '\\')
    {
        pos = file.find("\\", 2);
        if (pos == string::npos)
            return "";

        return file.substr(0, pos);
    }

    if (file.size() > 2 && isalpha(file[0]) && file[1] == ':')
    {
        pos = file.find("\\", 1);
        if (pos == string::npos)
            return "";

        return file.substr(0, pos + 1);
    }
#endif
   
    return "";
}

//---------------------------------------------------------------------------

const string FileNameMaker::sanitize(const string &str)
{
    string data;

    data = str;
    for(int i = str.size() - 1; i >= 0; i--)
       if (str[i] == dirSepChar)
           data.erase(i, 1);

    return data;
}

//---------------------------------------------------------------------------

WriteThread::WriteThread(TunePimp  *tunePimpArg, FileCache *cacheArg, Plugins *pluginsArg) 
            :Thread(), FileNameMaker(&tunePimpArg->context)
{
    tunePimp = tunePimpArg;
    cache = cacheArg;
    plugins = pluginsArg;

    exitThread = false;
    sem = new Semaphore();
}

//---------------------------------------------------------------------------

WriteThread::~WriteThread(void)
{
    exitThread = true;
    sem->signal();
    join();
    delete sem;
}

//---------------------------------------------------------------------------

void WriteThread::wake(void)
{
    sem->signal();
}

//---------------------------------------------------------------------------

void WriteThread::threadMain(void)
{
    Metadata  server;
    string    fileName, status, puid, trackId;
    Track    *track;
    bool      checkedTrack = false, writeError = false;

    for(; !exitThread;)
    {
        track = cache->getNextItem(eVerified);
        if (track == NULL)
        {
            if (checkedTrack)
            {
                checkedTrack = false;
                tunePimp->writeTagsComplete(!writeError);
                writeError = false;
            }
            sem->wait();
            continue;
        }

        checkedTrack = true;

        track->lock();
        track->getServerMetadata(server);
        track->getPUID(server.filePUID);

        if (track->hasChanged())
        {
            track->unlock();
            if (writeTrack(track, server))
            {
                track->lock();
                if (track->getStatus() == eVerified)
                {
                    if (context->getAutoRemoveSavedFiles())
                        track->setStatus(eDeleted);
                    else
                    {
                        track->setLocalMetadata(server);
                        track->setServerMetadata(server);
                        track->setStatus(eSaved);
                    }
                    track->setError("Track saved.");
                }
            }
            else
            {
                track->lock();
                track->setStatus(eError);
                writeError = true;
            }
            tunePimp->wake(track);
        }
        else
        {
            track->getFileName(fileName);
            if (context->getAutoRemoveSavedFiles())
                track->setStatus(eDeleted);
            else
                track->setStatus(eSaved);
        }

        track->unlock();

        tunePimp->wake(track);
        cache->release(track);
    }
}

//---------------------------------------------------------------------------

bool WriteThread::writeTrack(Track *track, const Metadata &server)
{
    string           ext, fileName;
    unsigned long    fileSize;
    Plugin          *plugin;
    metadata_t       mdata;

    track->lock();
    track->getFileName(fileName);
    ext = extractFileExt(fileName);


    track->unlock();
    fileSize = fileOpenTest(fileName);
    track->lock();

    if (fileSize == 0)
    {
        track->setError("Cannot remove existing file -- file cannot be opened for exclusive access.");
        track->unlock();
        return false;
    }
    
    track->unlock();
    if (!diskSpaceTest(fileName, fileSize))
    {
        track->lock();
        track->setError("Not enough available diskspace for writing tags to the existing file.");
        track->unlock();
        return false;
    }

    plugin = plugins->get(ext, TP_PLUGIN_FUNCTION_METADATA);        
    if (plugin)
    {
        bool   ret;
        string err, encoding;
        int    flags = 0;

        if (strcasecmp(ext.c_str(), ".mp3") == 0)
        {
            if (tunePimp->context.getWriteID3v1())
                flags |= TP_PLUGIN_FLAGS_WRITE_ID3V1;
            if (tunePimp->context.getWriteID3v2_3())
                flags |= TP_PLUGIN_FLAGS_MP3_USE_ID3V23;
            switch(tunePimp->context.getID3Encoding())
            {
                case eLatin1:
                    flags |= TP_PLUGIN_FLAGS_MP3_WRITE_LATIN1;
                    break;
                case eEncodingError:
                case eUTF8:
                    // Do nothing -- UTF8 is the default
                    break;
                case eUTF16:
                    flags |= TP_PLUGIN_FLAGS_MP3_WRITE_UTF16;
                    break;
            }
        }

        if (tunePimp->context.getClearTags())
            flags |= TP_PLUGIN_FLAGS_GENERAL_CLEAR_TAGS;

        encoding = tunePimp->context.getFileNameEncoding();
        server.writeToC(&mdata);
        try
        {
            ret = plugin->writeMetadata(&mdata, fileName.c_str(), flags, encoding.c_str());
        }
        catch(...)
        {
            ret = false;
        }
        if (!ret)
        {
            err = string(plugin->getError());
            track->lock();
            track->setError(string("Could not write metadata to track: ") + string(err));
            track->unlock();
            return false;
        }
    }

    if (tunePimp->context.getRenameFiles() || tunePimp->context.getMoveFiles())
    {
        string newName, err;
        int    ret;

        for(int j = 0;; j++)
        {
            newName = fileName;
            makeNewFileName(server, newName, j);
            if (!tunePimp->context.getMoveFiles() || createPath(newName))
            {
#ifdef WIN32
                if (strcasecmp(newName.c_str(), fileName.c_str()) == 0)
#else
                if (strcmp(newName.c_str(), fileName.c_str()) == 0)
#endif
                   break;

                string encoding = tunePimp->context.getFileNameEncoding();
		if (taccess(newName.c_str(), 0, encoding.c_str()) == 0)
                   continue;

                fileSize = fileOpenTest(fileName);
                if (fileSize == 0)
                {
                    track->lock();
                    track->setError("Cannot write to new file -- access denied.");
                    track->unlock();
                    return false;
                }
    
                if (!diskSpaceTest(newName, fileSize))
                {
                    track->lock();
                    track->setError("Not enough available diskspace for writing a new file.");
                    track->unlock();
                    return false;
                }

                ret = trename(fileName.c_str(), newName.c_str(), encoding.c_str());
		if (ret != 0 && errno == EEXIST)
                    continue;

                if (ret != 0)
                {
                    track->lock();
                    track->setError("Could not rename file.");
                    track->unlock();
                    return false;
                }

                if (tunePimp->context.getMoveFiles())
                    cleanPath(fileName);
            }
            else
            {
                string path = extractFilePath(newName);

                err = string("Could not create destination directory: ") + path;
                track->lock();
                track->setError(err);
                track->unlock();
                return false;
            }

            break;
        }
        track->lock();
        track->setFileName(newName);
        track->unlock();
    }

    return true;
}

//---------------------------------------------------------------------------

#ifdef WIN32
unsigned long WriteThread::fileOpenTest(const string &fileName)
{
    HANDLE        openTest = INVALID_HANDLE_VALUE;
    unsigned long fileSize;

    if (GetVersion() < 0x80000000)
    {
	string newFileName = string("\\\\?\\") + fileName;
	LPWSTR wFileName = new WCHAR[newFileName.size() + 1];
	MultiByteToWideChar(CP_UTF8, 0, newFileName.c_str(), -1, wFileName, newFileName.size() + 1);
	openTest = CreateFileW(wFileName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
	delete [] wFileName;
    }
    else {
	LPSTR aFileName = NULL;
	if (!utf8_decode(fileName.c_str(), &aFileName))
	{
	    openTest = CreateFileA(aFileName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
	    free(aFileName);
	}
    }
    
    if (openTest == INVALID_HANDLE_VALUE)
        return 0;

    fileSize = SetFilePointer(openTest, 0, NULL, FILE_END);
    CloseHandle(openTest);

    return fileSize;
}

#else
//---------------------------------------------------------------------------

unsigned long WriteThread::fileOpenTest(const string &fileName)
{
    int           openTest;
    unsigned long fileSize;
    string        encoding;
   
    encoding = tunePimp->context.getFileNameEncoding();
    openTest = open(utf8ToEncoding(fileName, encoding).c_str(), O_EXCL | O_RDWR);
    if (openTest < 0)
        return 0;

    fileSize = lseek(openTest, 0, SEEK_END);
    close(openTest);

    return fileSize;
}
#endif

//---------------------------------------------------------------------------

#ifdef WIN32
bool WriteThread::diskSpaceTest(const string &fileName, unsigned long fileSize)
{
    ULARGE_INTEGER temp; 
    __int64        diskSpace;
    bool           ret = false;
    string         newFileName;
    LPWSTR         wFileName;

    string path = extractFilePath(fileName);

    // GetDiskFreeSpaceEx says that if a path is a UNC then it needs
    // to end with a backslash. 
    if (path.size() >= 2 && path[0] == '\\' && path[1] == '\\')
        path += "\\";

    if (GetVersion() < 0x80000000)
    {
	newFileName = string("\\\\?\\") + path;
	wFileName = new WCHAR[newFileName.size() + 1];
	MultiByteToWideChar(CP_UTF8, 0, newFileName.c_str(), -1, wFileName, newFileName.size() + 1);
	ret = GetDiskFreeSpaceExW(wFileName, &temp, NULL, NULL);
	delete [] wFileName;
	if (!ret && GetLastError() == ERROR_INVALID_NAME)
	{
	    path.erase(3, path.size());
	    newFileName = string("\\\\?\\") + path;
	    wFileName = new WCHAR[newFileName.size() + 1];
	    MultiByteToWideChar(CP_UTF8, 0, newFileName.c_str(), -1, wFileName, newFileName.size() + 1);
	    ret = GetDiskFreeSpaceExW(wFileName, &temp, NULL, NULL);
	    delete [] wFileName;
	}
    }
    else {
	LPSTR aFileName = NULL;
	if (!utf8_decode(fileName.c_str(), &aFileName))
	{
	    ret = GetDiskFreeSpaceExA(aFileName, &temp, NULL, NULL);
	    free(aFileName);
	}
    }

    if (ret)
    {
        diskSpace = *(__int64 *)&temp;

        // Increase the size a bit in case the file grows and what not.
        fileSize += fileSize / 10;

        return diskSpace > (__int64)fileSize;
    }

    // If we can't determine if the diskspace is ok, just assume it is. There is
    // probably some bigger bug causing havoc...
    return true;
}

#else
//---------------------------------------------------------------------------

bool WriteThread::diskSpaceTest(const string &fileName, unsigned long fileSize)
{
    struct statfs stat;
    string        encoding;
   
    encoding = tunePimp->context.getFileNameEncoding();

    string path = extractFilePath(fileName);
    if (statfs(utf8ToEncoding(path, encoding).c_str(), &stat) == 0)
    {
        if (stat.f_bsize == 0)
            return true;
        
        fileSize += fileSize / 10;
        fileSize /= stat.f_bsize;

        return fileSize < (unsigned long)stat.f_bavail;
    }
    else
        return false;
}
#endif

bool WriteThread::createPath(const string &pathArg)
{
    string            path = string(extractFilePath(pathArg).c_str());
    string            volume = string(extractVolume(pathArg).c_str());
    string            partial, encoding;
    string::size_type pos;

    encoding = tunePimp->context.getFileNameEncoding();
    if (volume.size() > 0)
        path.erase(0, volume.size());

    if (path[path.size() - 1] != dirSepChar)
        path += dirSep;

    for(pos = 1;;)
    {
        pos = path.find(dirSep, pos);
        if (pos == string::npos)
            break;

        partial = volume + path.substr(0, pos);
        if (taccess(partial.c_str(), 0, encoding.c_str()))
        {
            if (tmkdir(partial.c_str(), encoding.c_str()) < 0)
                return false;
        }

        pos++;
    }

    return true;
}

void WriteThread::cleanPath(const string &pathArg)
{
    string      path = string(extractFilePath(pathArg).c_str());
    string      volume = string(extractVolume(pathArg).c_str());
    string      srcDir, complete, encoding;
    unsigned    pos;
    int         ret;

    encoding = tunePimp->context.getFileNameEncoding();
    srcDir = tunePimp->context.getTopSrcDir();
    if (volume.size() > 0)
        path.erase(0, volume.size());

    if (path[path.size() - 1] == dirSepChar)
        path.erase(path.size() - 1);

    if (srcDir[srcDir.size() - 1] == dirSepChar)
        srcDir.erase(srcDir.size() - 1);

    for(;;)
    {
        complete = volume + path;
        if (strcasecmp(srcDir.c_str(), complete.c_str()) == 0)
        {
            break;
        }

        ret = trmdir(complete.c_str(), encoding.c_str());
        if (ret < 0)
            break;

        pos = path.rfind(dirSep);
        if (pos == string::npos)
            break;

        path.erase(pos);
    }
}
