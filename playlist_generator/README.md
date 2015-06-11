#Playlist Generator
##Given timeslot, generate playlist
- Given a timeslot, calc genre, if transitioning & what, safe harbor
- Using 1 criteria and 2 weights, random generate a subgenre/twist
- Using 2 criteria, generate 20 minutes and 3 songs worth of music from that, weighing against duration beyond 5 and referencing
- Using 3+ songs, calculate similar artists => their similar albums => download => good songs from those albums go into playlist
- Using list of songs, calc similarity between each to form total order (again prioritizing transition and when)
- Using 57+ min of ordered music, calc liners
- Store playlist in DB with genre, subgenre, transitioning_to/from, table of starting time offset and file path
- Email webmaster critical errors when runing program