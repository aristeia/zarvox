#!/usr/bin/env python
#---------------------------------------------------------------------------
#
#   Pimp My Tunes -- The MusicBrainz command line tagger.
#                    Let a gazllion tunes be tagged!
#   
#   Copyright (C) Robert Kaye 2005
#   
#   This file is part of pimpmytunes.
#
#   pimpmytunes is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   pimpmytunes is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with pimpmytunes; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#---------------------------------------------------------------------------

import sys, os, getopt, re
import readline

class QueryReader(object):
    '''
    This class has mostly been subsumed into pimpmytunes.py -- the standalone search tool still uses it,
    but that will also be subsumed into pimpmytunes.py. Your days are nubered queryreader.py!!
    '''


    def __init__(self, searchTool, cmdPrefix = ''):
        self.searchTool = searchTool
        self.detailsRe = re.compile("^\.\d+")
        self.cmdPrefix = cmdPrefix

    def readQueries(self):
        while 1:
            try:
                line = raw_input(">")
            except KeyboardInterrupt:
                break
            except EOFError:
                print
                return "q"

            if self.detailsRe.search(line):
                self.searchTool.details(int(line[1:]))
                continue

            if line.startswith('\\d'):
                self.searchTool.setDefaultField(line[3:])
                print "Default field is now: '%s'" % line[3:]
                continue

            if line.startswith('\\f'):
                fields = line[3:].split(' ')
                self.searchTool.setDefaultFields(fields)
                print "Default fields are now:", fields
                continue

            if line == '\\s': 
                self.searchTool.useMultiFields(False)
                print "Using standard (single field) query parser"
                continue

            if line == '\\m': 
                self.searchTool.useMultiFields(True)
                print "Using multi field query parser"
                continue

            if self.cmdPrefix:
                if line.startswith(self.cmdPrefix):
                    line = line[1:]
                    self.searchTool.match(line, 25)
                else:
                    return line
            else:
                if line == '\\q': break
                self.searchTool.match(line, 25)

        print
        return ''
