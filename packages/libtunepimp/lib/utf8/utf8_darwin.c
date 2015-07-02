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

   $Id: utf8_darwin.c 1340 2004-09-21 04:41:06Z robert $

----------------------------------------------------------------------------*/
/*
 * Convert a string between UTF-8 and the locale's charset.
 */

#include <stdlib.h>
#include <string.h>
#include <CoreFoundation/CFString.h>

#include "utf8.h"

// returns 0 for ok, -1 for not ok
int utf8_encode(const char *from, char **to)
{
    CFIndex     destLen;
    CFStringRef temp;
    
    temp = CFStringCreateWithBytes (NULL, (const UInt8 *)from,
                          strlen(from), kCFStringEncodingISOLatin1, false);
    destLen = CFStringGetMaximumSizeForEncoding(CFStringGetLength(temp),  
              kCFStringEncodingUTF8);
    *to = malloc(destLen + 1);
    return CFStringGetCString(temp, *to, destLen+1, kCFStringEncodingUTF8) ? 0 : -1;
}

int utf8_decode(const char *from, char **to)
{
    CFIndex     destLen;
    CFStringRef temp;
    
    temp = CFStringCreateWithBytes (NULL, (const UInt8 *)from,
                          strlen(from), kCFStringEncodingUTF8, false);
    destLen = CFStringGetMaximumSizeForEncoding(CFStringGetLength(temp),  
              kCFStringEncodingUTF8);
    *to = malloc(destLen + 1);
    return CFStringGetCString(temp, *to, destLen+1, kCFStringEncodingISOLatin1) ? 0 : -1;
}
