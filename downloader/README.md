#Downloader
##Three cases and functionalities

#0: Given a folder containing music, generate metadata for that music
- Determine most frequent audio file format
- Get mean artist and album from those files
- If album in db, throw this out
- else, if artist in db, use artist and get album from what
- else, search on what and find closest
- Using the closest tor group, generate metadata
- Modify metadata to match file format and songs which we have
- Proceed to postprocessor

#1: Download top x albums from a genre
- do downloader steps (get genres, iterate, have torrent groups)
- Using groups, generate metadata
- Download torrents, save metadata, and run postprocessor when done downloading

#2: Download metadata for everything because datamining
- get pages of whatgroups for genres or top10s or potentially from other sites
- Using groups, generate metadata
- postprocess data with the partial postprocessor process