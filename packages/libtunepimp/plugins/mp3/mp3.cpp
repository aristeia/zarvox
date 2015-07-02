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

   $Id: mp3.cpp 1426 2005-10-07 01:34:14Z luks $

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
#include "mp3.h"
#include "mp3decode.h"
#include "metadata.h"
#include "id3_meta.h"
#include "id3_2_3_meta.h"
#include "mp3info.h"

/*-------------------------------------------------------------------------*/

#define PLUGIN_VERSION               "1.0.0"
#define PLUGIN_NAME                  "MP3 decoder & ID3v1/v2 reader/writer"


extern "C"
{

/*-------------------------------------------------------------------------*/

#ifndef WIN32
  #define initPlugin mp3InitPlugin
#endif

Plugin                  *initPlugin      (void);
static void              MP3Shutdown     (void);
static const char       *MP3GetVersion   (void);
static const char       *MP3GetName      (void);
static int               MP3GetNumFormats(void);
static int               MP3GetFormat    (int, char ext[TP_EXTENSION_LEN],
                                          char desc[TP_PLUGIN_DESC_LEN], int *functions);
static const char       *MP3GetError     (void);
static int               MP3WriteMetadata(const metadata_t *mdata, const char *fileName, int flags, const char *encoding);
static int               MP3ReadMetadata (metadata_t *mdata, const char *fileName, int flags, const char *encoding);
static unsigned long     MP3GetDuration  (const char *file, int flags, const char *encoding);
static void             *MP3DecodeStart  (const char *file, int flags, const char *encoding);
static int               MP3DecodeInfo   (void *decode,
                                          unsigned long *duration,
                                          unsigned int *samplesPerSecond,
                                          unsigned int *bitsPerSample,
                                          unsigned int *channels);
static int               MP3DecodeRead   (void *decode, char *data, int maxBytes);
static void              MP3DecodeEnd    (void *decode);

/*-------------------------------------------------------------------------*/

static Plugin methods = 
{
    MP3Shutdown,
    MP3GetVersion,
    MP3GetName,
    MP3GetNumFormats,
    MP3GetFormat,
    MP3GetError,
    MP3ReadMetadata,
    MP3WriteMetadata,
    MP3GetDuration,
    MP3DecodeStart,
    MP3DecodeInfo,
    MP3DecodeRead,
    MP3DecodeEnd
};
static char *errorString = "";

/*-------------------------------------------------------------------------*/

Plugin *initPlugin(void)
{
    return &methods;
}

static void MP3Shutdown(void)
{
    if (strlen(errorString))
       free(errorString);
}

static const char *MP3GetVersion(void)
{
    return PLUGIN_VERSION;
}

static const char *MP3GetName(void)
{
    return PLUGIN_NAME;
}

static int MP3GetNumFormats(void)
{
    return 1;
}

static int MP3GetFormat(int i, char ext[TP_EXTENSION_LEN],
                        char desc[TP_PLUGIN_DESC_LEN], int *functions)
{
    if (i > 0)
        return 0;

    strcpy(ext, ".mp3");
    strcpy(desc, "MP3 Audio format");
    *functions = TP_PLUGIN_FUNCTION_DECODE | TP_PLUGIN_FUNCTION_METADATA;

    return 1;
}

static const char *MP3GetError(void)
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

static MetadataPlugin *id3Factory(int flags, const string &encoding)
{
    bool writeV1 = ((flags & TP_PLUGIN_FLAGS_WRITE_ID3V1) != 0);
    bool use2_3 = ((flags & TP_PLUGIN_FLAGS_MP3_USE_ID3V23) != 0);
    ID3_Encoding enc = idUTF8;

    if ((flags & TP_PLUGIN_FLAGS_MP3_WRITE_LATIN1) != 0)
        enc = idLatin1;
    else
    if ((flags & TP_PLUGIN_FLAGS_MP3_WRITE_UTF16) != 0)
        enc = idUTF16;
        
    return use2_3 ? (MetadataPlugin *)(new ID3_2_3(writeV1, enc, encoding)) : (MetadataPlugin *)(new ID3(writeV1, enc, encoding));
}

static int MP3ReadMetadata(metadata_t *mdata, const char *fileName, int flags, const char *encoding)
{
    Metadata        data;
    MetadataPlugin *id3 = id3Factory(flags, encoding);
    int             ret = 0;

    if (id3->read(fileName, data))
    {
        data.writeToC(mdata);
        ret = 1;
    }
    else
    {
        string err;
        id3->getError(err);
        setError(err);
    }
    delete id3;
    return ret;
}

static int MP3WriteMetadata(const metadata_t *mdata, const char *fileName, int flags, const char *encoding)
{
    int             ret;
    Metadata        data;
    MetadataPlugin *id3 = id3Factory(flags, encoding);

    data.readFromC(mdata);
    ret = id3->write(fileName, data, (flags & TP_PLUGIN_FLAGS_GENERAL_CLEAR_TAGS) != 0);
    if (!ret)
    {
        string err;
        id3->getError(err);
        setError(err);
    }
    delete id3;
    return ret;
}

static unsigned long MP3GetDuration(const char *fileName, int flags, const char *encoding)
{
    TPMP3Info     mp3info;
    int           ret;

    ret = mp3info.analyze(fileName, encoding);
    if (ret)
        return (unsigned long)mp3info.getDuration();

    return 0;
}

static void *MP3DecodeStart(const char *fileName, int flags, const char *encoding)
{
    return (void *)new MP3Decode(fileName, encoding);
}

static int MP3DecodeInfo(void *decode,
                         unsigned long *duration,
                         unsigned int *samplesPerSecond,
                         unsigned int *bitsPerSample,
                         unsigned int *channels)
{
    return ((MP3Decode *)decode)->getInfo(*duration, *samplesPerSecond, *bitsPerSample, *channels); 
}

static int MP3DecodeRead(void *decode, char *data, int maxBytes)
{
    return ((MP3Decode *)decode)->read(data, maxBytes);
}

static void MP3DecodeEnd(void *decode)
{
    delete (MP3Decode *)decode;
}

} // extern "C"
