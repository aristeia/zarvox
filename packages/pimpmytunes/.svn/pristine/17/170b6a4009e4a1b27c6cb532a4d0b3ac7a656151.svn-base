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

import re
import indexsearch, mcompare
import PyLucene
 
class AlbumSearch(indexsearch.IndexSearch):
    '''
    For the documentation of this class, please refer to the docs of the IndexSearcher class.
    This particular instance provides all the parameters for an album search.
    '''

    STOP_THRESHOLD = .5

    def __init__(self, indexName, tp):
        indexsearch.IndexSearch.__init__(self, indexName, tp)
        self.parenRegexp = re.compile('\(.*?\)$|\[(.*?)\]$')
 
    def getAnalyzer(self):
        return PyLucene.SnowballAnalyzer("English", PyLucene.StopAnalyzer.ENGLISH_STOP_WORDS)

    def getType(self):
        return 'album';
 
    def getQuery(self, mdata, fileName):

        if not mdata.artistId: raise MissingArtistIdError, "This search requires that an aritstid field be set in mdata"
        
        self.album = self.normalize(mdata.album)
        self.noParen = self.normalize(self.parenRegexp.sub('', mdata.album))

        query = PyLucene.BooleanQuery()
        idQuery = PyLucene.TermQuery(PyLucene.Term("ar.gid", mdata.artistId))
        idQuery.setBoost(0.001)
        query.add(idQuery, True, False)
        query.add(PyLucene.TermQuery(PyLucene.Term("al.type", "1")), False, False)

        for term in self.album.split():
            query.add(PyLucene.TermQuery(PyLucene.Term("al.name", term)), False, False)

        for term in self.noParen.split():
            query.add(PyLucene.TermQuery(PyLucene.Term("al.noparen", term)), False, False)

        return query
 
    def getScore(self, mdata, doc, rank):
        '''
        Calculate the similarity between the album name  and album noparen name. Return this value, the max and the rank 
        '''
        r1 = mcompare.sim(doc.get('al.name'), self.album) + rank) / 2
        r2 = mcompare.sim(doc.get('al.noparen'), self.noParen) + rank) / 2
        return (rank >= AlbumSearch.STOP_THRESHOLD, max(r1, r2))
 
    def printDebug(self, doc, score):
        print "%-40s %-40s" % (doc.get("al.o_name"), doc.get("al.noparen"))
