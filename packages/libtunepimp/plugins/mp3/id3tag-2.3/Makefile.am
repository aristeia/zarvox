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
#    $Id: Makefile.am 7487 2006-05-08 23:31:08Z luks $
#
INCLUDES = -I$(top_srcdir)/include/tunepimp-0.5

noinst_LTLIBRARIES = libid3tag23.la
libid3tag23_la_SOURCES = compat.c crc.c debug.c field.c file.c frame.c frametype.c genre.c latin1.c parse.c render.c tag.c ucs4.c utf16.c utf8.c util.c version.c 

EXTRA_DIST = genre.dat

noinst_HEADERS = compat.h crc.h debug.h field.h file.h frame.h frametype.h genre.h global.h id3tag.h latin1.h parse.h render.h tag.h ucs4.h utf16.h utf8.h util.h version.h
