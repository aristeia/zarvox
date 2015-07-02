/*----------------------------------------------------------------------------

   libtunepimp -- The MusicBrainz tagging library.
                  Let a thousand taggers bloom!

   Copyright (C) Robert Kaye 2003

   This file is part of libtunepimp.

   libtunepimp is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

   libtunepimp is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with libtunepimp; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

   $Id: tunepimp.xs 1367 2005-02-21 01:10:28Z robert $

----------------------------------------------------------------------------*/

#include "EXTERN.h"
#include "perl.h"
#include "XSUB.h"

#include "ppport.h"

#include <tunepimp/tp_c.h>

#include "const-c.inc"

// Various "get string" functions require a buffer to be supplied, with no
// obvious way to get the size of the buffer first.  So let's guess high.
#define BIG_STRING 1000

// Shorter buffers, for album type/status
#define SMALL_STRING 100
// TRM length
#define TRM_LENGTH 36

SV *perl_notify_callback = NULL;
SV *perl_status_callback = NULL;

void notify_callback(tunepimp_t o, void *data, TPCallbackEnum notifyType, int fileId, TPFileStatus status)
{
	//if (notifyType == tpFileAdded) printf("TP notify callback: file #%d added\n", fileId);
	//else if (notifyType == tpFileChanged) printf("TP notify callback: file #%d changed\n", fileId);
	//else if (notifyType == tpFileRemoved) printf("TP notify callback: file #%d removed\n", fileId);
	//else printf("TP notify callback: file #%d unknown type #%d\n", fileId, notifyType);

	if (!perl_notify_callback) return;

	dSP;
	ENTER;
	SAVETMPS;

	PUSHMARK(SP);
	XPUSHs(sv_2mortal(newSViv(notifyType)));
	XPUSHs(sv_2mortal(newSViv(fileId)));
	XPUSHs(sv_2mortal(newSViv(status)));
	PUTBACK;

	call_sv(SvRV(perl_notify_callback), G_VOID|G_DISCARD|G_EVAL);

	FREETMPS;
	LEAVE;
}

void status_callback(tunepimp_t o, void *data, const char *msg)
{
	//printf("TP status callback: %s\n", msg);

	if (!perl_status_callback) return;

	//printf("time to call something in %s\n", CvFILE(SvRV(perl_status_callback)));

	dSP;
	ENTER;
	SAVETMPS;

	PUSHMARK(SP);
	XPUSHs(sv_2mortal(newSVpv(msg, 0)));
	PUTBACK;

	call_sv(SvRV(perl_status_callback), G_VOID|G_DISCARD|G_EVAL);

	FREETMPS;
	LEAVE;
}

SV * _flatten_artist_result(artistresult_t *r)
{
	HV *hv;
	hv = newHV();

	hv_store(hv, "id",		2, newSVpv(r->id, 0),		0);
	hv_store(hv, "name",		4, newSVpv(r->name, 0),		0);
	hv_store(hv, "sortName",	8, newSVpv(r->sortName, 0),	0);
	hv_store(hv, "relevance",	9, newSViv(r->relevance),	0);

	return newRV_noinc((SV *)hv);
}

SV * _flatten_album_result(albumresult_t *r)
{
	HV *hv;
	hv = newHV();

	hv_store(hv, "id",		2, newSVpv(r->id, 0),		0);
	hv_store(hv, "name",		4, newSVpv(r->name, 0),		0);
	hv_store(hv, "relevance",	9, newSViv(r->relevance),	0);
	hv_store(hv, "numTracks",	9, newSViv(r->numTracks),	0);
	hv_store(hv, "numCDIndexIds",	13,newSViv(r->numCDIndexIds),	0);
	hv_store(hv, "isVA",		4, newSViv(r->isVA),		0);
	hv_store(hv, "isNA",		4, newSViv(r->isNA),		0);
	hv_store(hv, "status",		6, newSViv(r->status),		0);
	hv_store(hv, "type",		4, newSViv(r->type),		0);
	hv_store(hv, "artist",		6, _flatten_artist_result(&r->artist), 0);

	return newRV_noinc((SV *)hv);
}

SV * _flatten_track_result(albumtrackresult_t *r)
{
	HV *hv;
	hv = newHV();

	hv_store(hv, "relevance",	9, newSViv(r->relevance),	0);
	hv_store(hv, "name",		4, newSVpv(r->name, 0),		0);
	hv_store(hv, "id",		2, newSVpv(r->id, 0),		0);
	hv_store(hv, "numTRMIds",	9, newSViv(r->numTRMIds),	0);
	hv_store(hv, "trackNum",	8, newSViv(r->trackNum),	0);
	hv_store(hv, "duration",	8, newSVuv(r->duration),	0);
	hv_store(hv, "artist",		6, _flatten_artist_result(&r->artist), 0);
	hv_store(hv, "album",		5, _flatten_album_result(&r->album), 0);

	return newRV_noinc((SV *)hv);
}

MODULE = MusicBrainz::Tunepimp			PACKAGE = MusicBrainz::Tunepimp

# Yeah, there's bound to be a better way of doing this, but I don't know it, and
# this method works.

int
TP_ARTIST_NAME_LEN()
	CODE:
		RETVAL = TP_ARTIST_NAME_LEN;
	OUTPUT:
		RETVAL

int
TP_ALBUM_NAME_LEN()
	CODE:
		RETVAL = TP_ALBUM_NAME_LEN;
	OUTPUT:
		RETVAL

int
TP_TRACK_NAME_LEN()
	CODE:
		RETVAL = TP_TRACK_NAME_LEN;
	OUTPUT:
		RETVAL

int
TP_ID_LEN()
	CODE:
		RETVAL = TP_ID_LEN;
	OUTPUT:
		RETVAL

int
TP_FORMAT_LEN()
	CODE:
		RETVAL = TP_FORMAT_LEN;
	OUTPUT:
		RETVAL

int
TP_COUNTRY_LEN()
	CODE:
		RETVAL = TP_COUNTRY_LEN;
	OUTPUT:
		RETVAL

MODULE = MusicBrainz::Tunepimp::metadata	PACKAGE = MusicBrainz::Tunepimp::metadata

INCLUDE: const-xs.inc

void
clear(arg0)
	metadata_t *	arg0
	CODE:
		md_Clear(arg0);

void
_getAlbumStatusNameFromNumber(status)
	TPAlbumStatus	status
	PREINIT:
		char	albumStatus[SMALL_STRING];
	CODE:
		md_ConvertFromAlbumStatus(status, albumStatus, SMALL_STRING);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(albumStatus, 0)));
		XSRETURN(1);

void
_getAlbumTypeNameFromNumber(type)
	TPAlbumType	type
	PREINIT:
		char	albumType[SMALL_STRING];
	CODE:
		md_ConvertFromAlbumType(type, albumType, SMALL_STRING);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(albumType, 0)));
		XSRETURN(1);

TPAlbumStatus
_getAlbumStatusNumberFromName(albumStatus)
	const char *	albumStatus
	CODE:
		RETVAL = md_ConvertToAlbumStatus(albumStatus);
	OUTPUT:
		RETVAL

TPAlbumType
_getAlbumTypeNumberFromName(albumType)
	const char *	albumType
	CODE:
		RETVAL = md_ConvertToAlbumType(albumType);
	OUTPUT:
		RETVAL

void
DESTROY(arg0)
	metadata_t *	arg0
	CODE:
		md_Delete(arg0);

metadata_t *
_new()
	CODE:
		RETVAL = md_New();
	OUTPUT:
		RETVAL

# The following methods all read the members of the metadata_t struct

char *
getArtist(md)
	metadata_t * md
	CODE:
		if (!md->artist) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->artist, 0)));
		XSRETURN(1);

char *
getSortName(md)
	metadata_t * md
	CODE:
		if (!md->sortName) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->sortName, 0)));
		XSRETURN(1);

char *
getAlbum(md)
	metadata_t * md
	CODE:
		if (!md->album) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->album, 0)));
		XSRETURN(1);

char *
getTrack(md)
	metadata_t * md
	CODE:
		if (!md->track) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->track, 0)));
		XSRETURN(1);


int
getTrackNum(md)
	metadata_t * md
	CODE:
		RETVAL = md->trackNum;
	OUTPUT:
		RETVAL

int
getVariousArtist(md)
	metadata_t * md
	CODE:
		RETVAL = md->variousArtist;
	OUTPUT:
		RETVAL

int
getNonAlbum(md)
	metadata_t * md
	CODE:
		RETVAL = md->nonAlbum;
	OUTPUT:
		RETVAL

char *
getArtistId(md)
	metadata_t * md
	CODE:
		if (!md->artistId) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->artistId, 0)));
		XSRETURN(1);

char *
getAlbumId(md)
	metadata_t * md
	CODE:
		if (!md->albumId) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->albumId, 0)));
		XSRETURN(1);

char *
getTrackId(md)
	metadata_t * md
	CODE:
		if (!md->trackId) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->trackId, 0)));
		XSRETURN(1);

char *
getFileTrm(md)
	metadata_t * md
	CODE:
		if (!md->fileTrm) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->fileTrm, 0)));
		XSRETURN(1);

char *
getAlbumArtistId(md)
	metadata_t * md
	CODE:
		if (!md->albumArtistId) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->albumArtistId, 0)));
		XSRETURN(1);

unsigned long
getDuration(md)
	metadata_t * md
	CODE:
		RETVAL = md->duration;
	OUTPUT:
		RETVAL

int
getAlbumType(md)
	metadata_t * md
	CODE:
		RETVAL = md->albumType;
	OUTPUT:
		RETVAL

char *
getFileFormat(md)
	metadata_t * md
	CODE:
		if (!md->fileFormat[0]) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->fileFormat, 0)));
		XSRETURN(1);

int
getReleaseYear(md)
	metadata_t * md
	CODE:
		RETVAL = md->releaseYear;
	OUTPUT:
		RETVAL

int
getReleaseMonth(md)
	metadata_t * md
	CODE:
		RETVAL = md->releaseMonth;
	OUTPUT:
		RETVAL

int
getReleaseDay(md)
	metadata_t * md
	CODE:
		RETVAL = md->releaseDay;
	OUTPUT:
		RETVAL

char *
getReleaseCountry(md)
	metadata_t * md
	CODE:
		if (!md->releaseCountry[0]) XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(md->releaseCountry, 0)));
		XSRETURN(1);

int
getNumTrmIds(md)
	metadata_t * md
	CODE:
		RETVAL = md->numTRMIds;
	OUTPUT:
		RETVAL

void
setArtist(md, artist)
	metadata_t * md
	const char *artist
	CODE:
		if (strlen(artist)+1 > TP_ARTIST_NAME_LEN)
			croak("artist name too long");
		strncpy(md->artist, artist, TP_ARTIST_NAME_LEN);
		md->artist[TP_ARTIST_NAME_LEN] = '\0';
		XSRETURN_UNDEF;

void
setSortName(md, sortName)
	metadata_t * md
	const char *sortName
	CODE:
		if (strlen(sortName)+1 > TP_ARTIST_NAME_LEN)
			croak("artist sortname too long");
		strncpy(md->sortName, sortName, TP_ARTIST_NAME_LEN);
		md->sortName[TP_ARTIST_NAME_LEN] = '\0';
		XSRETURN_UNDEF;

void
setAlbum(md, album)
	metadata_t * md
	const char *album
	CODE:
		if (strlen(album)+1 > TP_ALBUM_NAME_LEN)
			croak("album name too long");
		strncpy(md->album, album, TP_ALBUM_NAME_LEN);
		md->album[TP_ALBUM_NAME_LEN] = '\0';
		XSRETURN_UNDEF;

void
setTrack(md, track)
	metadata_t * md
	const char *track
	CODE:
		if (strlen(track)+1 > TP_TRACK_NAME_LEN)
			croak("track name too long");
		strncpy(md->track, track, TP_TRACK_NAME_LEN);
		md->track[TP_TRACK_NAME_LEN] = '\0';
		XSRETURN_UNDEF;

void
setTrackNum(md, trackNum)
	metadata_t * md
	int trackNum
	CODE:
		md->trackNum = trackNum;

void
setVariousArtist(md, variousArtist)
	metadata_t * md
	int variousArtist
	CODE:
		md->variousArtist = (variousArtist ? 1 : 0);

void
setNonAlbum(md, nonAlbum)
	metadata_t * md
	int nonAlbum
	CODE:
		md->nonAlbum = (nonAlbum ? 1 : 0);

void
setArtistId(md, artistId)
	metadata_t * md
	const char *artistId
	CODE:
		if (strlen(artistId)+1 > TP_ID_LEN)
			croak("artistId too long");
		strncpy(md->artistId, artistId, TP_ID_LEN);
		md->artistId[TP_ID_LEN] = '\0';
		XSRETURN_UNDEF;

void
setAlbumId(md, albumId)
	metadata_t * md
	const char *albumId
	CODE:
		if (strlen(albumId)+1 > TP_ID_LEN)
			croak("albumId too long");
		strncpy(md->albumId, albumId, TP_ID_LEN);
		md->albumId[TP_ID_LEN] = '\0';
		XSRETURN_UNDEF;

void
setTrackId(md, trackId)
	metadata_t * md
	const char *trackId
	CODE:
		if (strlen(trackId)+1 > TP_ID_LEN)
			croak("trackId too long");
		strncpy(md->trackId, trackId, TP_ID_LEN);
		md->trackId[TP_ID_LEN] = '\0';
		XSRETURN_UNDEF;

void
setFileTrm(md, fileTrm)
	metadata_t * md
	const char *fileTrm
	CODE:
		if (strlen(fileTrm)+1 > TP_ID_LEN)
			croak("fileTrm too long");
		strncpy(md->fileTrm, fileTrm, TP_ID_LEN);
		md->fileTrm[TP_ID_LEN] = '\0';
		XSRETURN_UNDEF;

void
setAlbumArtistId(md, albumArtistId)
	metadata_t * md
	const char *albumArtistId
	CODE:
		if (strlen(albumArtistId)+1 > TP_ID_LEN)
			croak("albumArtistId too long");
		strncpy(md->albumArtistId, albumArtistId, TP_ID_LEN);
		md->albumArtistId[TP_ID_LEN] = '\0';
		XSRETURN_UNDEF;

void
setDuration(md, duration)
	metadata_t * md
	unsigned long duration
	CODE:
		md->duration = duration;

void
setAlbumType(md, albumType)
	metadata_t * md
	TPAlbumType albumType
	CODE:
		md->albumType = albumType;

# Note, no setters for these:
# char * setFileFormat
# int setReleaseYear
# int setReleaseMonth
# int setReleaseDay
# char * setReleaseCountry
# int setNumTRMIds

int
compare(mdA, mdB)
	metadata_t *mdA
	metadata_t *mdB
	CODE:
		RETVAL = md_Compare(mdA, mdB);
	OUTPUT:
		RETVAL

MODULE = MusicBrainz::Tunepimp::tunepimp	PACKAGE = MusicBrainz::Tunepimp::tunepimp

INCLUDE: const-xs.inc

int
addFile(o, fileName, readMetadataNow)
	tunepimp_t	o
	const char *	fileName
	int		readMetadataNow
	CODE:
		RETVAL = tp_AddFile(o, fileName, readMetadataNow);
	OUTPUT:
		RETVAL

int
addDir(o, dirPath)
	tunepimp_t	o
	const char *	dirPath
	CODE:
		RETVAL = tp_AddDir(o, dirPath);
	OUTPUT:
		RETVAL

void
DESTROY(o)
	tunepimp_t	o
	CODE:
		tp_Delete(o);

void
getError(o)
	tunepimp_t	o
	PREINIT:
		char	error[BIG_STRING];
	CODE:
		tp_GetError(o, error, BIG_STRING);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(error, 0)));
		XSRETURN(1);

void
getFileIds(o)
	tunepimp_t	o
	PREINIT:
		int *	ids;
		int NumFileIds;
		int i;
	CODE:
		NumFileIds = tp_GetNumFileIds(o);
		if (!NumFileIds) XSRETURN_EMPTY;

		New(0, ids, NumFileIds, int);
		SAVEFREEPV(ids);
		tp_GetFileIds(o, ids, NumFileIds);

		sp -= items;
		EXTEND(SP, NumFileIds);

		for (i=0; i<NumFileIds; ++i)
		{
			PUSHs(sv_2mortal(newSViv(*ids++)));
		}

		XSRETURN(NumFileIds);

int
getNumFileIds(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetNumFileIds(o);
	OUTPUT:
		RETVAL

int
getNumFiles(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetNumFiles(o);
	OUTPUT:
		RETVAL

int
getNumSupportedExtensions(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetNumSupportedExtensions(o);
	OUTPUT:
		RETVAL

int
getNumUnsubmitted(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetNumUnsubmitted(o);
	OUTPUT:
		RETVAL

int
getNumUnsavedItems(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetNumUnsavedItems(o);
	OUTPUT:
		RETVAL

void
getTrackCounts(o)
	tunepimp_t	o
	PREINIT:
		// eLastStatus is one more than the maximum valid status,
		// hence eLastStatus == count of valid status codes
		int buffer[eLastStatus];
		int numStatus;
		int i;
	CODE:
		numStatus = tp_GetTrackCounts(o, buffer, eLastStatus);
		++numStatus;

		sp -= items;
		EXTEND(SP, numStatus);

		for (i=0; i<numStatus; ++i)
		{
			PUSHs(sv_2mortal(newSViv(buffer[i])));
		}

		XSRETURN(numStatus);

void
getSupportedExtensions(o)
	tunepimp_t	o
	PREINIT:
		int num;
		int i;
		char *extensions;
	CODE:
		num = tp_GetNumSupportedExtensions(o);
		if (!num) XSRETURN_EMPTY;

		New(0, extensions, num*TP_EXTENSION_LEN, char);
		SAVEFREEPV(extensions);
		tp_GetSupportedExtensions(o, (void *)extensions);

		sp -= items;
		EXTEND(SP, num);

		for (i=0; i<num; ++i)
		{
			PUSHs(sv_2mortal(newSVpv(extensions+TP_EXTENSION_LEN*i, 0)));
		}

		XSRETURN(num);

track_t
_getTrack(o, fileId)
	tunepimp_t	o
	int	fileId
	CODE:
		RETVAL = tp_GetTrack(o, fileId);
	OUTPUT:
		RETVAL

void
_getVersion(o)
	tunepimp_t	o
	PREINIT:
		int major;
		int minor;
		int rev;
	CODE:
		tp_GetVersion(o, &major, &minor, &rev);
		sp -= items;
		EXTEND(SP, 3);
		XPUSHs(sv_2mortal(newSViv(major)));
		XPUSHs(sv_2mortal(newSViv(minor)));
		XPUSHs(sv_2mortal(newSViv(rev)));
		XSRETURN(3);

void
identifyAgain(o, fileId)
	tunepimp_t	o
	int	fileId
	CODE:
		tp_IdentifyAgain(o, fileId);

void
misidentified(o, fileId)
	tunepimp_t	o
	int	fileId
	CODE:
		tp_Misidentified(o, fileId);

void
_getRecognizedFileList(o, threshold)
	tunepimp_t	o
	int	threshold
	PREINIT:
		int numBelowThreshold;
		int *fileIds;
		int numIds;
		int i;
	CODE:
		numBelowThreshold = tp_GetRecognizedFileList(o, threshold, &fileIds, &numIds);

		sp -= items;
		EXTEND(sp, 1 + numIds);
		XPUSHs(sv_2mortal(newSViv(numBelowThreshold)));

		for (i = 0; i < numIds ; ++i)
		{
			XPUSHs(sv_2mortal(newSViv(fileIds[i])));
		}

		tp_DeleteRecognizedFileList(o, fileIds);
		XSRETURN(1 + numIds);

void
addTRMSubmission(o, trackId, trmId)
	tunepimp_t	o
	const char *trackId
	const char *trmId
	CODE:
		tp_AddTRMSubmission(o, trackId, trmId);

tunepimp_t
_new(appName, appVersion)
	const char *	appName
	const char *	appVersion
	CODE:
		RETVAL = tp_New(appName, appVersion);
	OUTPUT:
		RETVAL

void
_releaseTrack(o, track)
	tunepimp_t	o
	track_t	track
	CODE:
		tp_ReleaseTrack(o, track);

void
remove(o, fileId)
	tunepimp_t	o
	int	fileId
	CODE:
		tp_Remove(o, fileId);

TPError
selectResult(o, track, resultIndex)
	tunepimp_t	o
	track_t	track
	int	resultIndex
	CODE:
		tp_SelectResult(o, track, resultIndex);

void
setAllowedFileCharacters(o, allowedFileCharacters)
	tunepimp_t	o
	const char *	allowedFileCharacters
	CODE:
		tp_SetAllowedFileCharacters(o, allowedFileCharacters);

void
getAllowedFileCharacters(o)
	tunepimp_t	o
	PREINIT:
		char	chars[BIG_STRING];
	CODE:
		tp_GetAllowedFileCharacters(o, chars, BIG_STRING);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(chars, 0)));
		XSRETURN(1);

void
setAutoFileLookup(o, enable)
	tunepimp_t	o
	int	enable
	CODE:
		tp_SetAutoFileLookup(o, enable);

int
getAutoFileLookup(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetAutoFileLookup(o);
	OUTPUT:
		RETVAL

void
setAutoSaveThreshold(o, autoSaveThreshold)
	tunepimp_t	o
	int	autoSaveThreshold
	CODE:
		tp_SetAutoSaveThreshold(o, autoSaveThreshold);

int
getAutoSaveThreshold(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetAutoSaveThreshold(o);
	OUTPUT:
		RETVAL

void
setClearTags(o, clearTags)
	tunepimp_t	o
	int	clearTags
	CODE:
		tp_SetClearTags(o, clearTags);

int
getClearTags(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetClearTags(o);
	OUTPUT:
		RETVAL

void
setDebug(o, debug)
	tunepimp_t	o
	int	debug
	CODE:
		tp_SetDebug(o, debug);

int
getDebug(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetDebug(o);
	OUTPUT:
		RETVAL

void
setDestDir(o, destDir)
	tunepimp_t	o
	const char *	destDir
	CODE:
		tp_SetDestDir(o, destDir);

void
getDestDir(o)
	tunepimp_t	o
	PREINIT:
		char	destDir[BIG_STRING];
	CODE:
		tp_GetDestDir(o, destDir, BIG_STRING);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(destDir, 0)));
		XSRETURN(1);

void
setFileMask(o, fileMask)
	tunepimp_t	o
	const char *	fileMask
	CODE:
		tp_SetFileMask(o, fileMask);

void
getFileMask(o)
	tunepimp_t	o
	PREINIT:
		char	fileMask[BIG_STRING];
	CODE:
		tp_GetFileMask(o, fileMask, BIG_STRING);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(fileMask, 0)));
		XSRETURN(1);

void
setMoveFiles(o, move)
	tunepimp_t	o
	int	move
	CODE:
		tp_SetMoveFiles(o, move);

int
getMoveFiles(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetMoveFiles(o);
	OUTPUT:
		RETVAL

void
setNotifyCallback(o, cb)
	tunepimp_t	o
	SV * cb
	CODE:
		if (cb == &PL_sv_undef)
		{
			if (!perl_notify_callback) XSRETURN_UNDEF;

			SvREFCNT_dec(SvRV(perl_notify_callback));
			perl_notify_callback = NULL;
			tp_SetNotifyCallback(o, NULL, NULL);
			XSRETURN_UNDEF;
		}

		if (!SvROK(cb)) croak("cb must be a defined CODE reference");
		cb = SvRV(cb);

		if (SvTYPE(cb) != SVt_PVCV) croak("cb must be a defined CODE reference");
		if (!CvROOT(cb)) croak("cb must be a defined CODE reference");

		perl_notify_callback = newRV_inc(cb);

		tp_SetNotifyCallback(o, (tp_notify_callback) &notify_callback, NULL);

# TODO update this
SV *
getNotifyCallback(o)
	tunepimp_t o
	CODE:
		if (!perl_notify_callback) XSRETURN_UNDEF;
		RETVAL = newRV_inc(SvRV(perl_notify_callback));
	OUTPUT:
		RETVAL

void
getNotification(o)
	tunepimp_t o
	PREINIT:
		TPCallbackEnum type;
		int fileId;
		TPFileStatus status;
	CODE:
		if (!tp_GetNotification(o, &type, &fileId, &status))
			XSRETURN_EMPTY;
		sp -= items;
		XPUSHs(sv_2mortal(newSViv(type)));
		XPUSHs(sv_2mortal(newSViv(fileId)));
		XPUSHs(sv_2mortal(newSViv(status)));
		XSRETURN(3);

void
setProxy(o, proxyAddr, proxyPort)
	tunepimp_t	o
	const char *	proxyAddr
	short	proxyPort
	CODE:
		tp_SetProxy(o, proxyAddr, proxyPort);

void
_getProxy(o)
	tunepimp_t	o
	PREINIT:
		char	proxyAddr[BIG_STRING];
		short	proxyPort;
	CODE:
		tp_GetProxy(o, proxyAddr, BIG_STRING, &proxyPort);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(proxyAddr, 0)));
		XPUSHs(sv_2mortal(newSViv((int)proxyPort)));
		XSRETURN(2);

void
setAnalyzerPriority(o, priority)
	tunepimp_t	o
	int	priority
	CODE:
		tp_SetAnalyzerPriority(o, priority);

int
getAnalyzerPriority(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetAnalyzerPriority(o);
	OUTPUT:
		RETVAL

void
setMaxFileNameLen(o, maxFileNameLen)
	tunepimp_t	o
	int	maxFileNameLen
	CODE:
		tp_SetMaxFileNameLen(o, maxFileNameLen);

int
getMaxFileNameLen(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetMaxFileNameLen(o);
	OUTPUT:
		RETVAL

void
setAutoRemovedSavedFiles(o, autoRemoveSavedFiles)
	tunepimp_t	o
	int	autoRemoveSavedFiles
	CODE:
		tp_SetAutoRemovedSavedFiles(o, autoRemoveSavedFiles);

int
getAutoRemovedSavedFiles(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetAutoRemovedSavedFiles(o);
	OUTPUT:
		RETVAL

void
setRenameFiles(o, rename)
	tunepimp_t	o
	int	rename
	CODE:
		tp_SetRenameFiles(o, rename);

int
getRenameFiles(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetRenameFiles(o);
	OUTPUT:
		RETVAL

void
setServer(o, serverAddr, serverPort)
	tunepimp_t	o
	const char *	serverAddr
	short	serverPort
	CODE:
		tp_SetServer(o, serverAddr, serverPort);

void
_getServer(o)
	tunepimp_t	o
	PREINIT:
		char	serverAddr[BIG_STRING];
		short	serverPort;
	CODE:
		tp_GetServer(o, serverAddr, BIG_STRING, &serverPort);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(serverAddr, 0)));
		XPUSHs(sv_2mortal(newSViv((int)serverPort)));
		XSRETURN(2);

void
setStatusCallback(o, cb)
	tunepimp_t	o
	SV * cb
	CODE:
		if (cb == &PL_sv_undef)
		{
			if (!perl_status_callback) XSRETURN_UNDEF;

			SvREFCNT_dec(SvRV(perl_status_callback));
			perl_status_callback = NULL;
			tp_SetStatusCallback(o, NULL, NULL);
			XSRETURN_UNDEF;
		}

		if (!SvROK(cb)) croak("cb must be a defined CODE reference");
		cb = SvRV(cb);

		if (SvTYPE(cb) != SVt_PVCV) croak("cb must be a defined CODE reference");
		if (!CvROOT(cb)) croak("cb must be a defined CODE reference");

		perl_status_callback = newRV_inc(cb);

		tp_SetStatusCallback(o, (tp_status_callback) &status_callback, NULL);

# TODO update this
SV *
getStatusCallback(o)
	tunepimp_t o
	CODE:
		if (!perl_status_callback) XSRETURN_UNDEF;
		RETVAL = newRV_inc(SvRV(perl_status_callback));
	OUTPUT:
		RETVAL

void
getStatus(o)
	tunepimp_t o
	PREINIT:
		char status[BIG_STRING];
	CODE:
		if (!tp_GetStatus(o, status, BIG_STRING))
			XSRETURN_UNDEF;
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(status, 0)));
		XSRETURN(1);

void
setTRMCollisionThreshold(o, trmThreshold)
	tunepimp_t	o
	int	trmThreshold
	CODE:
		tp_SetTRMCollisionThreshold(o, trmThreshold);

int
getTRMCollisionThreshold(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetTRMCollisionThreshold(o);
	OUTPUT:
		RETVAL

void
setMinTRMThreshold(o, trmThreshold)
	tunepimp_t	o
	int	trmThreshold
	CODE:
		tp_SetMinTRMThreshold(o, trmThreshold);

int
getMinTRMThreshold(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetMinTRMThreshold(o);
	OUTPUT:
		RETVAL

void
setTopSrcDir(o, topSrcDir)
	tunepimp_t	o
	const char *	topSrcDir
	CODE:
		tp_SetTopSrcDir(o, topSrcDir);

void
getTopSrcDir(o)
	tunepimp_t	o
	PREINIT:
		char	topSrcDir[BIG_STRING];
	CODE:
		tp_GetTopSrcDir(o, topSrcDir, BIG_STRING);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(topSrcDir, 0)));
		XSRETURN(1);

void
setUserInfo(o, userName, password)
	tunepimp_t	o
	const char *	userName
	const char *	password
	CODE:
		tp_SetUserInfo(o, userName, password);

void
_getUserInfo(o)
	tunepimp_t	o
	PREINIT:
		char	userName[BIG_STRING];
		char	password[BIG_STRING];
	CODE:
		tp_GetUserInfo(o, userName, BIG_STRING, password, BIG_STRING);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(userName, 0)));
		XPUSHs(sv_2mortal(newSVpv(password, 0)));
		XSRETURN(2);

void
setVariousFileMask(o, variousFileMask)
	tunepimp_t	o
	const char *	variousFileMask
	CODE:
		tp_SetVariousFileMask(o, variousFileMask);

void
getVariousFileMask(o)
	tunepimp_t	o
	PREINIT:
		char	variousFileMask[BIG_STRING];
	CODE:
		tp_GetVariousFileMask(o, variousFileMask, BIG_STRING);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(variousFileMask, 0)));
		XSRETURN(1);

void
setNonAlbumFileMask(o, nonAlbumFileMask)
	tunepimp_t	o
	const char *	nonAlbumFileMask
	CODE:
		tp_SetNonAlbumFileMask(o, nonAlbumFileMask);

void
getNonAlbumFileMask(o)
	tunepimp_t	o
	PREINIT:
		char	nonAlbumFileMask[BIG_STRING];
	CODE:
		tp_GetNonAlbumFileMask(o, nonAlbumFileMask, BIG_STRING);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(nonAlbumFileMask, 0)));
		XSRETURN(1);

void
setWriteID3v1(o, writeID3v1)
	tunepimp_t	o
	int	writeID3v1
	CODE:
		tp_SetWriteID3v1(o, writeID3v1);

int
getWriteID3v1(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetWriteID3v1(o);
	OUTPUT:
		RETVAL

TPError
submitTRMs(o)
	tunepimp_t	o
	CODE:
		tp_SubmitTRMs(o);

void
setUseUTF8(o, useUTF8)
	tunepimp_t	o
	int	useUTF8
	CODE:
		tp_SetUseUTF8(o, useUTF8);

int
getUseUTF8(o)
	tunepimp_t	o
	CODE:
		RETVAL = tp_GetUseUTF8(o);
	OUTPUT:
		RETVAL

void
wake(o, track)
	tunepimp_t	o
	track_t	track
	CODE:
		tp_Wake(o, track);

int
_writeTags(o, fileIds, numFileIds)
	tunepimp_t	o
	char *	fileIds
	int	numFileIds
	CODE:
		RETVAL = tp_WriteTags(o, (int *)fileIds, numFileIds);
	OUTPUT:
		RETVAL


MODULE = MusicBrainz::Tunepimp::track		PACKAGE = MusicBrainz::Tunepimp::track

INCLUDE: const-xs.inc

void
lock(t)
	track_t	t
	CODE:
		tr_Lock(t);

void
unlock(t)
	track_t	t
	CODE:
		tr_Unlock(t);

void
getError(t)
	track_t	t
	PREINIT:
		char	error[BIG_STRING];
	CODE:
		tr_Lock(t);
		tr_GetError(t, error, BIG_STRING);
		tr_Unlock(t);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(error, 0)));
		XSRETURN(1);

char *
getFileName(t)
	track_t	t
	PREINIT:
		char	fileName[BIG_STRING];
	CODE:
		tr_Lock(t);
		tr_GetFileName(t, fileName, BIG_STRING);
		tr_Unlock(t);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(fileName, 0)));
		XSRETURN(1);

void
_getLocalMetadata(t, mdata)
	track_t	t
	metadata_t *	mdata
	CODE:
		tr_Lock(t);
		tr_GetLocalMetadata(t, mdata);
		tr_Unlock(t);

int
getNumResults(t)
	track_t	t
	CODE:
		tr_Lock(t);
		RETVAL = tr_GetNumResults(t);
		tr_Unlock(t);
	OUTPUT:
		RETVAL

void
getResults(t)
	track_t	t
	PREINIT:
		result_t *	results;
		TPResultType type;
		int numResults;
		int i;
		SV *sv;
		AV *av;
	CODE:
		tr_Lock(t);
		numResults = tr_GetNumResults(t);
		if (!numResults) { tr_Unlock(t); XSRETURN_EMPTY; }

		New(0, results, numResults, result_t);
		SAVEFREEPV(results);
		tr_GetResults(t, &type, results, &numResults);
		tr_Unlock(t);

		av = newAV();
		av_fill(av, numResults-1);

		for (i=0; i<numResults; ++i)
		{
			SV *sv;

			if (type == eArtistList)	sv = _flatten_artist_result((artistresult_t *)results[i]);
			else if (type == eAlbumList)	sv = _flatten_album_result((albumresult_t *)results[i]);
			else if (type == eTrackList)	sv = _flatten_track_result((albumtrackresult_t *)results[i]);
			else sv = &PL_sv_undef;

			av_store(av, i, sv);
		}

		rs_Delete(type, results, numResults);

		sp -= items;
		XPUSHs(sv_2mortal(newSViv(type)));
		XPUSHs(sv_2mortal(newRV_noinc((SV *)av)));
		XSRETURN(2);

void
_getServerMetadata(t, mdata)
	track_t	t
	metadata_t *	mdata
	CODE:
		tr_Lock(t);
		tr_GetServerMetadata(t, mdata);
		tr_Unlock(t);

int
getSimilarity(t)
	track_t	t
	CODE:
		tr_Lock(t);
		RETVAL = tr_GetSimilarity(t);
		tr_Unlock(t);
	OUTPUT:
		RETVAL

TPFileStatus
getStatus(t)
	track_t	t
	CODE:
		tr_Lock(t);
		RETVAL = tr_GetStatus(t);
		tr_Unlock(t);
	OUTPUT:
		RETVAL

void
getTRM(t)
	track_t	t
	PREINIT:
		char	trm[TRM_LENGTH+1];
	CODE:
		tr_Lock(t);
		tr_GetTRM(t, trm, TRM_LENGTH+1);
		tr_Unlock(t);
		sp -= items;
		XPUSHs(sv_2mortal(newSVpv(trm, 0)));
		XSRETURN(1);

int
hasChanged(t)
	track_t	t
	CODE:
		tr_Lock(t);
		RETVAL = tr_HasChanged(t);
		tr_Unlock(t);
	OUTPUT:
		RETVAL

void
setLocalMetadata(t, mdata)
	track_t	t
	const metadata_t *	mdata
	CODE:
		tr_Lock(t);
		tr_SetLocalMetadata(t, mdata);
		tr_Unlock(t);

void
setServerMetadata(t, mdata)
	track_t	t
	const metadata_t *	mdata
	CODE:
		tr_Lock(t);
		tr_SetServerMetadata(t, mdata);
		tr_Unlock(t);

void
setStatus(t, status)
	track_t	t
	TPFileStatus	status
	CODE:
		tr_Lock(t);
		tr_SetStatus(t, status);
		tr_Unlock(t);

MODULE = MusicBrainz::Tunepimp::tunepimp	PACKAGE = MusicBrainz::Tunepimp::tunepimp
