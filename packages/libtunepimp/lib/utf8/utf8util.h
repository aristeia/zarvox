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

   $Id: utf8util.h 1415 2005-07-02 05:56:41Z robert $

----------------------------------------------------------------------------*/
#ifndef __UTF8UTIL_H
#define __UTF8UTIL_H

#include <string>
using namespace std;

#include "utf8.h"

string utf8Decode(const string &from);
string utf8Encode(const string &from);

/* These are not needed on WIN32 due to the Unicode filename support */
string utf8ToEncoding(const string &from, const string &encoding);
string utf8FromEncoding(const string &from, const string &encoding);

#endif /* __UTF8UTIL_H */
