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
import tracksearch
from musicbrainz2.luceneindex import trackindex

class MissingArtistIdError(Exception):
    pass
 
class AlbumTrackSearch(indexsearch.IndexSearch):
    '''
    Album track search carries out a search on an album and a track at the same time. Optionally
    track duration will also be searched on.
    '''

    STOP_THRESHOLD = .5
    ALBUM_ACCEPT_THRESHOLD = .6
    TRACK_ACCEPT_THRESHOLD = .6

    def __init__(self, indexName, tp):
        indexsearch.IndexSearch.__init__(self, indexName, tp)
 
    def getAnalyzer(self):
        return PyLucene.SnowballAnalyzer("English", PyLucene.StopAnalyzer.ENGLISH_STOP_WORDS)
 
    def getType(self):
        return 'track';
 
    def createQuery(self, albumField, album, trackField, track, mdata):
        '''
        This helper function crafts a query tree from fields and terms. This makes creating
        differnent subclasses of the same search trivial.
        '''

        query = "tr.ar_gid:%s^0.001 tr.al_type:1^4 " % mdata.artistId
        if mdata.duration: 
            qdur = int(mdata.duration) / trackindex.TI_DURATION_QUANT
            query += "tr.quantlen:%d tr.quantlen:%d tr.quantlen:%d " % (qdur -1, qdur, qdur + 1)
 
        for term in album.split():
            query += "%s:%s " % (albumField, term)

        for term in track.split():
            query += "%s:%s " % (trackField, term)

        return PyLucene.QueryParser.parse(query, "tr.name", self.analyzer)

    def getQuery(self, mdata, fileName):

        if not mdata.artistId: raise MissingArtistIdError, "This search requires that an aritstid field be set in mdata"

        self.album = self.normalize(mdata.album)
        self.albumField = "tr.al_name"
        self.track = self.normalize(mdata.track)
        self.trackField = "tr.name"

        return self.createQuery("tr.al_name", self.album, "tr.name", self.track, mdata)
 
    def getScore(self, mdata, doc, rank):
        '''
        Calculate the similarity between the album name  and album noparen name. Return this value, the max and the rank 
        '''
        # Check to see if the album/track meet the minimum thresholds
        alSim = mcompare.sim(doc.get(self.albumField), self.album) 
        trSim = mcompare.sim(doc.get(self.trackField), self.track)
        #print "'%s' '%s' -> %.3f" % (doc.get(self.albumField), self.album, alSim)
        #print "'%s' '%s' -> %.3f" % (doc.get(self.trackField), self.track, trSim)
        if alSim < AlbumTrackSearch.ALBUM_ACCEPT_THRESHOLD or \
           trSim < AlbumTrackSearch.TRACK_ACCEPT_THRESHOLD:
            return (rank >= AlbumTrackSearch.STOP_THRESHOLD, -1.0)
   
        durSim = -1.0
        dur = doc.get('tr.length')
        if dur:
            durSim = tracksearch.durationSim(int(doc.get('tr.length')), mdata.duration) 
        if durSim >= 0.0:
            return (rank >= AlbumTrackSearch.STOP_THRESHOLD, (alSim + trSim + durSim + rank) / 4)
        else:
            return (rank >= AlbumTrackSearch.STOP_THRESHOLD, (alSim + trSim + rank) / 3)
 
    def printDebug(self, doc, score):
        print "%-40s %-40s" % (doc.get("tr.al_name"), doc.get("tr.o_name"))

