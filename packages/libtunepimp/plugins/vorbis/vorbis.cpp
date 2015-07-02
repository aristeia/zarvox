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

   $Id: vorbis.cpp 1441 2005-12-18 19:16:49Z luks $

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
#include "vorbisdecode.h"
#include "vorbis_meta.h"

extern "C"
{

/*-------------------------------------------------------------------------*/

#ifndef WIN32
  #define initPlugin vorbisInitPlugin
#endif

Plugin                  *initPlugin         (void);
static void              vorbisShutdown     (void);
static const char       *vorbisGetVersion   (void);
static const char       *vorbisGetName      (void);
static int               vorbisGetNumFormats(void);
static int               vorbisGetFormat    (int, char ext[TP_EXTENSION_LEN],
                                             char desc[TP_PLUGIN_DESC_LEN], int *functions);
static const char       *vorbisGetError     (void);
static int               vorbisWriteMetadata(const metadata_t *mdata, const char *fileName, int flags, const char *encoding);
static int               vorbisReadMetadata (metadata_t *mdata, const char *fileName, int flags, const char *encoding);
static unsigned long     vorbisGetDuration  (const char *file, int flags, const char *encoding);
static void             *vorbisDecodeStart  (const char *file, int flags, const char *encoding);
static int               vorbisDecodeInfo   (void *decode,
                                             unsigned long *duration,
                                             unsigned int *samplesPerSecond,
                                             unsigned int *bitsPerSample,
                                             unsigned int *channels);
static int               vorbisDecodeRead   (void *decode, char *data, int maxBytes);
static void              vorbisDecodeEnd    (void *decode);

/*-------------------------------------------------------------------------*/

#define PLUGIN_VERSION "1.0.0"
#define PLUGIN_NAME    "Vorbis decoder & metadata reader/writer"

static char *errorString = "";

/*-------------------------------------------------------------------------*/

static Plugin methods = 
{
    vorbisShutdown,
    vorbisGetVersion,
    vorbisGetName,
    vorbisGetNumFormats,
    vorbisGetFormat,
    vorbisGetError,
    vorbisReadMetadata,
    vorbisWriteMetadata,
    vorbisGetDuration,
    vorbisDecodeStart,
    vorbisDecodeInfo,
    vorbisDecodeRead,
    vorbisDecodeEnd
};

/*-------------------------------------------------------------------------*/

Plugin *initPlugin(void)
{
    return &methods;
}

static void vorbisShutdown(void)
{
    if (strlen(errorString))
       free(errorString);
}

static const char *vorbisGetVersion(void)
{
    return PLUGIN_VERSION;
}

static const char *vorbisGetName(void)
{
    return PLUGIN_NAME;
}

static int vorbisGetNumFormats(void)
{
    return 1;
}

static int vorbisGetFormat(int i, char ext[TP_EXTENSION_LEN],
                        char desc[TP_PLUGIN_DESC_LEN], int *functions)
{
    if (i > 0)
        return 0;

    strcpy(ext, ".ogg");
    strcpy(desc, "Ogg/Vorbis Audio format");
    *functions = TP_PLUGIN_FUNCTION_DECODE | TP_PLUGIN_FUNCTION_METADATA;

    return 1;
}

static const char *vorbisGetError(void)
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

static int vorbisReadMetadata(metadata_t *mdata, const char *fileName, int flags, const char *encoding)
{
    Metadata data;
    Vorbis   vorbis(encoding);

    if (vorbis.read(fileName, data))
    {
        data.writeToC(mdata);
        return 1;
    }
    else
    {
        string err;
        vorbis.getError(err);
        setError(err);
    }
    return 0;
}

static int vorbisWriteMetadata(const metadata_t *mdata, const char *fileName, int flags, const char *encoding)
{
    Metadata data;
    Vorbis   vorbis(encoding);

    data.readFromC(mdata);
    int ret = vorbis.write(fileName, data, (flags & TP_PLUGIN_FLAGS_GENERAL_CLEAR_TAGS) != 0);
    if (!ret)
    {
        string err;
        vorbis.getError(err);
        setError(err);
    }
    return ret;
}

static unsigned long vorbisGetDuration(const char *fileName, int flags, const char *encoding)
{
    VorbisDecode  *decode;
    unsigned long  duration;
    unsigned int   samplesPerSecond, bitsPerSample, channels;

    decode = new VorbisDecode(fileName, encoding);
    if (!decode)
        return 0;

    if (!decode->getInfo(duration, samplesPerSecond, bitsPerSample, channels))
        duration = 0;

    delete decode;

    return duration;
}

static void *vorbisDecodeStart(const char *fileName, int flags, const char *encoding)
{
    return (void *)new VorbisDecode(fileName, encoding);
}

static int vorbisDecodeInfo(void *decode,
                            unsigned long *duration,
                            unsigned int *samplesPerSecond,
                            unsigned int *bitsPerSample,
                            unsigned int *channels)
{
    return ((VorbisDecode *)decode)->getInfo(*duration, *samplesPerSecond, *bitsPerSample, *channels); 
}

static int vorbisDecodeRead(void *decode, char *data, int maxBytes)
{
    return ((VorbisDecode *)decode)->read(data, maxBytes);
}

static void vorbisDecodeEnd(void *decode)
{
    delete (VorbisDecode *)decode;
}

} // extern "C"

