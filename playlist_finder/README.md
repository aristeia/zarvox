#Playlist Finder
##Given a timeslot, play a playlist
- Given a timeslot, calc genre, if transitioning & what, safe harbor
- Using 2 criteria and 2 weight (transitioning and plays-per-playlist (double)), order playlists by what should be played
- search by order for one with time that'll work with +/- 30 seconds
- if none, increase time +/- 45 etc.
- return playlist to music player
- Email webmaster log with output of how the search is doing (at first) & any errors at runtime
- In case of critical error with finding playlist, default to playing student shows from current time offset

Popularity probability