#
#  TunePimp -- The MusicBrainz tagging clien interface:
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
#    $Id: Makefile.am 8090 2006-07-04 16:49:27Z luks $
#
AUTOMAKE_OPTIONS = foreign

SUBDIRS = libltdl include lib plugins examples 

FEATHERS = $(mbndex_SOURCES) $(DOCS) $(OTHERFILES)

EXTRA_DIST = include/tunepimp-0.5/tp_c.h include/tunepimp-0.5/track.h include/tunepimp-0.5/tunepimp.h \
             include/tunepimp-0.5/context.h include/tunepimp-0.5/defs.h \
	     include/tunepimp-0.5/metadata.h include/tunepimp-0.5/plugin.h \
             AUTHORS COPYING TODO README README.LGPL ChangeLog \
             perl/tunepimp-perl/MANIFEST perl/tunepimp-perl/Changes  \
             perl/tunepimp-perl/Makefile.PL perl/tunepimp-perl/README  \
             perl/tunepimp-perl/const-c.inc perl/tunepimp-perl/const-xs.inc \
             perl/tunepimp-perl/ppport.h perl/tunepimp-perl/tunepimp.pm  \
             perl/tunepimp-perl/tunepimp.xs perl/tunepimp-perl/typemap \
             perl/tunepimp-perl/t/1.t perl/tunepimp-perl/META.yml \
             perl/tunepimp-perl/examples/tp_tagger.pl \
	     python/MANIFEST.in python/COPYING README \
	     python/setup.py python/examples/trm.py  \
	     python/tunepimp/__init__.py python/tunepimp/metadata.py  \
	     python/tunepimp/track.py python/tunepimp/tunepimp.py \
	     config_win32.h win32

snapshot: $(FEATHERS)
	tar -cf - $(FEATHERS) | gzip > $(PACKAGE)-$(VERSION).tar.gz

cvsclean: distclean
	@echo "additonal cleanup for cvs commits"
	rm -f *~
	rm -f $(PACKAGE)-$(VERSION).tar.gz

install-data-local:
	mkdir -p $(DESTDIR)$(libdir)/tunepimp/plugins
	$(INSTALL) -m 0655 examples/plugins/*.tpp $(DESTDIR)$(libdir)/tunepimp/plugins

uninstall-local:
	rm -rf $(libdir)/tunepimp/plugins $(libdir)/tunepimp
	rm -rf $(includedir)/tunepimp
