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
import PyLucene
import Levenshtein
from unac import unac
import pimpmytunes, lookup
from tunepimp import metadata
import mcompare

def convertToMdata(tp, type, doc, supp = None):
    '''
    Given a lucene track document, return an equivalent tunepimp metadata object 
    '''

    mdata = metadata.metadata(tp)
    if type == 'artist':
        mdata.artist = doc.get('ar.name')
        mdata.artistId = doc.get('ar.gid')
        mdata.sortname = doc.get('ar.sortname')
        return mdata

    if type == 'album':
        mdata.artistId = doc.get('al.ar_gid')
        mdata.album = doc.get('al.o_name')
        mdata.albumId = doc.get('al.gid')
        mdata.albumType = int(doc.get('al.type'))
        mdata.albumStatus = int(doc.get('al.status'))
        mdata.totalInSet = int(doc.get('al.tracks'))
        if supp and supp.artistId == mdata.artistId:
            mdata.artist = supp.artist
            mdata.sortName = supp.sortName
        return mdata
   
    if type == 'track':
        mdata.artistId = doc.get('tr.ar_gid')
        mdata.album = doc.get('tr.al_name')
        mdata.albumId = doc.get('tr.al_gid')
        mdata.albumType = int(doc.get('tr.al_type'))
        mdata.track = doc.get('tr.o_name')
        mdata.trackId = doc.get('tr.gid')
        mdata.trackNum = int(doc.get('tr.tnum'))
        mdata.totalInSet = int(doc.get('tr.al_tracks'))
        if supp and supp.artistId == mdata.artistId:
            mdata.artist = supp.artist
            mdata.sortName = supp.sortName
        return mdata
    return None

class IndexSearch(object):
    '''
    IndexSearches is the base class that implements searching a lucene index. Classes must
    derive from this class in order to implement an actual search. The derived classes
    provide all the query info and ranking of search results
    '''

    def __init__(self, indexName, tp):
        self.tp = tp
        self.mcompare = mcompare.MetadataCompare()
        self.alnumRe = re.compile("[^\w\s]")
        self.analyzer = self.getAnalyzer()
        self.lookup = lookup.Lookup(indexName, self.tp)
        try:
            self.index = PyLucene.IndexSearcher(PyLucene.FSDirectory.getDirectory(indexName, False))
        except ValueError:
            raise pimpmytunes.NoSuchIndexError, "Could not open index %s: %s" % (indexName, msg)
        except PyLucene.JavaError, msg:
            raise pimpmytunes.NoSuchIndexError, "Could not open index %s: %s" % (indexName, msg)

    def getType(self):
        '''
        Indicate what type of results this search returns. One of 'artist', 'album' or 'track'.
        '''
        return NotImplemented
 
    def getAnalyzer(self):
        '''
        Return the lucene analyzer to use for searching this index.
        '''
        return NotImplemented
 
    def getQuery(self, mdata, fileName):
        '''
        This method returns a Lucene query object that can be passed to Lucene for immediate searching
        '''
        return NotImplemented
 
 
    def getScore(self, mdata, doc, rank):
        '''
        Given track metadata, lucene document and a lucene rank, return a tuple containing a boolean value 
        whether or not to continue examining hits, and a similarity value of this document when 
        compared to the track metadata.
        '''
        return NotImplemented
 
    def compare(self, w1, w2):
        '''
        Given two tuples of weights returned from the getScores function, rank the
        two tuples. Return standard -1, 0, 1 return values.
        '''
        return cmp(w2[0], w1[0])

    def weighValues(wvPairs):
        '''
        Given a dictionary of parametric values and their corresponding decimal weights, 
        calculate a parametric overall weight.
        '''
        totalParam = 0.0
        totalWeight = 0.0
        for pair in wvPairs:
            totalWeight += pair[1]
            totalParam += pair[0] * pair[1]
 
        return totalParam / totalWeight

    def normalize(self, query):
        '''
        Return the normalized version of this query. Normalization entails accent removal, non alpha
        numeric character removal and lower casing the query.
        '''
        text = query.strip()
        text = text.replace('_', ' ')
        text = text.replace('-', ' ')
        text = unac.unac_string(text)
        text = text.lower()
        return self.alnumRe.sub(u"", text)

 
    def close(self):
        '''
        Close the index when done searching.
        '''
        self.index.close();
 
    def augmentMatches(self, matches):

        artists = {}
        albums = {}
        for mdata in matches:
            artists[mdata.artistId] = 1
            albums[mdata.albumId] = 1

        artistResults = self.lookup.lookupArtists(artists.keys())
        albumResults = self.lookup.lookupAlbums(albums.keys())

        # TODO: Add albums type and others that are needed
        for mdata in matches:
            if artistResults:
                mdata.artist = artistResults[mdata.artistId].artist
                mdata.sortName = artistResults[mdata.artistId].sortName
            if albumResults:
                mdata.album = albumResults[mdata.albumId].album

        return matches

    def match(self, mdata, fileName, debug, maxHits):
        '''
        Carry out the actual database search to match the track to MB data.
        '''
 
        matches = []
        query = None
        hits = []

        # Get the query, normalize it and then feed it to lucene
        try:
            query = self.getQuery(mdata, fileName)
        except PyLucene.JavaError, msg:
            print "%s: Cannot form query: %s" % (self.__class__.__name__, msg)
            return matches

        if not query: return matches

        if debug: print "query: %s" % query

        try:
            hits = self.index.search(query);
        except PyLucene.JavaError, msg:
            print "%s: Cannot form query: %s" % (self.__class__.__name__, msq)
            return matches

        if not hits: 
            return matches

        temp = []
        for i in xrange(min(hits.length(), maxHits)):
            doc = hits.doc(i)

            cont, score = self.getScore(mdata, doc, hits.score(i))
            if score < 0.0: continue

            ddata = convertToMdata(self.tp, self.getType(), doc, mdata)
            if self.getType() == 'track':
                # For complete tracks, use our similarity function
                temp.append(ddata)
            else:
                # For albums and artists, use the score from the search
                matches.append((int(score * 100), ddata))

            if not cont: break

        if self.getType() == 'track':
            temp = self.augmentMatches(temp)
            for ddata in temp:
                matches.append((self.mcompare.compare(ddata, mdata), ddata))

        if debug: print
        matches.sort(self.compare)
        return matches
