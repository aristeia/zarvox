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

   $Id: plugins.h 1324 2004-06-24 19:21:19Z robert $

----------------------------------------------------------------------------*/
#ifndef PLUGINS_H
#define PLUGINS_H

#include <vector>
#include <string>
using namespace std;
#include "plugin.h"
#include "tp_c.h"

#ifndef MAX_PATH
#define MAX_PATH    1024
#endif

struct CapInfo
{
    string ext;
    string desc;
    int    functions;
};

class PluginInfo
{

      public:

            PluginInfo(void) { methods = NULL; handle = NULL; file[0] = 0; };
           ~PluginInfo(void) {};

            Plugin         *methods;
            char            file[MAX_PATH];
            vector<CapInfo> caps;

#ifdef WIN32
            HMODULE         handle;
#else
            void           *handle;
#endif
};

class Plugins
{
    public:

                Plugins               (void);
       virtual ~Plugins               (void);

       int      load                  (const char *path, bool printDebugInfo = false);
       void     unload                (void);

       int      getNumPlugins         (void) { return plugins.size(); };
       Plugin  *get                   (const string &extension, int functionFlags);
       void     getSupportedExtensions(vector<string> &extList);

    private:

       vector<PluginInfo> plugins;
};

/*-------------------------------------------------------------------------*/

#endif
