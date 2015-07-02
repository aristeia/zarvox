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

   $Id: flac.cpp 1441 2005-12-18 19:16:49Z luks $

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
#include "flacdecode.h"
#include "flac_meta.h"

extern "C"
{

/*-------------------------------------------------------------------------*/

#ifndef WIN32
  #define initPlugin flacInitPlugin
#endif

Plugin                  *initPlugin       (void);
static void              flacShutdown     (void);
static const char       *flacGetVersion   (void);
static const char       *flacGetName      (void);
static int               flacGetNumFormats(void);
static int               flacGetFormat    (int, char ext[TP_EXTENSION_LEN],
                                           char desc[TP_PLUGIN_DESC_LEN], int *functions);
static const char       *flacGetError     (void);
static int               flacWriteMetadata(const metadata_t *mdata, const char *fileName, int flags, const char *encoding);
static int               flacReadMetadata (metadata_t *mdata, const char *fileName, int flags, const char *encoding);
static unsigned long     flacGetDuration  (const char *file, int flags, const char *encoding);
static void             *flacDecodeStart  (const char *file, int flags, const char *encoding);
static int               flacDecodeInfo   (void *decode,
                                           unsigned long *duration,
                                           unsigned int *samplesPerSecond,
                                           unsigned int *bitsPerSample,
                                           unsigned int *channels);
static int               flacDecodeRead   (void *decode, char *data, int maxBytes);
static void              flacDecodeEnd    (void *decode);

/*-------------------------------------------------------------------------*/

#define PLUGIN_VERSION "1.0.0"
#define PLUGIN_NAME    "FLAC decoder & metadata reader/writer"

static char *errorString = "";

/*-------------------------------------------------------------------------*/

static Plugin methods = 
{
    flacShutdown,
    flacGetVersion,
    flacGetName,
    flacGetNumFormats,
    flacGetFormat,
    flacGetError,
    flacReadMetadata,
    flacWriteMetadata,
    flacGetDuration,
    flacDecodeStart,
    flacDecodeInfo,
    flacDecodeRead,
    flacDecodeEnd
};

/*-------------------------------------------------------------------------*/

Plugin *initPlugin(void)
{
    return &methods;
}

static void flacShutdown(void)
{
    if (strlen(errorString))
       free(errorString);
}

static const char *flacGetVersion(void)
{
    return PLUGIN_VERSION;
}

static const char *flacGetName(void)
{
    return PLUGIN_NAME;
}

static int flacGetNumFormats(void)
{
    return 1;
}

static int flacGetFormat(int i, char ext[TP_EXTENSION_LEN],
                        char desc[TP_PLUGIN_DESC_LEN], int *functions)
{
    if (i > 0)
        return 0;

    strcpy(ext, ".flac");
    strcpy(desc, "FLAC Lossless audio format");
    *functions = TP_PLUGIN_FUNCTION_DECODE | TP_PLUGIN_FUNCTION_METADATA;

    return 1;
}

static const char *flacGetError(void)
{
    return errorString;
}

static void setError(const string &err)
{
    if (err.length())
    {
        if (errorString)
            free(errorString);
        errorString = strdup(err.c_str());
    }
}

static int flacReadMetadata(metadata_t *mdata, const char *fileName, int flags, const char *encoding)
{
    Metadata data;
    FLAC     flac(encoding);

    if (flac.read(fileName, data))
    {
        data.writeToC(mdata);
        return 1;
    }
    else
    {
        string err;
        flac.getError(err);
        setError(err);
    }
    return 0;
}

static int flacWriteMetadata(const metadata_t *mdata, const char *fileName, int flags, const char *encoding)
{
    Metadata data;
    FLAC     flac(encoding);

    data.readFromC(mdata);
    int ret = flac.write(fileName, data, (flags & TP_PLUGIN_FLAGS_GENERAL_CLEAR_TAGS) != 0);
    if (!ret)
    {
        string err;
        flac.getError(err);
        setError(err);
    }
    return ret;
}

static unsigned long flacGetDuration(const char *fileName, int flags, const char *encoding)
{
    FlacDecode    *decode;
    unsigned long  duration;
    unsigned int   samplesPerSecond, bitsPerSample, channels;

    decode = new FlacDecode(fileName, encoding);
    if (!decode)
        return 0;

    if (!decode->getInfo(duration, samplesPerSecond, bitsPerSample, channels))
        duration = 0;

    delete decode;

    return duration;
}

static void *flacDecodeStart(const char *fileName, int flags, const char *encoding)
{
    return (void *)new FlacDecode(fileName, encoding);
}

static int flacDecodeInfo(void *decode,
                            unsigned long *duration,
                            unsigned int *samplesPerSecond,
                            unsigned int *bitsPerSample,
                            unsigned int *channels)
{
    return ((FlacDecode *)decode)->getInfo(*duration, *samplesPerSecond, *bitsPerSample, *channels); 
}

static int flacDecodeRead(void *decode, char *data, int maxBytes)
{
    return ((FlacDecode *)decode)->read(data, maxBytes);
}

static void flacDecodeEnd(void *decode)
{
    delete (FlacDecode *)decode;
}

} // extern "C"
