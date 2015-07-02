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

   $Id: plugins_win32.cpp 1326 2004-06-30 20:45:57Z robert $

----------------------------------------------------------------------------*/
/* (PD) 2001 The Bitzi Corporation
 * Please see file COPYING or http://bitzi.com/publicdomain 
 * for more info.
 */
/*------------------------------------------------------------------------- */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <windows.h>
#include <map>
using namespace std;
#include "../config_win32.h"

#include "plugins.h"

/*------------------------------------------------------------------------- */
#ifndef MAX_PATH
   #define MAX_PATH    1024
#endif
#define DB printf("%s:%d\n", __FILE__, __LINE__);
#define ERROR_FILENOTFOUND   "File not found."

/*------------------------------------------------------------------------- */
typedef Plugin *(CALLBACK* InitFunction)(void);
/*------------------------------------------------------------------------- */

Plugins::Plugins(void)
{
}

Plugins::~Plugins(void)
{
   unload();
}

int Plugins::load(const char *path, bool printDebugInfo)
{
   WIN32_FIND_DATA  find;
   HANDLE           hFind;
   int              count = 0, j;
   char            *ptr, file[MAX_PATH];
   InitFunction     init_function;

   sprintf(file, "%s\\*.tpp", path);
   hFind = FindFirstFile(file, &find);
   if (hFind == INVALID_HANDLE_VALUE)
      return 0;

   for(j = 0;; j++)
   {
       PluginInfo info;

       if (j > 0)
          if (!FindNextFile(hFind, &find))
              break;

       ptr = strrchr(find.cFileName, '.');
       if (!ptr || strcasecmp(ptr, ".tpp"))
          continue;

       if (printDebugInfo)
           printf("  %s: ", find.cFileName);
       sprintf(file, "%s/%s", path, find.cFileName);

       /* Found one, lets open it */
       info.handle = LoadLibrary(file);
       if (info.handle == NULL)
       {
           if (printDebugInfo)
               printf("Cannot load plugin %s.\n", file);
           continue;
       }
       strcpy(info.file, find.cFileName);

       /* Opened plugin ok, now locate our entry function */
       init_function = (InitFunction)GetProcAddress(info.handle, "initPlugin");
       if (init_function == NULL)
       {
           FreeLibrary(info.handle);
           if (printDebugInfo)
               printf("Cannot find entry point in %s.\n", file);
           continue;
       }

       /* Init the plugin and get the methods provided by the plugin */
       info.methods = init_function();
       if (info.methods == NULL)
       {
           FreeLibrary(info.handle);
           if (printDebugInfo)
               printf("Cannot retrieve supported methods from %s.\n", file);
           continue;
       }

       /* Now get the formats handled by the plugin */
       int numFormats = info.methods->getNumFormats();
       for(int i = 0; i != numFormats; i++)
       {
           CapInfo cap;
           char ext[TP_EXTENSION_LEN];
           char desc[TP_PLUGIN_DESC_LEN];

           info.methods->getFormat(i, ext, desc, &cap.functions);
           cap.ext = string(ext);
           cap.desc = string(desc);
           info.caps.push_back(cap);
       }

       if (printDebugInfo)
       {
           printf("%s ", info.methods->getName());
           printf("(%s)\n", info.methods-> getVersion());
       }

       /* Check to make sure that the given plugin hasnt already been loaded */
       for(j = plugins.size() - 1; j >= 0; j--)
       {
           if (!strcmp(plugins[j].file, info.file))
           {
               if (printDebugInfo)
                  printf("  [Plugin %s has alaready been loaded. Skipping.]\n", info.file);
                
               info.methods->shutdown();
               FreeLibrary(info.handle);
               break;
           }
       }

       /* If we didn't already this plugin loaded, increment our counters */
       if (j < 0)
           plugins.push_back(info);

   }
   FindClose(hFind);

   return count;
}

void Plugins::unload(void)
{
    vector<PluginInfo>::iterator i;

    for(i = plugins.begin(); i != plugins.end(); i++)
    {
        if ((*i).handle)
        {
            (*i).methods->shutdown();
            FreeLibrary((*i).handle);
            (*i).handle = NULL;
        }
    }
}

Plugin *Plugins::get(const string &extension, int functionFlags)
{
    vector<PluginInfo>::iterator i;
    vector<CapInfo>::iterator j;

    for(i = plugins.begin(); i != plugins.end(); i++)
    {
        for(j = (*i).caps.begin(); j != (*i).caps.end(); j++)
        {
            if (strcasecmp((*j).ext.c_str(), extension.c_str()) == 0 &&
                    ((*j).functions & functionFlags) == functionFlags)
                return (*i).methods;
        }
    }

    return NULL;
}

void Plugins::getSupportedExtensions(vector<string> &extList)
{
   vector<PluginInfo>::iterator i;
   vector<CapInfo>::iterator j;
   map<string, int> exts;
   map<string, int>::iterator k;

   for(i = plugins.begin(); i != plugins.end(); i++)
   {
       for(j = (*i).caps.begin(); j != (*i).caps.end(); j++)
       {
          exts[(*j).ext] = 1;
       }
   }

   extList.clear();
   for(k = exts.begin(); k != exts.end(); k++)
       extList.push_back((*k).first);
}
