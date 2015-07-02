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

lib_LTLIBRARIES = wma.la
wma_la_SOURCES = wma.cpp wmaattribute.cpp wmaattribute.h wmafile.cpp wmafile.h \
	wmaproperties.cpp wmaproperties.h wmatag.cpp wmatag.h
wma_la_CXXFLAGS = $(TAGLIB_CFLAGS)
wma_la_LDFLAGS = -module -avoid-version
wma_la_LIBADD = ../../lib/utf8/libutf8.la ../../lib/libpluginsupport.la $(TAGLIB_LIBS) -lmusicbrainz

all:
	mkdir -p $(top_srcdir)/examples/plugins
	rm -f $(top_srcdir)/examples/plugins/wma.tpp
	ln -s ../../plugins/wma/.libs/wma.so $(top_srcdir)/examples/plugins/wma.tpp

install-exec-am:

clean distclean:
	rm -f $(top_srcdir)/examples/plugins/wma.tpp
