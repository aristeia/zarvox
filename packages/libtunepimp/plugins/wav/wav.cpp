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

   $Id: wav.cpp 1390 2005-06-14 17:46:40Z robert $

----------------------------------------------------------------------------*/


#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include <errno.h>
#ifdef WIN32
#include <winsock.h>
#else
#include <netinet/in.h>
#include <sys/param.h>
#endif

#include "plugin.h"
#include "wavdecode.h"

extern "C"
{

/*-------------------------------------------------------------------------*/

#ifndef WIN32
  #define initPlugin wavInitPlugin
#endif

Plugin                  *initPlugin      (void);
static void              wavShutdown     (void);
static const char       *wavGetVersion   (void);
static const char       *wavGetName      (void);
static int               wavGetNumFormats(void);
static int               wavGetFormat    (int, char ext[TP_EXTENSION_LEN],
                                          char desc[TP_PLUGIN_DESC_LEN], int *functions);
static const char       *wavGetError     (void);
static unsigned long     wavGetDuration  (const char *file, int flags, const char *encoding);
static void             *wavDecodeStart  (const char *file, int flags, const char *encoding);
static int               wavDecodeInfo   (void *decode,
                                          unsigned long *duration,
                                          unsigned int *samplesPerSecond,
                                          unsigned int *bitsPerSample,
                                          unsigned int *channels);
static int               wavDecodeRead   (void *decode, char *data, int maxBytes);
static void              wavDecodeEnd    (void *decode);

/*-------------------------------------------------------------------------*/

#define PLUGIN_VERSION "1.0.0"
#define PLUGIN_NAME    "WAV decoder"

static char *errorString = "";

/*-------------------------------------------------------------------------*/

static Plugin methods = 
{
    wavShutdown,
    wavGetVersion,
    wavGetName,
    wavGetNumFormats,
    wavGetFormat,
    wavGetError,
    NULL,
    NULL,
    wavGetDuration,
    wavDecodeStart,
    wavDecodeInfo,
    wavDecodeRead,
    wavDecodeEnd
};

/*-------------------------------------------------------------------------*/

Plugin *initPlugin(void)
{
    return &methods;
}

static void wavShutdown(void)
{
    if (strlen(errorString))
       free(errorString);
}

static const char *wavGetVersion(void)
{
    return PLUGIN_VERSION;
}

static const char *wavGetName(void)
{
    return PLUGIN_NAME;
}

static int wavGetNumFormats(void)
{
    return 1;
}

static int wavGetFormat(int i, char ext[TP_EXTENSION_LEN],
                        char desc[TP_PLUGIN_DESC_LEN], int *functions)
{
    if (i > 0)
        return 0;

    strcpy(ext, ".wav");
    strcpy(desc, "WAV Audio format");
    *functions = TP_PLUGIN_FUNCTION_DECODE;

    return 1;
}

static const char *wavGetError(void)
{
    return errorString;
}

static unsigned long wavGetDuration(const char *fileName, int flags, const char *encoding)
{
    WavDecode     *decode;
    unsigned long  duration;
    unsigned int   samplesPerSecond, bitsPerSample, channels;

    decode = new WavDecode(fileName, encoding);
    if (!decode)
        return 0;

    if (!decode->getInfo(duration, samplesPerSecond, bitsPerSample, channels))
        duration = 0;

    delete decode;

    return duration;
}

static void *wavDecodeStart(const char *fileName, int flags, const char *encoding)
{
    return (void *)new WavDecode(fileName, encoding);
}

static int wavDecodeInfo(void *decode,
                         unsigned long *duration,
                         unsigned int *samplesPerSecond,
                         unsigned int *bitsPerSample,
                         unsigned int *channels)
{
    return ((WavDecode *)decode)->getInfo(*duration, *samplesPerSecond, *bitsPerSample, *channels); 
}

static int wavDecodeRead(void *decode, char *data, int maxBytes)
{
    return ((WavDecode *)decode)->read(data, maxBytes);
}

static void wavDecodeEnd(void *decode)
{
    delete (WavDecode *)decode;
}

} // extern "C"
