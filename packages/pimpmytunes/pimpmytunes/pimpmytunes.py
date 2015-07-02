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

import sys
import os
import re
import copy
import readline
from time import sleep
from tunepimp import tunepimp, metadata, track
import artistsearch
import albumtracksearch
import tracksearch
import lookup
import combosearch
import searchtool
import filenamesearch
import indent

# The two modes that pmt can operate in
PMT_MODE_AUTOMATIC = 1
PMT_MODE_MANUAL = 2

# Status values that the manual and automatic methods return
PMT_STATUS_ERROR = 0
PMT_STATUS_RECOGNIZED = 1
PMT_STATUS_UNRECOGNIZED = 2
PMT_STATUS_SKIP = 3
PMT_STATUS_QUIT = 4
PMT_STATUS_AGAIN = 5
PMT_STATUS_REDO = 6
metadata_dict = {}

tunepimpStatus = [ "eMetadataRead", "ePending", "eUnrecognized", "eRecognized", "eTRMLookup", 
                   "eTRMCollision", "eFileLookup", "eUserSelection", "eVerified", "eSaved", 
                   "eDeleted", "eError" ]
tunepimpType = [ 'add', 'change', 'remove', 'writetags' ]
albumTypes = ('album', 'single', 'EP', 'comp', 'sndtrck', 'spword', 'intrview', 'abook', 'live', 'remix', 'other', '???')
albumStatus = ('official', 'promotion', 'bootleg', '?')

class NoSuchIndexError(ValueError):
    pass

class PimpMyTunes(object):
    '''
    This class is the core of pimp my tunes. It takes a list of files and
    feeds each file to libtunepimp for metadata reading. After reading the metadata
    it fires off the right lucene searches in order to match this track. Mixed into this
    is all the code that deals with user interaction. This should be seperated out at some point.
    '''

    def __init__(self, version, indexDir):
        # core objects we'll need
        self.tp = tunepimp.tunepimp('pmt', version, tunepimp.tpThreadRead | tunepimp.tpThreadWrite);
        self.artistSearch = artistsearch.ArtistSearch(os.path.join(indexDir, "combined_index"), self.tp)
        self.albumTrackSearch = albumtracksearch.AlbumTrackSearch(os.path.join(indexDir, "combined_index"), self.tp)
        self.trackSearch = tracksearch.TrackSearch(os.path.join(indexDir, "combined_index"), self.tp)
        self.lookup = lookup.Lookup(os.path.join(indexDir, "combined_index"), self.tp)
        self.comboSearch = combosearch.ComboSearch(os.path.join(indexDir, "combined_index"), self.tp)
        self.filenameSearch = filenamesearch.FilenameSearch(os.path.join(indexDir, "combined_index"), self.tp)
        self.searchTool = searchtool.SearchTool(os.path.join(indexDir, "combined_index"), self.tp)

        # stats
        self.statsRecognized = 0
        self.statsUnrecognized = 0
        self.statsError = 0

        # settings
        self.automaticAcceptThreshold = .65
        self.artistAcceptThreshold = .8
        self.albumAcceptThreshold = .7
        self.comboSearchAcceptThreshold = .5
        self.artistMinimumThreshold = .7
        self.trackMinimumThreshold = .6
        self.trackBareMinimumThreshold = .4
        self.debug = False
        self.terse = False
        self.maxHits = 25

        # regexp's
        self.selectionRe = re.compile("^\d+$")
        self.detailsRe = re.compile("^\.\d+$")
        self.parenRe = re.compile('\s*(\(.*\)|\[.*\])\s*$')

        # restrict searches by this artist
        self.artistIdRest = u''

    def setDebug(self, d):
        self.debug = d

    def setTerse(self, t):
        self.terse = t

    def getStats(self):
        '''
        Return the stats we gathered during our identification runs.
        '''

        return (self.statsRecognized, self.statsUnrecognized, self.statsError)

    def identify(self, files, mode):
        '''
        Given a list of files and a mode (PMT_MODE_AUTOMATIC or PMT_MODE_MANUAL)
        identify the set of files.
        '''
        self.metadata_dict = {}
        nextSet = []
        while True:
            for file in files:
                while True:
                    ret = self.identifyFile(file, mode)
                    if ret == PMT_STATUS_AGAIN: continue
                    break

                if ret == PMT_STATUS_SKIP:
                    nextSet.append(file)
                if ret == PMT_STATUS_QUIT:
                    return

            if len(nextSet): 
                files = nextSet
            else:
                break
        return self.metadata_dict

    def identifyFile(self, file, mode):
        '''
        Identify one file in the given mode. Feed it to libtp to read metadata
        and then fire off the right lookup process. Depending on the lookup
        results and the mode, save the results, skip it or get user feedback
        on what to do.
        '''

        self.artistIdRest = u''

        fileId = self.tp.addFile(file)
        status = self.waitForChange(fileId)
        if status == tunepimp.eError:
            self.error(file, fileId)
            self.removeFile(fileId)
            return PMT_STATUS_ERROR

        if status != tunepimp.eRecognized and status != tunepimp.eUnrecognized:
            print "Unexpected status: %d" % status
            self.removeFile(fileId)
            return PMT_STATUS_ERROR

        tr = self.tp.getTrack(fileId)
        mdata = tr.getLocalMetadata()
        mdataOrig = tr.getLocalMetadata()
        self.tp.releaseTrack(tr)

        while True:
            if not self.terse:
                header = "Input file: %s:" % file
                print "%s\n%s" % (header, len(header)*'-')
                self.printData(mdata)

            if status == tunepimp.eRecognized:
                self.recognized(file, mdata)
                return PMT_STATUS_RECOGNIZED

            if status == tunepimp.eUnrecognized:

                # Lookup track -- returns a list of (sim, mdata) tuples
                type, matches = self.findMatches(mdata, file, mode)
                if mode == PMT_MODE_AUTOMATIC:
                    if len(matches) == 0 or type != 'track': 
                        self.unrecognized(file)
                        return PMT_STATUS_UNRECOGNIZED

                    if matches[0][0]< self.automaticAcceptThreshold: 
                        self.unrecognized(file)
                        return PMT_STATUS_UNRECOGNIZED

                    mdata = matches[0][1]

                    # now save the file and return
                    if not self.terse:
                        header = "Matched track: %s:" % file
                        print "%s\n%s" % (header, len(header)*'-')
                   
                    self.removeFile(fileId)
                    if 0: #not self.saveFile(fileId, mdata):
                        self.error(file, fileId)
                        self.removeFile(fileId)
                        return PMT_STATUS_ERROR

                    self.recognized(file, mdata)
                    return PMT_STATUS_RECOGNIZED

                # manual
                if len(matches) == 0:
                    print "No possible matches found."
                else:
                    if self.debug: print "=== SEARCH RESULTS ==="
                    self.printMatches(type, matches, mdata)
                    print

                ret = self.getUserInput(file, fileId, mdata, mdataOrig, matches, type)
                if ret == PMT_STATUS_REDO: continue
                return ret

    def readLine(self, prompt, init = '', nohist=False):
        '''
        Read input from the command line, with optional; history support. 
        Prompt defines what to print before the input field, and init gives an 
        initial value for the text input.
        '''

        readline.set_startup_hook(lambda: readline.insert_text(init))
        try:
            line = raw_input(prompt)
        except (KeyboardInterrupt, EOFError):
            print
            return None

        if nohist: readline.remove_history_item(readline.get_current_history_length() - 1)

        if line == '': return ''
        if not line: return None
        return line.strip()


    def getUserInput(self, file, fileId, mdata, mdataOrig, matches, matchType):
        '''
        Read a command from the command line and carry out the action of pass
        control to a supporting class/method.
        '''
        
        line = ''
        resultType = ''

        lastWasMatches = True
        while True:
            line = self.readLine(">")
            if line == None: return PMT_STATUS_QUIT
            if line == '': continue
            cmd = line[0]

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

            if cmd == 'd':
                self.deleteFile(file, fileId)
                continue

            if cmd == 'e':
                print "Enter new metadata information:"
                mdata.clear()
                mdata.artist = unicode(self.readLine("artist: ", mdataOrig.artist, True) or " ", 'utf-8')
                mdata.album = unicode(self.readLine("album: ", mdataOrig.album, True) or " ", 'utf-8')
                mdata.track = unicode(self.readLine("track: ", mdataOrig.track, True) or " ", 'utf-8')
                mdata.duration = mdataOrig.duration
                return PMT_STATUS_REDO

            if cmd == 'm':
                try:
                    self.maxHits = int(line[2:])
                except:
                    print "Invalid number of max hits."
                else:
                    print "Only displaying %d max hits" % self.maxHits
                continue

            if cmd == 'c':
                self.artistIdRest = u''
                print "artist restriction cleared"
                continue

            if cmd == 'a':
                print "enter album not implemented"
                continue

            if cmd == 'a':
                print "lookup album not implemented"
                continue

            if cmd == 'q':
                self.removeFile(fileId)
                return PMT_STATUS_QUIT

            if cmd == 'b':
                self.debug = not self.debug
                print "debug is", self.debug
                continue

            if cmd == '!':
                self.removeFile(fileId)
                return PMT_STATUS_AGAIN

            if cmd == 'r':
                self.removeFile(fileId)
                return PMT_STATUS_UNRECOGNIZED

            if cmd == 's':
                self.removeFile(fileId)
                return PMT_STATUS_SKIP

            if cmd == '/':
                line = line[1:]
                if self.searchTool.search(line, self.artistIdRest):
                    self.searchTool.printHits(self.maxHits)

                lastWasMatches = False
                continue

            if line == 'pm':
                self.printMatches(matchType, matches, mdata)
                print
                lastWasMatches = True
                continue

            if line == 'ps': 
                self.searchTool.printHits(25)
                lastWasMatches = False
                continue

            if self.detailsRe.search(line):
                index = int(line[1:])
                if lastWasMatches:
                    try:
                        self.printData(matches[index][1])
                    except IndexError:
                        print "Invalid result number"
                        continue
                else:
                    self.searchTool.details(index)
                continue

            if self.selectionRe.search(line):
                match = None
                if lastWasMatches:
                    try:
                        index = int(line) - 1
                    except:
                        index = -1

                    if index < 0 or index >= len(matches):
                        print "Invalid match number"
                        continue

                    # Blank out the lower case artist name to have the real name looked up
                    match = matches[index][1]
                    type = matchType
                else:
                    index, resultType = self.searchTool.mapItemToIndex(int(line))
                    if index < 0:
                        print "Invalid result number"
                        continue
                    match = self.searchTool.getResult(int(line), mdata)
                    type = resultType

                if type == 'track':
                    self.removeFile(fileId)
                    self.recognized(file, match)
                    ret = 1 # self.saveFile(fileId, match)
                    if not ret:
                        err = self.tp.getError()
                        print "Error: %s" % error
                        continue
                    return PMT_STATUS_RECOGNIZED

                elif type == 'album':
                    self.searchTool.match("tr.al_gid:%s" % match.albumId, 25, u'')
                    lastWasMatches = False
                    continue

                elif type == 'artist':
                    self.artistIdRest = match.artistId 
                    print "searches now resticted to artist: '%s'" % match.artist
                    print "use c to clear restriction"
                    continue

            print "invalid command"

    def addDashes(self, uuid):
        '''
        Convert a dashless UUID to a standard UUID with dashes.
        '''
        return "%s-%s-%s-%s-%s" % (uuid[0:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:32])

    def saveFile(self, fileId, mdata):
        '''
        Tell libtunepimp to save the file and wait for tunepimpt to carry out the save.
        Returns a boolean sucess value.
        '''

        # Add the dashes back in that lucene removed
        mdata.artistId = self.addDashes(mdata.artistId)
        mdata.albumId = self.addDashes(mdata.albumId)
        mdata.trackId = self.addDashes(mdata.trackId)

        tr = self.tp.getTrack(fileId)
        tr.setServerMetadata(mdata)
        tr.setStatus(tunepimp.eVerified)
        self.tp.wake(tr)
        self.tp.releaseTrack(tr)

        # Get the note that we're set to verified.
        status = self.waitForChange(fileId)
        if status != tunepimp.eVerified:
            return False

        # Write the file
        self.tp.writeTags([fileId])

        # Get the note we're saved
        status = self.waitForChange(fileId)
        if status != tunepimp.eSaved:
            return False

        # Get the write tags complete message
        self.waitForChange(fileId, tunepimp.eWriteTagsComplete)

        self.removeFile(fileId)
        return True

    def removeFile(self, fileId):
        '''
        Remove the file from libtunepimp and wait for libtp to acknowledge it.
        '''
        # Remove the file from tunepimp
        self.tp.remove(fileId)
        self.waitForChange(fileId, tunepimp.eFileRemoved)

    def deleteFile(self, file, fileId):
        '''
        Delete a file from disk after getting the user to confirm the delete.
        '''
        print "%s:\nAre you sure you want to permanently delete this file? (N/y)" % file,
        verify = self.readLine(": ")
        if verify and verify[:1].lower() == 'y':
            self.removeFile(fileId)
            try:
                os.unlink(file)
            except OSError, msg:
                print "Cannot remove file: %s" %msg

    def printMatches(self, type, matches, mdata):
        '''
        Determine what type of results we have and call the right sub function to print the results.
        '''
        try:
            import curses
            curses.setupterm()
            width = curses.tigetnum("cols")
        except:
            width = 80

        if type == 'artist':
            self.printArtistMatches(matches, width)
        elif type == 'track':
            self.printTrackMatches(mdata, matches, width)
        else:
            print "unknown match type: '%s'" % type
            return

    def printTrackMatches(self, mdata, matches, width):
        '''
        Print track matches in a nice table format.
        '''
        rows = [ [ '#', 'sim', 'artist', 'album', 'type', 'track', 'tnum', 'dur' ] ]
        index = 1
        for sim, track in matches:
           dur = mdata.duration
           if dur:
               dur = "%2d:%02d" % (dur / 60000, (dur % 60000) / 1000)
           else:
               dur = ' '

           col = []
           col.append(unicode(index))
           col.append("%3d" % int(sim * 100))
           col.append(track.artist)
           col.append(track.album)
           col.append(albumTypes[track.albumType - 1])
           col.append(track.track)
           col.append("%2d/%2d" % (track.trackNum, track.totalInSet))
           col.append(dur)
           rows.append(col)
           index += 1

        indent.printTable(rows, width)

    def printArtistMatches(self, matches, width):
        '''
        Print artist matches in a nice table format.
        '''
        rows = [ [ '#', 'artist', 'sortname', 'gid' ] ]
        index = 1
        for sim, artist in matches:
           col = []
           col.append(unicode(index))
           col.append(artist.artist)
           col.append(artist.sortName)
           col.append(artist.artistId)
           rows.append(col)
           index += 1

        indent.printTable(rows, width)

    def printData(self, mdata):
        '''
        Print one metadata structure.
        '''
        print " artist: %-50s %s" % (mdata.artist, mdata.artistId)
        print "  album: %-50s %s" % (mdata.album, mdata.albumId)
        print "  track: %-50s %s" % (mdata.track, mdata.trackId)
        if mdata.trackNum > 0 or mdata.totalInSet > 0:
            print "track #: %d of %d" % (mdata.trackNum, mdata.totalInSet)
        if mdata.albumType != tunepimp.eAlbumType_Error:
            print "   type: %s / %s" % (albumTypes[mdata.albumType - 1], albumStatus[mdata.albumStatus - 1])
        if mdata.duration > 0:
            print "    dur: %d:%02d" % (mdata.duration / 60000, (mdata.duration % 60000) / 1000)
        print

    def unrecognized(self, fileName):
        '''
        This function is called when a track is not matched. Print the right user feedback and
        update the stats.
        '''
        print "%s:" % fileName
        if not self.terse:
            print "  unrecognized"
            print
        self.statsUnrecognized += 1

    def recognized(self, fileName, mdata):
        '''
        This function is called when a track is matched. 
        '''
        if self.terse:
            print "%s:%s" % (fileName, mdata.trackId)
        else:
            print "%s:" % fileName
            self.printData(mdata)
            print
        self.statsRecognized += 1
        self.metadata_dict[fileName] = mdata

    def error(self, file, fileId):
        '''
        Called when libtp encounteres an error reading/writing a file.
        '''

        if not self.terse:
            tr = self.tp.getTrack(fileId)
            err = tr.getTrackError()
            self.tp.releaseTrack(tr)
            print "%s:" % file
            print "  error: %s" % err
            print
        self.statsError += 1

    def findMatches(self, mdata, fileName, mode):
        '''
        This function is the brainz of pimpmytunes. It takes the metadata from one file
        and calls the appropriate search methods to try and identify this file. Read the
        inline comments for details.
        '''

        # TODO: Add no paren checkin

        savedArtist = mdata.artist
        savedArtistId = mdata.artistId
        savedSortName = mdata.sortName
        savedTrack = mdata.track

        if self.debug: print "Input: '%s', '%s', '%s'" % (mdata.artist, mdata.album, mdata.track)
        if not mdata.artistId:

            # Carry out an artist search. Once we have an artist, we can narrow down the search
            artists = self.artistSearch.match(mdata, fileName, self.debug, self.maxHits)
            if self.debug and artists:
                print "=== ARTIST SEARCH ==="
                self.printMatches('artist', artists, mdata)
            if len(artists) >= 1 and artists[0][0] >= self.artistMinimumThreshold:
                mdata.artist = artists[0][1].artist 
                mdata.sortName = artists[0][1].sortName 
                mdata.artistId = artists[0][1].artistId 
                if self.debug: 
                    print "Matched artist: '%s'" % mdata.artist
                    print "=== ACCEPT ARTIST SEARCH ===\n"
            else:
                return ('artist', artists)

            # Then, search on album and track
            albumTracks = None
            if mdata.album:
                albumTracks = self.albumTrackSearch.match(mdata, fileName, self.debug, self.maxHits)
                if self.debug and albumTracks:
                    print "=== ALBUM/TRACK SEARCH ==="
                    self.printMatches('track', albumTracks, mdata)
                if len(albumTracks) and albumTracks[0][0] >= self.trackMinimumThreshold:
                    if self.debug:
                        print "=== ACCEPT ALBUM/TRACK SEARCH ===\n"
                    return ('track', albumTracks)

            # If that doesn't give a good match, try without the album
            tracks = self.trackSearch.match(mdata, fileName, self.debug, self.maxHits)
            if len(tracks) >= 1:
                if self.debug and tracks:
                    print "=== TRACK SEARCH ==="
                    self.printMatches('track', tracks, mdata)

                # did the track search an acceptable search result and there were no albumtrack matches?
                # did the track search give better results than the album search? if either, return track matches
                if ((tracks[0][0] >= self.trackMinimumThreshold and not albumTracks) or
                    (tracks[0][0] >= self.trackMinimumThreshold and albumTracks and tracks[0][0] > albumTracks[0][0])):
                    if self.debug:
                        print "=== ACCEPT TRACK SEARCH ===\n"
                    return ('track', tracks)

            # Look at the albumTrack again. Does it meet the most basic requirements if we're in manual mode?
            if albumTracks and albumTracks[0][0] >= self.trackBareMinimumThreshold and mode == PMT_MODE_AUTOMATIC:
                if self.debug:
                    print "=== ACCEPT ALBUM/TRACK SEARCH ===\n"
                return ('track', albumTracks)

        # Restore values we may have tinkered with
        mdata.artist = savedArtist
        mdata.sortName = savedSortName
        mdata.artistId = savedArtistId
        mdata.track = savedTrack

        # last ditch effort, do a combo search on all fields
        tracks = self.comboSearch.match(mdata, fileName, self.debug, self.maxHits)
        if len(tracks) >= 1:
            if self.debug and tracks:
                print "=== COMBO SEARCH ==="
                self.printMatches('track', tracks, mdata)
            if tracks[0][0] >= self.comboSearchAcceptThreshold:
                if self.debug:
                    print "=== ACCEPT COMBO SEARCH ===\n"
                return ('track', tracks)

        tracks = self.filenameSearch.match(mdata, fileName, self.debug, self.maxHits)
        if self.debug and tracks:
            print "=== FILENAME SEARCH ==="
            self.printMatches('track', tracks, mdata)

        return ('track', tracks)

    def waitForChange(self, fileId, wantStatus = tunepimp.eFileChanged):
        '''
        Poll in a loop and wait for the status of a file in libtp to change.
        '''
        while True:
            ret, type, id, status = self.tp.getNotification();
            if fileId != id:
                continue
            if not ret:
                sleep(.01)
                continue

            if type == wantStatus:
                return status
