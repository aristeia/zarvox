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

   $Id: flac_meta.h 1448 2006-01-14 00:29:50Z luks $

----------------------------------------------------------------------------*/
//---------------------------------------------------------------------------
// This code is based on vorbis.cpp and vorbis.cpp from FreeAmp. EMusic.com
// has released this code into the Public Domain. 
// (Thanks goes to Brett Thomas, VP Engineering Emusic.com)
//---------------------------------------------------------------------------
// Portions (c) Copyright Kristian G. Kvilekval, and permission to use in LGPL
// library granted on February 25th, 2003

#ifndef INCLUDED_FLAC_META_H
#define INCLUDED_FLAC_META_H

#include <string>
#include <assert.h>
using namespace std;

#include "metadata.h"
#include "metadata_plugin.h"

class FLAC : public MetadataPlugin
{
    public:

                     FLAC(const char *encoding) : encoding(encoding) {};
       virtual      ~FLAC(void) {};

       bool          write  (const string &fileName, const Metadata &metadata, bool clear);
       bool          read   (const string &fileName, Metadata &metadata);

       void          getError(string &error) { error = errString; };

    private:

       const string ConvertToISO(const char *utf8);
       string   encoding;
       string   errString;
};

#endif
