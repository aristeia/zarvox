/*----------------------------------------------------------------------------

   libtunepimp -- The MusicBrainz tagging library.
                  Let a thousand taggers bloom!

   Copyright (C) Robert Kaye 2003
   Originally part of bitcollider from the Bitzi Corporation.

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

   $Id: plugin.h 1389 2005-06-14 00:00:38Z robert $

----------------------------------------------------------------------------*/
#ifndef PLUGIN_H
#define PLUGIN_H

#ifdef __cplusplus
extern "C" {
#endif

#include "tp_c.h"

#define TP_PLUGIN_DESC_LEN          64

/* Does this plugin support metadata reading/writing? */
#define TP_PLUGIN_FUNCTION_METADATA 1
/* Does this plugin support audio decode? */
#define TP_PLUGIN_FUNCTION_DECODE   2

/* These are general flags that apply to all plugins */
#define TP_PLUGIN_FLAGS_GENERAL_CLEAR_TAGS 0x0001
#define TP_PLUGIN_FLAGS_GENERAL_RESEVERD2  0x0002
#define TP_PLUGIN_FLAGS_GENERAL_RESEVERD3  0x0004

/* These are flags that are specific to a particular plugin type */
#define TP_PLUGIN_FLAGS_SPECIFIC1           0x0010
#define TP_PLUGIN_FLAGS_SPECIFIC2           0x0020
#define TP_PLUGIN_FLAGS_SPECIFIC3           0x0040
#define TP_PLUGIN_FLAGS_SPECIFIC4           0x0080
#define TP_PLUGIN_FLAGS_SPECIFIC5           0x0100

/* Specific flags for the MP3 plugin */
#define TP_PLUGIN_FLAGS_WRITE_ID3V1      TP_PLUGIN_FLAGS_SPECIFIC1 

/* Latin1 tags will be written by default, if id3v2.3 is used */
#define TP_PLUGIN_FLAGS_MP3_USE_ID3V23   TP_PLUGIN_FLAGS_SPECIFIC2

/* UTF-8 tags will be written by default, unless one of these flags is passed: */
#define TP_PLUGIN_FLAGS_MP3_WRITE_LATIN1 TP_PLUGIN_FLAGS_SPECIFIC3
#define TP_PLUGIN_FLAGS_MP3_WRITE_UTF16  TP_PLUGIN_FLAGS_SPECIFIC4

/*-------------------------------------------------------------------------*/

typedef struct _Plugin
{
    void              (*shutdown)            (void);

    const char       *(*getVersion)          (void);
    const char       *(*getName)             (void);
    int               (*getNumFormats)       (void);
    int               (*getFormat)           (int, 
                                              char ext[TP_EXTENSION_LEN], 
                                              char desc[TP_PLUGIN_DESC_LEN],
                                              int *functions);
    const char       *(*getError)            (void);
   
    int               (*readMetadata)        (metadata_t *, 
                                              const char *fileName,
                                              int flags,
                                              const char *encoding);
    int               (*writeMetadata)       (const metadata_t *, 
                                              const char *fileName,
                                              int flags,
                                              const char *encoding);
    unsigned long     (*getDuration)         (const char *fileName, 
                                              int flags,
                                              const char *encoding);
    void             *(*decodeStart)         (const char *fileName, 
                                              int flags,
                                              const char *encoding);
    int               (*decodeInfo)          (void *decode, 
                                              unsigned long *duration,
                                              unsigned int *samplesPerSecond,
                                              unsigned int *bitsPerSample,
                                              unsigned int *channels);
    int               (*decodeRead)          (void *decode, char *data, int maxBytes);
    void              (*decodeEnd)           (void *decode);

} Plugin;

/*-------------------------------------------------------------------------*/

#ifdef __cplusplus
}
#endif

#endif
