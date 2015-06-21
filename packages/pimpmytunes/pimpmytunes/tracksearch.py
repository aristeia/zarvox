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
from musicbrainz2.luceneindex import trackindex

# TODO: If input has no duration, tracks with no duration are favored

class MissingArtistIdError(Exception):
    pass

def durationSim(trackA, trackB):
    '''
    Calculate the duration between two tracks and return a value between 0.0 and 1.0. If either
    one of the track durations is zero, return -1
    '''

    if not trackA or not trackB: return -1.0

    diff = abs(trackA - trackB)
    if diff > 60000: return 0.0

    return 1.0 - (float(diff) / 60000.0)
 
class TrackSearch(indexsearch.IndexSearch):
    '''
    Carry out a track search with option track duration. Consider no album bits.
    '''

    STOP_THRESHOLD = .5

    def __init__(self, indexName, tp):
        indexsearch.IndexSearch.__init__(self, indexName, tp)
 
    def getAnalyzer(self):
        return PyLucene.SnowballAnalyzer("English", PyLucene.StopAnalyzer.ENGLISH_STOP_WORDS)
 
    def getType(self):
        return 'track';
 
    def createQuery(self, trackField, track, mdata):
        '''
        This helper function crafts a query tree from fields and terms. This makes creating
        differnent subclasses of the same search trivial.
        '''
        query = "tr.ar_gid:%s^0.001 tr.al_type:1^10 " % mdata.artistId
        if mdata.duration: 
            qdur = int(mdata.duration) / trackindex.TI_DURATION_QUANT
            query += "tr.quantlen:%d tr.quantlen:%d tr.quantlen:%d " % (qdur -1, qdur, qdur + 1)

        for term in track.split():
            query += "%s:%s " % (trackField, term)

        return PyLucene.QueryParser.parse(query, "tr.name", self.analyzer)

    def getQuery(self, mdata, fileName):

        if not mdata.artistId: raise MissingArtistIdError, "This search requires that an aritstid field be set in mdata"

        self.track = self.normalize(mdata.track)
        self.trackField = "tr.name"

        return self.createQuery("tr.name", self.track, mdata)
 
    def getScore(self, mdata, doc, rank):
        trSim = mcompare.sim(doc.get(self.trackField), self.track)
        durSim = -1.0
        if doc.get('tr.length'):
            durSim = durationSim(int(doc.get('tr.length')), mdata.duration) 
        if durSim >= 0.0:
            return (rank >= TrackSearch.STOP_THRESHOLD, (trSim + durSim + rank) / 3)
        else:
            return (rank >= TrackSearch.STOP_THRESHOLD, (trSim + rank) / 2)
 
    def printDebug(self, doc, score):
        print "%-40s %-40s" % (doc.get("tr.al_name"), doc.get("tr.o_name"))

class TrackSearchTrackNoParen(TrackSearch):
    '''
    This particular instance provides all the parameters for a track search where the track has been
    stripped of parens
    '''

    def __init__(self, indexName):
        TrackSearch.__init__(self, indexName)
        self.parenRegexp = re.compile('\(.*?\)$|\[(.*?)\]$')
 
    def getQuery(self, mdata, fileName):

        if not mdata.artistId: raise MissingArtistIdError, "This search requires that an aritstId field be set in mdata"

        self.track = self.normalize(self.parenRegexp.sub('', mdata.track))
        self.trackField = "tr.noparen"

        return self.createQuery(self.trackField, self.track, mdata)
