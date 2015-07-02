#
#  TunePimp -- The MusicBrainz tagging clien interface:
#              "Let a thousand taggers bloom!"
#
#  Copyright (C) 2005 Lukas Lalinsky
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
#
#
INCLUDES = -I$(top_srcdir)/include/tunepimp-0.5 $(INCLTDL) 

lib_LTLIBRARIES = mp4.la
mp4_la_SOURCES = mp4.cpp
mp4_la_LDFLAGS = -module -avoid-version
mp4_la_LIBADD = ../../lib/utf8/libutf8.la ../../lib/libpluginsupport.la -lmp4v2 -lmusicbrainz

all:
	mkdir -p $(top_srcdir)/examples/plugins
	rm -f $(top_srcdir)/examples/plugins/mp4.tpp
	ln -s ../../plugins/mp4/.libs/mp4.so $(top_srcdir)/examples/plugins/mp4.tpp

install-exec-am:

clean distclean:
	rm -f $(top_srcdir)/examples/plugins/mp4.tpp
