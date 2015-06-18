#Playlist Generator
##Given timeslot, generate playlist
- Given a timeslot, calc genre, if transitioning & what, safe harbor
- Using 1 criteria (genre) and 2 weights (subgenre popularity and transitioning similarity), random generate a subgenre w/ transition
- Using 2 criteria (genre/subgenre/transition and safe harbor) and 2 weights (popularity and inverse of our playcount), generate at least 20 minutes and 3 songs worth of music from that, weighing against duration beyond 5 min
- Using 3+ songs, do 1 of 2 things depending on whether or not we can steal Pandora data
  - If unofficial Pandora API works and seems to work long-term, do it
  - Otherwise, either use Last.fm or calculate similar artists & pref subgenre for artists => their similar albums => download => good songs from those albums go into playlist or some combination 
- Using list of songs, calc similarity between each (either using Chromaprint or lastfm or subgenres or combination) to form total order (again prioritizing transition and when)
- Using 57+ min of ordered music, calc liners
- Store playlist in DB with genre, subgenre, transitioning_to/from, table of starting time offset and file path
- Email webmaster critical errors when runing program