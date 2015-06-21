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

import re, os
import indexsearch, mcompare
import PyLucene

class MissingArtistIdError(Exception):
    pass
 
class FilenameSearch(indexsearch.IndexSearch):
    '''
    A filename search takes the filename and does a dumb search across all the name fields in the lucene index.
    Sounds stupid, but it can find some amazing things some times.
    '''

    STOP_THRESHOLD = .5

    def __init__(self, indexName, tp):
        indexsearch.IndexSearch.__init__(self, indexName, tp)
 
    def getAnalyzer(self):
        return PyLucene.SnowballAnalyzer("English", PyLucene.StopAnalyzer.ENGLISH_STOP_WORDS)

    def getType(self):
        return 'track';
 
    def getQuery(self, mdata, fileName):
        '''
        This helper function crafts a query tree from fields and terms. This makes creating
        differnent subclasses of the same search trivial.
        '''

        text = self.normalize(unicode(os.path.splitext(os.path.basename(fileName))[0], 'utf-8', 'replace'))
        if not text: return None

        try:
            query = PyLucene.MultiFieldQueryParser.parse(text, ['ar.name', 'al.name', 'tr.name'], self.analyzer)
        except PyLucene.JavaError, msg:
            return None

        return query

    def getScore(self, mdata, doc, rank):
        # filter out artist and albums
        if not doc.get('tr.gid'): rank = -1.0
        return (rank >= FilenameSearch.STOP_THRESHOLD, rank)
 
    def printDebug(self, doc, score):
        print "%-40s %-40s" % (doc.get("tr.al_name").encode('utf-8', 'replace'), doc.get("tr.o_name").encode('utf-8', 'replace'))
