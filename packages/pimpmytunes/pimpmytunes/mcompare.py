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

import Levenshtein
import re
from tunepimp import tunepimp

artistWeight    = 10
albumWeight     = 9 
trackWeight     = 10
trackNumWeight  = 2
durationWeight  = 3
albumTypeWeight = 3

def sim(str1, str2):
    '''
    Given two strings, return the parametric similarity between two strings. Two dissimilar
    strings will return 0.0 and two exact same strings will be 1.0.
    '''
    if not str1 or not str2: return 0.0
    return 1.0 - (float(Levenshtein.distance(str1, str2)) / float(max(len(str1), len(str2))))

def durationSim(durA, durB):
    '''
    Given to millisecond durations, calculate the parametric similarity between the two. If the
    two tracks are off by more than 3 seconds, its 0.0 similarity.
    '''
    diff = abs(durA - durB)
    if diff > 30000:
       return 0.0

    return 1.0 - (float(diff) / 30000.0)

class MetadataCompare(object):

    def __init__(self):
        self.parenRe = re.compile('\s*(\(.*\)|\[.*\])\s*$')

    def noParenSim(self, a, b):
        anp = a.lower().replace(' ', '')
        bnp = b.lower().replace(' ', '')
        s = sim(anp, bnp)
        hadParen = False
        if self.parenRe.search(anp):
            anp = self.parenRe.sub('', anp)
            hadParen = True
        if self.parenRe.search(bnp):
            bnp = self.parenRe.sub('', bnp)
            hadParen = True

        if hadParen:
            s2 = sim(anp, bnp)
            if s2 > s: s = s2

        return s

    def compare(self, a, b):
        '''
        Given two tunepimp metadata objects, return the parametric similarity value of the two.
        '''

        #print "'%-40s' - '%-40s' %.2f" % (a.artist, b.artist, sim(a.artist.lower().replace(' ', ''), b.artist.lower().replace(' ', '')))
        #print "'%-40s' - '%-40s' %.2f" % (a.album, b.album, sim(a.album.lower().replace(' ', ''), b.album.lower().replace(' ', '')))
        #print "'%-40s' - '%-40s' %.2f" % (a.track, b.track, sim(a.track.lower().replace(' ', ''), b.track.lower().replace(' ', '')))
        #print "'%-40d' - '%-40d' %.2f" % (a.trackNum, b.trackNum, float(a.trackNum == b.trackNum))
        #print "'%-40d' - '%-40d' %.2f" % (a.albumType, b.albumType, durationSim(a.duration, b.duration))
        #print "'%-40d' - '%-40d' %.2f" % (a.duration, b.duration, float(a.albumType == b.albumType))

        sims = []
        if a.artist and b.artist:
            sims.append((sim(a.artist.lower().replace(' ', ''), b.artist.lower().replace(' ', '')), artistWeight))

        if a.album and b.album:
            sims.append((self.noParenSim(a.album, b.album), albumWeight))

        if a.track and b.track:
            sims.append((self.noParenSim(a.track, b.track), trackWeight))

        if a.trackNum > 0 and b.trackNum > 0:
            sims.append((float(a.trackNum == b.trackNum), trackNumWeight))

        if a.duration and b.duration:
            sims.append((durationSim(a.duration, b.duration), durationWeight))

        if a.albumType != tunepimp.eAlbumType_Error and b.albumType != tunepimp.eAlbumType_Error:
            sims.append((float(a.albumType == b.albumType), albumTypeWeight))

        if not sims: return 0.0

        total = 0.0
        for s, weight in sims:
           total += weight

        ret = 0.0
        for s, weight in sims:
           ret += weight * s / total

        #print "Sim: %d" % int(ret * 100)
        #print
           
        return ret 
