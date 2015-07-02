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

   $Id: mp3decode.h 1390 2005-06-14 17:46:40Z robert $

----------------------------------------------------------------------------*/
#ifndef __MP3_DECODE_H_
#define __MP3_DECODE_H_

#include <string>
using namespace std;
#include "mad.h"
#include "decode_plugin.h"
#include "fileio.h"

#define INPUT_BUFFER_SIZE   (5*8192)
#define OUTPUT_BUFFER_SIZE  8192    /* Must be an integer multiple of 4. */

class MP3Decode : public DecodePlugin
{
    public:

                MP3Decode(const string &file, const string &encoding);
       virtual ~MP3Decode(void);

       int      getInfo(unsigned long &duration, 
                        unsigned int &samplesPerSecond,
                        unsigned int &bitsPerSample,
                        unsigned int &channels);
       int      read    (char *data, int maxBytes);

    private:

       TFILE        *file;
       unsigned long duration; 
       unsigned int  samplesPerSecond;
       unsigned int  bitsPerSample;
       unsigned int  channels;
       string        encoding;

       struct mad_stream    Stream;
       struct mad_frame     Frame;
       struct mad_synth     Synth;
       mad_timer_t          Timer;
       unsigned char        InputBuffer[INPUT_BUFFER_SIZE];
       const unsigned char *OutputBufferEnd;
       unsigned long        FrameCount, id3v1TagOffset, curOffset;
};

#endif
