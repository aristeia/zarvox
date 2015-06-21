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
import readline
from unac import unac
import queryreader, indent, indexsearch, pimpmytunes

class NoSuchIndexError(ValueError):
   pass

class SearchTool(object):
   '''
   This class carries out the command line searches for pmt.
   '''

   def __init__(self, indexName, tp):

       self.tp = tp
       self.threshold = .1
       self.colDefs = { 
                         'artist':[ 'ar.gid', 'ar.o_name', 'ar.o_sortname' ],
                         'album':[ 'al.ar_gid', 'al.gid', 'al.o_name', 'al.type', 'al.noparen', 'al.tracks', 'al.status' ],
                         'track':[ 'tr.al_name', 'tr.al_type', 'tr.o_name', 'tr.tnum', 'tr.al_tracks', 'tr.length',   
                                   'tr.quantlen' ]
                       }
       self.count = 0
       self.usedSum = 0
       self.useMulti = True
       self.defaultField = "ar.name"
       self.defaultMultiFields = ["ar.name", "al.name", "tr.name"]
       self.hits = None
       self.artists = []
       self.albums = []
       self.tracks = []

       self.analyzer = PyLucene.SnowballAnalyzer("English", [])
       try:
           self.index = PyLucene.IndexSearcher(PyLucene.FSDirectory.getDirectory(indexName, False))
       except ValueError:
           raise NoSuchIndexError

   def close(self):
       self.index.close();

   def useMultiFields(self, multi):
       ''' 
       If set, use lucene's MultiFieldQueryParser
       '''
       self.useMulti = multi

   def setDefaultField(self, default):
       ''' 
       If set, use lucene's QueryParser for searching on one default field
       '''
       self.defaultField = default

   def setDefaultMultiFields(self, fields):
       '''
       The multi fields searched when the users specifies no multi fields
       '''
       self.defaultMultiFields = fields

   def search(self, query, artistIdRest):
       '''
       Carry out a search, with an optional artistId restraint. Return PyLucene hits 
       '''

       boolQuery = PyLucene.BooleanQuery()
       restQuery = None
       if artistIdRest:
           boolQuery.add(PyLucene.TermQuery(PyLucene.Term("al.ar_gid", artistIdRest)), False, False)
           boolQuery.add(PyLucene.TermQuery(PyLucene.Term("tr.ar_gid", artistIdRest)), False, False)

       parsedQuery = None
       if self.useMulti:
           print "Multi field query ", self.defaultMultiFields, ": %s" % query
           parsedQuery = PyLucene.MultiFieldQueryParser.parse(query, self.defaultMultiFields, self.analyzer);
       else:
           print "Single field query %s: %s" % (self.defaultField, query)
           parsedQuery = PyLucene.QueryParser.parse(query, self.defaultField, self.analyzer);

       boolQuery.add(parsedQuery, False, False)

       try:
           self.hits = self.index.search(boolQuery);
           return True
       except PyLucene.JavaError, msg:
           self.hits = None
           print "Search error: %s" % msg
           return False

   def printHits(self, maxHits):
       '''
       Print a PyLucene hits list as returned by search()
       '''

       if not self.hits: 
           print "No search results"
           return

       # Get the terminal width if we can. Assume 80 col otherwise
       width = 80
       try:
           import curses
           curses.setupterm()
           width = curses.tigetnum("cols")
       except:
           pass

       self.artists = []
       self.albums = []
       self.tracks = []
       for i in xrange(min(self.hits.length(), maxHits)):
           doc = self.hits.doc(i)
           if doc.get('ar.gid'):
               self.artists.append(i)
           elif doc.get('al.gid'):
               self.albums.append(i)
           else:
               self.tracks.append(i)

       count = 1
       if len(self.artists): count = self.output(self.hits, self.artists, self.colDefs['artist'], width, count)
       if len(self.albums): count = self.output(self.hits, self.albums, self.colDefs['album'], width, count)
       if len(self.tracks): count = self.output(self.hits, self.tracks, self.colDefs['track'], width, count)

       print "%d artists, %d albums, %d tracks, total %d of %d matches shown" % (len(self.artists), len(self.albums), len(self.tracks), 
                                                                                count - 1, self.hits.length())
       print

   def output(self, hits, docIndexes, colDefs, width, itemCount):
       '''
       Print the search hits in a nice table.
       '''

       rows = [ ["#", "sim"] ]
       rows[0].extend(colDefs)
       for i in docIndexes:
           if (hits.score(i) < self.threshold): break
           doc = hits.doc(i)

           cols = []
           cols.append("%2d" % itemCount)
           cols.append("%3d" % int(hits.score(i) * 100))
           for index in xrange(len(colDefs)):
               field = doc.get(colDefs[index])
               if not field: field = ""
               if colDefs[index] == "tr.length" and doc.get('tr.length'):
                   field = "%d:%02d" % (int(doc.get('tr.length')) / 60000, (int(doc.get('tr.length')) % 60000) / 1000)
               if colDefs[index] == "tr.al_type":
                   try:
                       field = pimpmytunes.albumTypes[int(doc.get('tr.al_type')) - 1]
                   except IndexError:
                       field = '?'
               cols.append(field)

           rows.append(cols)
           itemCount += 1

       indent.printTable(rows, width)

       return itemCount

   def mapItemToIndex(self, itemNum):
       '''
       Map one of the three part item numbers to a hit in the last hits
       '''

       itemNum -= 1
       index = -1
       if itemNum < len(self.artists): 
           return (self.artists[itemNum], 'artist')
       elif itemNum < len(self.artists) + len(self.albums):
           return (self.albums[itemNum - len(self.artists)], 'album')
       elif itemNum < len(self.artists) + len(self.albums) + len(self.tracks):
           return (self.tracks[itemNum - len(self.artists) - len(self.albums)], 'track')

       return (None, '')

   def getResult(self, itemNum, mdata):
       '''
       Return a tunepimp Metadata object from a search hit
       '''
       index, type = self.mapItemToIndex(itemNum)
       if index < 0:
           return None

       return indexsearch.convertToMdata(self.tp, type, self.hits.doc(index), mdata)

   def details(self, itemNum):
       '''
       Print the details for a search hit.
       '''
       index, type = self.mapItemToIndex(itemNum)
       if index < 0:
           print "Invalid search result index."
           return

       doc = self.hits.doc(index)
       if not doc: return

       if itemNum < len(self.artists): 
           print "Artist information:"
           print "         id: %s" % doc.get('ar.gid')
           print "       name: %s" % doc.get('ar.o_name')
           print "   sortname: %s" % doc.get('ar.o_sortname')
           print

       elif itemNum < len(self.artists) + len(self.albums):
           print "Album information:"
           print "         id: %s (artist: %s)" % (doc.get('al.gid'), doc.get('al.ar_gid'))
           print "       name: %s" % doc.get('al.o_name')
           print " num tracks: %s" % doc.get('al.tracks')
           type = doc.get('al.type')
           if type:
               print "       type: %s" % pimpmytunes.albumTypes[int(doc.get('al.type')) - 1]
           status = doc.get('al.type')
           if status:
               print "     status: %s" % pimpmytunes.albumStatus[int(doc.get('al.status')) - 1]
           print

       elif itemNum < len(self.artists) + len(self.albums) + len(self.tracks):
           dur = doc.get('tr.length')
           if dur:
               dur = int(dur)
           else:
               dur = 0

           print "Track information:"
           print "         id: %s (artist: %s / album: %s)" % (doc.get('tr.gid'), doc.get('tr.ar_gid'), doc.get('tr.al_gid'))
           print "       name: %s" % doc.get('tr.o_name')
           print "  track num: %s of %s" % (doc.get('tr.tnum'), doc.get('tr.al_tracks'))
           print "   duration: %d:%02d" % (dur / 60000, (dur % 60000) / 1000)
           print "  qduration: %s * 5s" % doc.get('tr.quantlen')
           print " album name: %s" % doc.get('tr.al_name')
           print " album type: %s" % pimpmytunes.albumTypes[int(doc.get('tr.al_type')) - 1]
           print

def usage():
    print "%s: [-i]" % sys.argv[0]
    print
    print "Options:"
    print " -i <index_dir> -- The location where the search indexes (artist_index, album_index, track_index)"
    sys.exit(-1)

if __name__ == '__main__':
    # Parse the command line args
    opts = None
    args = None
    index_dir = "."

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:")
    except:
        usage()

    for key, value in opts:
        if key == "-h": usage()
        if key == "-i": index_dir = value

    index = SearchTool(os.path.join(index_dir, "combined_index"))
    qr = queryreader.QueryReader(index)
    qr.readQueries()
