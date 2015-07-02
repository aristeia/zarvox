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

   $Id: wavdecode.h 1390 2005-06-14 17:46:40Z robert $

----------------------------------------------------------------------------*/
#ifndef __WAV_TRM_H_
#define __WAV_TRM_H_

#include <string>
using namespace std;
#include "decode_plugin.h"
#include "fileio.h"

class WavDecode : DecodePlugin
{
    public:

                WavDecode(const string &file, const string &encoding);
       virtual ~WavDecode(void);

       int      getInfo(unsigned long &duration, 
                        unsigned int &samplesPerSecond,
                        unsigned int &bitsPerSample,
                        unsigned int &channels);
       int      read    (char *data, int maxBytes);

    private:

       TFILE        *file;
       string        encoding;
       unsigned int  duration; 
       unsigned int  samplesPerSecond;
       unsigned int  bitsPerSample;
       unsigned int  channels;
};

#endif
