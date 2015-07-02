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
#    $Id: Makefile.am 1423 2005-09-16 08:05:23Z robert $
#
noinst_LTLIBRARIES = libutf8.la

if DARWIN
libutf8_la_SOURCES = utf8_darwin.c utf8.h utf8util.cpp iconvert.c
libutf8_la_LIBADD = -liconv
EXTRA_DIST = charmaps.h charset.c charset.h charsetmap.h iconvert.c utf8.c utf8util.h
else
libutf8_la_SOURCES = charmaps.h charset.c charset.h charsetmap.h iconvert.c utf8.c utf8.h utf8util.cpp utf8util.h
EXTRA_DIST = utf8_darwin.c 
endif
