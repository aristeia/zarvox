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

   $Id: utf8util.cpp 9816 2008-04-22 08:06:09Z luks $

----------------------------------------------------------------------------*/

#include <stdio.h>
#include <cstdlib>
#include "utf8util.h"
#include "utf8.h"
#ifdef WIN32
#include "../../config_win32.h"
#endif

string utf8Encode(const string &from)
{
    int   ret;
    char *dest;
    string to;

    to.clear();
    ret = utf8_encode(from.c_str(), &dest);
    if (ret >= 0)
    {
        to = string(dest);
        free(dest);
    }
    return to;
}

string utf8Decode(const string &from)
{
    int   ret;
    char *dest;
    string to;

    to.clear();
    ret = utf8_decode(from.c_str(), &dest);
    if (ret >= 0)
    {
        to = string(dest);
        free(dest);
    }
    return to;
}

#if !defined(WIN32) && defined(HAVE_ICONV)
extern "C"
{
int iconvert(const char *fromcode, const char *tocode,
	     const char *from, size_t fromlen,
	     char **to, size_t *tolen);
}
#endif

string utf8ToEncoding(const string &from, const string &encoding)
{
#if !defined(WIN32) && defined(HAVE_ICONV)
    string to;

    if (strcasecmp(encoding.c_str(), "utf-8") == 0)
    {
        to = from;
        return to;
    }

    int   ret;
    char *dest;

	ret = iconvert("UTF-8", encoding.c_str(), from.c_str(), from.length(), &dest, 0);
    if (ret >= 0)
    {
        to = string(dest);
        free(dest);
    }
    return to;
#else
    /* 
    It's perfectly safe to do this, because on Windows we have internally all file names in UTF-8, and for WINAPI functions we only can use file names in
    ANSI CPs (windows-1250, windows-1251, ...) or UNICODE16. File names in these encodings are then automaticaly (inside WINAPI) converted to right
    encoding. So if we will always use WINAPI functions with W suffix, we don't need any other encoding than UNICODE.
    */
    return from;
#endif
}

string utf8FromEncoding(const string &from, const string &encoding)
{
#if !defined(WIN32) && defined(HAVE_ICONV)
    string to;

    if (strcasecmp(encoding.c_str(), "utf-8") == 0)
    {
        to = from;
        return to;
    }

    int   ret;
    char *dest;
    ret = iconvert(encoding.c_str(), "UTF-8", from.c_str(), from.length(), &dest, 0);
    if (ret >= 0)
    {
        to = string(dest);
        free(dest);
    }
    
    return to;
#else
    return from;
#endif
}
