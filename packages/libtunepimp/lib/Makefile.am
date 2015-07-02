#  TunePimp -- The MusicBrainz tagging client interface:
#
#              "Let a thousand taggers bloom!"
#
#  Copyright (C) 2003 Robert Kaye
#  
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#  
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#  
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#    $Id: Makefile.am 8685 2006-11-28 20:34:01Z luks $
#
AUTOMAKE_OPTIONS = foreign

SUBDIRS = utf8 threads

INCLUDES = -I$(top_srcdir)/include/tunepimp-0.5 -Ithreads/posix
lib_LTLIBRARIES = libtunepimp.la

libtunepimp_la_SOURCES = tunepimp.cpp filecache.cpp analyzer.cpp dirsearch.cpp metadata.cpp astrcmp.c track.cpp write.cpp c_wrapper.cpp watchdog.cpp plugins.cpp readmeta.cpp fileio.cpp protocol.cpp

EXTRA_DIST = threads/win32/mutex.h threads/win32/mutex.cpp \
	threads/win32/semaphore.h threads/win32/semaphore.cpp \
	threads/win32/thread.h threads/win32/thread.cpp \
	debug.cpp debug.h fileio_win32.cpp plugins_win32.cpp

# Here are a set of rules to help you update your library version information:
#  Scheme: current:revsion:age
#  1. Start with version information of `0:0:0' for each libtool library.
#  2. Update the version information only immediately before a public release 
#     of your software. More frequent updates are unnecessary, and only 
#     guarantee that the current interface number gets larger faster.
#  3. If the library source code has changed at all since the last update, 
#     then increment revision (`c:r:a' becomes `c:r+1:a').
#  4. If any interfaces have been added, removed, or changed since the last 
#     update, increment current, and set revision to 0.
#  5. If any interfaces have been added since the last public release, then 
#     increment age.
#  6. If any interfaces have been removed since the last public release, then 
#     set age to 0. 
#  Version history:
#  0:0:0 - Initial version for 0.1.x
#  1:0:0 - TunePimp implementation for version 0.2.x
#  2:0:0 - TunePimp implementation for version 0.3.x
#  3:0:0 - TunePimp implementation for version 0.4.x
#  4:0:0 - TunePimp implementation for alpha releases of version 0.5.0
#  5:0:0 - TunePimp implementation for version 0.5.0
#  5:1:0 - TunePimp implementation for version 0.5.1
libtunepimp_la_LDFLAGS = -version-info 5:3:0
libtunepimp_la_LIBADD = threads/posix/libtpthread.la utf8/libutf8.la $(LIBLTDL) -lm

noinst_LTLIBRARIES = libpluginsupport.la
libpluginsupport_la_SOURCES = metadata.cpp fileio.cpp

noinst_HEADERS = analyzer.h dirsearch.h astrcmp.h filecache.h write.h watchdog.h readmeta.h plugins.h protocol.h
