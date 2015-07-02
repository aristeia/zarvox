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

   $Id: metadata_plugin.h 8359 2006-08-07 20:34:50Z luks $

----------------------------------------------------------------------------*/

#ifndef METADATA_PLUGIN_H
#define METADATA_PLUGIN_H

#include <string>

class MetadataPlugin
{
    public:

                MetadataPlugin() {};
       virtual ~MetadataPlugin(void) {};

       virtual bool write(const std::string  &fileName,
                          const Metadata    &data,
                          bool               clear) = 0;
       virtual bool read (const std::string  &fileName,
                          Metadata          &data) = 0;

       void getError(std::string &error) { error = errString; };

    protected:

       std::string errString;
};

#endif
