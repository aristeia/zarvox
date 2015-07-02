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

   $Id: plugins.cpp 1300 2004-05-06 22:54:33Z robert $

----------------------------------------------------------------------------*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <dirent.h>
#include "../libltdl/ltdl.h"
#include "plugins.h"

#include <map>
using namespace std;

/*------------------------------------------------------------------------- */

#define DB printf("%s:%d\n", __FILE__, __LINE__);

/*------------------------------------------------------------------------- */
#define ERROR_FILENOTFOUND   "File not found."

/*------------------------------------------------------------------------- */

Plugins::Plugins(void)
{
   lt_dlinit();
}

Plugins::~Plugins(void)
{
   unload();
   lt_dlexit();
}

int Plugins::load(const char *path, bool printDebugInfo)
{
   DIR           *dir;
   struct dirent *entry;
   int            j, i, numFormats;
   char          *ptr, file[MAX_PATH], init_func[255];
   Plugin        *(*init_function)(void);

   dir = opendir(path);
   if (dir == NULL)
      return 0;

   for(;;)
   {
       PluginInfo info;

       /* Scan the given dir for plugins */
       entry = readdir(dir);
       if (!entry)
          break;

       ptr = strrchr(entry->d_name, '.');
       if (!ptr || strcasecmp(ptr, ".tpp"))
          continue;

       sprintf(file, "%s/%s", path, entry->d_name);
       if (printDebugInfo)
           fprintf(stderr, "  %s: ", file);

       /* Found one, lets open it */
       info.handle = lt_dlopen(file);
       if (info.handle == NULL)
       {
           if (printDebugInfo)
               fprintf(stderr, "Cannot load plugin %s. (%s)\n", 
               file, lt_dlerror());
           continue;
       }
       strcpy(info.file, entry->d_name);
       strcpy(init_func, entry->d_name);
       ptr = strrchr(init_func, '.');
       if (ptr)
           *ptr = 0;
       strcat(init_func, "InitPlugin");

       /* Opened plugin ok, now locate our entry function */
       init_function = (Plugin *(*)(void))lt_dlsym((lt_dlhandle_struct *)info.handle, init_func);
       if (init_function == NULL)
       {
           if (printDebugInfo)
               fprintf(stderr, "Cannot find entry point in %s (%s).\n", file, lt_dlerror());
           lt_dlclose((lt_dlhandle_struct *)info.handle);
           continue;
       }

       /* Init the plugin and get the methods provided by the plugin */
       info.methods = (*init_function)();
       if (info.methods == NULL)
       {
           lt_dlclose((lt_dlhandle_struct *)info.handle);
           if (printDebugInfo)
               fprintf(stderr, "Cannot retrieve supported methods from %s.\n", file);
           continue;
       }

       numFormats = info.methods->getNumFormats();
       for(i = 0; i != numFormats; i++)
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
           fprintf(stderr, "%s ", info.methods->getName());
           fprintf(stderr, "(%s)\n", info.methods->getVersion());
       }

       /* Check to make sure that the given plugin hasnt already been loaded */
       for(j = plugins.size() - 1; j >= 0; j--)
       {
           if (!strcmp(plugins[j].file, info.file))
           {
               if (printDebugInfo)
                  fprintf(stderr, "  [Plugin %s has already been loaded. "
                       "Skipping.]\n", info.file);
               info.methods->shutdown();
               lt_dlclose((lt_dlhandle_struct *)info.handle);
               break;
           }
       }

       /* If we didn't already this plugin loaded, increment our counters */
       if (j < 0)
           plugins.push_back(info);
   }
   closedir(dir);

   return plugins.size();
}

void Plugins::unload(void)
{
   vector<PluginInfo>::iterator i;

   for(i = plugins.begin(); i != plugins.end(); i++)
   {
       if ((*i).handle)
       {
           (*i).methods->shutdown();
           lt_dlclose((lt_dlhandle_struct *)(*i).handle);
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
