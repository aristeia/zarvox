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

   $Id: id3_meta.h 1390 2005-06-14 17:46:40Z robert $

----------------------------------------------------------------------------*/

#ifndef MBID3_H
#define MBID3_H

#include <string>
using namespace std;
#include "id3tag/id3tag.h"
#include "metadata.h"
#include "metadata_plugin.h"
#include "mp3.h"

class ID3 : public MetadataPlugin
{
    public:

           ID3(bool writeV1, ID3_Encoding enc, const string &encoding);

       bool write(const string  &fileName,
                  const Metadata    &data,
                  bool               clear);
       bool read (const string  &fileName,
                  Metadata          &data);

    private:

       string     getText        (struct id3_tag *tag, const char *frameName);
       string     getUserText    (struct id3_tag *tag, const char *userTextName);
       string     getUniqueFileId(struct id3_tag *tag, const char *ufidName);

       bool       setUniqueFileId(struct id3_tag *tag, 
                                  const char *ufidName, 
                                  const string &id);
       bool       setUserText    (struct id3_tag *tag, 
                                  const char *userTextName, 
                                  const string &text);
       bool       setText(struct id3_tag *tag, 
                                  const char *frameName,
                                  const string &text);

       bool                   writeV1;
       string                 encoding;
       ID3_Encoding           enc;
       id3_field_textencoding id3Encoding;
};

#endif
