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

import sys, os, time
import PyLucene
from tunepimp import metadata

MAX_CACHE_ITEMS = 1000
ITEMS_PER_PURGE = 50

class MetadataCache(object):
    '''
    Cache metadata objects (artist and album mdata) so that we don't have to repeatedly fetch them
    from Lucene.
    '''

    def __init__(self):
        self.cache = {}
        self.times = {}

    def get(self, id):
        '''
        Given a metadata id, return the mdata if we have it, None otherwise. The Cache's lastused time is updated
        if the item was successfully looked up
        '''

        if self.cache.has_key(id):
            del self.times[self.cache[id]['lastused']]
            now = time.time()
            self.cache[id]['lastused'] = now
            self.times[now] = id
            #print "cache HIT: %s" % id
            return self.cache[id]['mdata']

        #print "cache MISS: %s" % id

        return None
            
    def add(self, id, mdata):
        '''
        Add a metadata, id pair to the cache.
        '''

        if len(self.cache) >= MAX_CACHE_ITEMS:
            self.trim()

        now = time.time()
        self.cache[id] = { 'mdata' : mdata, 'lastused' : now }
        self.times[now] = id
        #print "cache ADD: %s" % id

    def trim(self):
        '''
        Trip the oldest items in the cache to make more room.
        '''

        keys = self.times.keys()
        keys.sort(cmp)
        for index, key in enumerate(keys):
            if index == ITEMS_PER_PURGE: return
            del self.cache[self.times[key]]
            del self.times[key]

class Lookup(object):
    '''
    lookup retrieves a list or artists or albums from the lucene index. A Metadata structure list is returned.
    '''

    def __init__(self, indexName, tp):
        self.tp = tp

        # the caches are keyed by the artistId/albumId and contain mdata = metadata, lastused = time()
        self.artistCache = MetadataCache()
        self.albumCache = MetadataCache()
        self.analyzer = PyLucene.SnowballAnalyzer("English", PyLucene.StopAnalyzer.ENGLISH_STOP_WORDS)
        try:
            self.index = PyLucene.IndexSearcher(PyLucene.FSDirectory.getDirectory(indexName, False))
        except ValueError:
            raise pimpmytunes.NoSuchIndexError, "Could not open index %s" % indexName
        except PyLucene.JavaError:
            raise pimpmytunes.NoSuchIndexError, "Could not open index %s" % indexName
 
    def lookupArtists(self, artistIdList):
        '''
        Given an artist id, look it up in lucene and then create a Metadata object and return it
        '''

        results = {}
        lookupList = []
        text = ""

        # For some reason, Lucene doesn't find all the terms if you construct a boolean query.
        # It does, if you use query parser
        for artistId in artistIdList:
            mdata = self.artistCache.get(artistId)
            if mdata:
                results[artistId] = mdata
            else:
                text += "%s " % artistId

        if not text: return results

        query = None
        try:
            query = PyLucene.QueryParser.parse(text, "ar.gid", self.analyzer)
        except PyLucene.JavaError, msg:
            print "lookupArtists: query construction failed: %s" % msg
            return None

        hits = []
        try:
            hits = self.index.search(query);
        except PyLucene.JavaError, msg:
            print "lookupArtists: query failed: %s" % msg
            return None

        if not hits: return None

        for i in xrange(len(hits)):
            doc = hits.doc(i)
            mdata = metadata.metadata(self.tp)
            mdata.artist = doc.get('ar.o_name')
            mdata.sortName = doc.get('ar.o_sortname')
            mdata.artistId = doc.get('ar.gid')
            self.artistCache.add(mdata.artistId, mdata)
            results[mdata.artistId] = mdata

        return results

    def lookupAlbums(self, albumIdList):
        '''
        Given an album id, look it up in lucene and then create a Metadata object and return it
        '''

        results = {}
        lookupList = []
        text = ""

        # For some reason, Lucene doesn't find all the terms if you construct a boolean query.
        # It does, if you use query parser
        for albumId in albumIdList:
            mdata = self.albumCache.get(albumId)
            if mdata:
                results[albumId] = mdata
            else:
                text += "%s " % albumId

        if not text: return results

        query = None
        try:
            query = PyLucene.QueryParser.parse(text, "al.gid", self.analyzer)
        except PyLucene.JavaError, msg:
            print "lookupAlbum: query construction failed: %s" % msg
            return None

        hits = []
        try:
            hits = self.index.search(query);
        except PyLucene.JavaError, msg:
            print "lookupAlbum: query failed: %s" % msg
            return None

        if not hits: return None

        for i in xrange(len(hits)):
            doc = hits.doc(i)
            mdata = metadata.metadata(self.tp)
            mdata.album = doc.get('al.o_name')
            mdata.albumId = doc.get('al.gid')
            mdata.totalInSet = int(doc.get('al.tracks'))
            mdata.albumType = int(doc.get('al.type'))
            mdata.albumStatus = int(doc.get('al.status'))
            self.albumCache.add(mdata.albumId, mdata)
            results[mdata.albumId] = mdata

        return results

if __name__ == '__main__':
    cache = MetadataCache()
    cache.add('1', '_1')
    cache.add('2', '_2')
    cache.add('3', '_3')
    cache.add('4', '_4')
    cache.add('5', '_5')
    cache.add('6', '_6')
    cache.get('4')
    cache.add('7', '_7')
    cache.get('7')
    cache.add('8', '_8')
