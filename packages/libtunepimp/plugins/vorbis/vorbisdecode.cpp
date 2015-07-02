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

   $Id: vorbisdecode.cpp 7230 2006-04-16 11:25:38Z luks $

----------------------------------------------------------------------------*/
#include <stdlib.h>
#include <string.h>
#include <vorbis/vorbisfile.h>
#include "vorbisdecode.h"

const int decodeSize = 8192;

/* The callback functions were used since the ov_open call simply crashed and burned */
size_t ReadFunc(void *ptr, size_t size, size_t nmemb, void *datasource)
{
   return tread(ptr, size, nmemb, (TFILE *)datasource);
}

int SeekFunc(void *datasource, ogg_int64_t offset, int whence)
{
   return tseek((TFILE *)datasource, (int)offset, whence);
}

int CloseFunc(void *datasource)
{
   return tclose((TFILE *)datasource);
}

long TellFunc(void *datasource)
{
   return ttell((TFILE *)datasource);
}

VorbisDecode::VorbisDecode(const string &fileName, const string &encoding) 
             :DecodePlugin()
{
   vi = NULL;

   in = topen(fileName.c_str(), "rb", encoding.c_str());
   if (in == NULL)
      return;

   callbacks.read_func = ReadFunc;
   callbacks.seek_func = SeekFunc;
   callbacks.close_func = CloseFunc;
   callbacks.tell_func = TellFunc;

   memset(&vf, 0, sizeof(vf));
   if (ov_open_callbacks(in, &vf, NULL, 0, callbacks) < 0)
   {
       tclose(in);
       in = NULL;
       return;
   }

   vi = ov_info(&vf, -1);
   samplesPerSecond = vi->rate;
   channels = vi->channels;
   bitsPerSample = 16;
   duration = (unsigned long)((ov_pcm_total(&vf, -1) * 1000) / vi->rate);
}

VorbisDecode::~VorbisDecode(void)
{
    // The file in should not be closed, since vorbis takes care of closing that.
    if (in)
        ov_clear(&vf);
}

int VorbisDecode::getInfo(unsigned long &duration,
                          unsigned int &samplesPerSecond,
                          unsigned int &bitsPerSample,
                          unsigned int &channels)
{
    if (!in)
        return 0;

    duration = this->duration;
    samplesPerSecond = this->samplesPerSecond;
    bitsPerSample = this->bitsPerSample;
    channels = this->channels;

    return 1;
}

int VorbisDecode::read(char *data, int maxBytes)
{
    int ret, section;

    if (!in)
        return -1;

    for(;;)
    {
        ret = ov_read(&vf, data, maxBytes, 0, 2, 1, &section);
        if (ret < 0)
            continue;
        else
            return ret;
    }
} 

