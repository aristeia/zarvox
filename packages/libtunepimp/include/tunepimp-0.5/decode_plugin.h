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

   $Id: decode_plugin.h 8359 2006-08-07 20:34:50Z luks $

----------------------------------------------------------------------------*/
#ifndef DECODE_PLUGIN_H
#define DECODE_PLUGIN_H

#include <string>

class DecodePlugin
{
    public:

                DecodePlugin(void) {};
       virtual ~DecodePlugin(void) {};

       virtual int      getInfo(unsigned long &duration, 
                        unsigned int &samplesPerSecond,
                        unsigned int &bitsPerSample,
                        unsigned int &channels) = 0;
       virtual int      read    (char *data, int maxBytes) = 0;
       virtual void     getError(std::string &err) { err = this->errorString; };

    protected:

       std::string        errorString;
};

#endif
