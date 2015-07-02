#!/usr/bin/env python
#---------------------------------------------------------------------------
#
#   libtunepimp -- The MusicBrainz tagging library.  
#                  Let a thousand taggers bloom!
#   
#   Copyright (C) Robert Kaye 2003
#   
#   This file is part of libtunepimp.
#
#   libtunepimp is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   libtunepimp is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with libtunepimp; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#   $Id: trm.py 1323 2004-06-23 23:10:57Z robert $
#
#---------------------------------------------------------------------------

# NOTE: This example script shows only a small fraction of the capability of
#       the tunepimp library. If you would like to write more detailed example
#       scripts, please do so and send them to MusicBrainz.

import sys
from time import sleep
from tunepimp import tunepimp, metadata, track

if len(sys.argv) < 2:
    print "Usage: trm <audio file>"
    sys.exit(0)

tp = tunepimp.tunepimp('pytrm', '0.0.1', tunepimp.tpThreadRead | tunepimp.tpThreadAnalyzer);
print "Added file", tp.addFile(sys.argv[1])

done = 0
while not done:

    ret, type, fileId, status = tp.getNotification();
    if not ret:
        sleep(.1)
        continue

    if type != tunepimp.eFileChanged:
        continue
            

    tr = tp.getTrack(fileId);
    tr.lock()
    trm = tr.getTRM()

    if status == tunepimp.eUnrecognized and trm == "":
        tr.setStatus(tunepimp.ePending)
    else:
        if status == tunepimp.eTRMLookup:
            print tr.getTRM() 
            done = 1
        else:
            if status == tunepimp.eRecognized:
               print "TRM read from file: ", tr.getTRM() 
               tp.identifyAgain(fileId)
            else:
               if status == tunepimp.ePending:
                   pass
               else:
                   if status == tunepimp.eError:
                       print "Error:", tp.getError()
                       done = 1

    tr.unlock()                   
    tp.wake(tr)
    tp.releaseTrack(tr);
