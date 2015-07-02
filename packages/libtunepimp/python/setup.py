#!/usr/bin/env python
#---------------------------------------------------------------------------
#
#   libtunepimp -- The MusicBrainz tagging library.  
#                  Let a thousand taggers bloom!
#   
#   Copyright (C) Robert Kaye 2003
#   
#   This file is part of libtunepimp.
#
#   libtunepimp is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   libtunepimp is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with libtunepimp; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#   $Id: setup.py 7314 2006-04-22 20:15:08Z luks $
#
#---------------------------------------------------------------------------

from distutils.core import setup, Extension
import os.path

if not os.path.exists(os.path.join('tunepimp', '__init__.py')):
	print "ERROR: Please run ../configure before installing this package."
	raise ValueError

from tunepimp import __version__

setup(name="tunepimp",
      version=__version__,
      description="MusicBrainz TunePimp Extension",
      author="Robert Kaye",
      author_email="rob@eorbit.net",
      url="http://www.musicbrainz.org",
      packages = ['tunepimp'],
     )
