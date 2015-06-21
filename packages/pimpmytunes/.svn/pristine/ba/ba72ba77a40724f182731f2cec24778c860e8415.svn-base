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

import indexsearch, mcompare
import re
import PyLucene

class ArtistSearch(indexsearch.IndexSearch):
    '''
    This search only searches for an artist.
    '''

    STOP_THRESHOLD = .5

    def __init__(self, indexName, tp):
        indexsearch.IndexSearch.__init__(self, indexName, tp)
        self.featRe = re.compile('( feat.*)')
 
    def getAnalyzer(self):
        return PyLucene.SnowballAnalyzer("English", [])
 
    def getType(self):
        return 'artist';
 
    def getQuery(self, mdata, fileName):

        self.artist = self.normalize(mdata.artist)

        # If the artist has a feat. XYZ following it, nuke it
        if self.featRe.search(self.artist):
            self.artist = self.featRe.sub('', self.artist)
        self.sortName = self.normalize(mdata.sortName)

        if not self.artist: return None

        # Constructing the lucene query like this returns only ONE hit, which is wrong.
        #query = PyLucene.BooleanQuery()
        #for term in self.artist.split():
        #    query.add(PyLucene.TermQuery(PyLucene.Term("ar.name", term)), False, False)

        return PyLucene.QueryParser.parse(self.artist, "ar.name", self.analyzer)
 
    def getScore(self, mdata, doc, rank):
        return (rank >= ArtistSearch.STOP_THRESHOLD, (max(mcompare.sim(doc.get('ar.name'), self.artist), 
                                                          mcompare.sim(doc.get('ar.sortname'), self.sortName)) + rank) / 2)
 
    def printDebug(self, doc, score):
        print "%-30s %-30s %s" % (doc.get("ar.name"), doc.get("ar.sortname"), doc.get("ar.gid"))
