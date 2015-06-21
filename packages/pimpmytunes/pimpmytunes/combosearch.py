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
 
class ComboSearch(indexsearch.IndexSearch):
    '''
    A combo search takes the metadata from the track and the track duration and does a dumb
    search across all the name fields in the lucene index.
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

        count = 0
        if mdata.artist != '': count += 1
        if mdata.album != '': count += 1
        if mdata.track != '': count += 1

        if count < 2: return None
        text = self.normalize(u"%s %s %s" % (mdata.artist, mdata.album, mdata.track))
        if not text: return None

        query = PyLucene.BooleanQuery()
        query.add(PyLucene.MultiFieldQueryParser.parse(text, ['ar.name', 'al.name', 'tr.name'], self.analyzer), False, False)
        if mdata.duration: 
            qdur = int(mdata.duration) / 5000
            query.add(PyLucene.TermQuery(PyLucene.Term("tr.quantlen", unicode(qdur - 1))), False, False)
            query.add(PyLucene.TermQuery(PyLucene.Term("tr.quantlen", unicode(qdur))), False, False)
            query.add(PyLucene.TermQuery(PyLucene.Term("tr.quantlen", unicode(qdur + 1))), False, False)

        return query

    def getScore(self, mdata, doc, rank):
        # filter out artist and albums
        if not doc.get('tr.gid'): rank = -1.0
        return (rank >= ComboSearch.STOP_THRESHOLD, rank)
 
    def printDebug(self, doc, score):
        print "%-40s %-40s" % (doc.get("tr.al_name").encode('utf-8', 'replace'), doc.get("tr.o_name").encode('utf-8', 'replace'))
