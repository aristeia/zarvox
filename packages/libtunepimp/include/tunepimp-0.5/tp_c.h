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

   $Id: tp_c.h 8360 2006-08-07 21:05:12Z luks $

----------------------------------------------------------------------------*/
#ifndef _TP_C_H_
#define _TP_C_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include "defs.h"

/**
 * tunepimp_t is the basic C abstraction for a TunePimp Object. It is
 * completely transparent for the user. Don't try to manipulate it manually,
 * use one of the functions starting with "tp_".
 */
typedef void *tunepimp_t;


/**
 * The abstraction of a Track object. Functions to manipulate have a prefix
 * of "tr_".
 */
typedef void *track_t;


/**
 * This is the signature definition of a function suitable as a notification
 * callback. The data argument is the pointer that the user gave
 * when registering the function using tp_SetNotifyCallback().
 *
 * @param pimp the tunepimp object that invoked the callback function
 * @param data a pointer to user data set when registering the callback
 * @param type the type of this notification
 * @param fileId the Id of the file concerned
 *
 * @see tp_SetNotifyCallback()
 */
typedef void (*tp_notify_callback)(tunepimp_t pimp, void *data, TPCallbackEnum
type, int fileId, TPFileStatus status);


/**
 * This is the signature definition of a function suitable as a status
 * callback. The data argument is the pointer that the user gave
 * when registering the function using tp_SetStatusCallback().
 *
 * @param pimp the tunepimp object that invoked the callback function
 * @param data a pointer to user data set when registering the callback
 * @param status a pointer to a text message
 *
 * @see tp_SetStatusCallback()
 */
typedef void (*tp_status_callback)(tunepimp_t pimp, void *data, const char *status);


/**
 * This structure holds the meta data of a track.
 *
 * The meanings of most attributes are pretty straight forward, but a few
 * need additional explanations. Strings like artist, sortName, album etc.
 * are never NULL. If the information isn't available, the attribute is
 * set to the empty string ("").
 *
 * The duration attribute is in milliseconds. fileFormat is one of the
 * supported file formats (see tp_GetSupportedExtensions()) but without
 * the dot ("mp3", "ogg", "wav" etc.). If there was a PUID collision,
 * numPUIDIds is set to a value greater than one. If variousArtist is true,
 * the track is from a various artists release. If nonAlbum is true, the
 * track resides within a special non-album tracklisting.
 *
 * The memory containing the meta data will be released when calling
 * md_Clear() or md_Delete(), so you have to copy the data if you want
 * to use it.
 *
 * @see md_New(), md_Clear(), md_Delete()
 *      tr_GetLocalMetadata(), tr_SetLocalMetadata(),
 *      tr_GetServerMetadata(), tr_SetServerMetadata()
 */
#define TP_ARTIST_NAME_LEN 255
#define TP_ALBUM_NAME_LEN  255
#define TP_TRACK_NAME_LEN  255
#define TP_ID_LEN           40
#define TP_FORMAT_LEN       32
#define TP_COUNTRY_LEN       3
typedef struct _metadata_t
{
    char          artist[TP_ARTIST_NAME_LEN];
    char          sortName[TP_ARTIST_NAME_LEN];
    char          album[TP_ALBUM_NAME_LEN];
    char          track[TP_TRACK_NAME_LEN];
    int           trackNum;
    int           totalInSet;
    int           variousArtist;
    int           nonAlbum;
    char          artistId[TP_ID_LEN];   
    char          albumId[TP_ID_LEN];   
    char          trackId[TP_ID_LEN];
    char          filePUID[TP_ID_LEN];
    char          albumArtistId[TP_ID_LEN];
    unsigned long duration;
    TPAlbumType   albumType;
    TPAlbumStatus albumStatus;
    char          fileFormat[TP_FORMAT_LEN];
    int           releaseYear, releaseDay, releaseMonth;
    char          releaseCountry[TP_COUNTRY_LEN];

    // This is only used in case of PUID collision
    int           numPUIDIds;
    
    char          albumArtist[TP_ARTIST_NAME_LEN];
    char          albumArtistSortName[TP_ARTIST_NAME_LEN];
} metadata_t;


/* --------------------------------------------------------------------------
 * Main TunePimp Interface
 * --------------------------------------------------------------------------*/

/**
 * Create a new handle (a C abstraction) to the TunePimp object.
 * Call tp_Delete() when done with the handle.
 *
 * @param appName the name of your application
 * @param appVersion the version number of your application
 * @return the tunepimp_t type is used in subsequent tunepimp functions.
 *
 * @see tp_Delete()
 */
tunepimp_t tp_New           (const char *appName, const char *appVersion);

/**
 * Create a new handle (a C abstraction) to the TunePimp object, specifying
 * which internal threads to start.
 * Call tp_Delete() when done with the handle.
 *
 * @param appName the name of your application
 * @param appVersion the version number of your application
 * @param startThreads a bit flag that specifies which internal threads to
 *                     start. Pass in one or more TP_THREAD_XXXX flags that are or'ed together.
 * @param pluginDir the directory where tunepimp plugins can be found
 * @return the tunepimp_t type is used in subsequent tunepimp functions.
 *
 * @see tp_Delete()
 */
tunepimp_t tp_NewWithArgs   (const char *appName, const char *appVersion, 
                             int startThreads, const char *pluginDir);

/**
 * The destructor for the TunePimp class.
 *
 * @param o the handle for the tunepimp_t object to delete
 *
 * @see tp_New()
 */
void      tp_Delete         (tunepimp_t o);


/**
 * Get the version number of this library.
 *
 * @param o the tunepimp_t object returned from tp_New
 * @param major an int pointer that will receive the major number of the version
 * @param minor an int pointer that will receive the minor number
 * @param rev   an int pointer that will receive the rev number
 */
void      tp_GetVersion     (tunepimp_t o, int *major, int *minor, int *rev);


/**
 * Set the MusicDNS clientId.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param clientId a client id
 *
 */
void	tp_SetMusicDNSClientId(tunepimp_t o, const char *clientId);


/**
 * Get the MusicDNS clientId that was set with the tp_SetMusicDNSClientId
 * function.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param clientId a user supplied buffer of maxClientIdLen characters
 * @param maxClientIdLen the max size of the buffer for the client name
 *
 */
void       tp_GetMusicDNSClientId(tunepimp_t o, char *clientId, int maxClientIdLen);

/**
 * Use this function to specify the encoding to be used for
 * writing filenames to the filesystem. Defaults to UTF-8.
 *
 * UTF-8 and ISO-8859-1 are supported by default and more
 * encodings are supported by ICU is ICU is available to libtp
 * at compilation time.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param encoding the encoding to use. Must be 'UTF-8', 'ISO-8859-1' or
 * an ICU supported encoding.
 *
 * @see tp_GetFileNameEncoding()
 */
void      tp_SetFileNameEncoding(tunepimp_t o, const char *encoding);


/**
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @param encoding the encoding to use.
 * @param maxEncodingLen length of the encoding string
 *
 * @see tp_SetFileNameEncoding()
 */
void tp_GetFileNameEncoding(tunepimp_t o, char *encoding, int maxEncodingLen);


/**
 * Set the name and the port of the MusicBrainz server to use. If this
 * function is not called, the default www.musicbrainz.org server on port
 * 80 will be used.

 * @param o the tunepimp_t object returned from tp_New
 * @param serverAddr the name of the musicbrainz server to use 
 *                   e.g. www.musicbrainz.org
 * @param serverPort the port number to use. e.g. 80
 *
 * @see tp_GetServer(), tp_SetProxy()
 */
void       tp_SetServer      (tunepimp_t o, const char *serverAddr, 
                              short serverPort);


/**
 * Get the server settings. tp_GetServer() stores the address in a user
 * supplied buffer. Not more than maxLen characters including the
 * trailing '\\0' byte are copied into that buffer.
 *
 * If no proxy was set, serverAddr is set to the empty string ("").
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param serverAddr a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 * @param serverPort the address of a variable to receive the port
 *
 * @see tp_SetServer()
 */
void tp_GetServer(tunepimp_t o, char *serverAddr, int maxLen,
                                short *serverPort);


/**
 * Set the name of the HTTP Proxy to use. This function must be called anytime
 * the client library must communicate via a proxy firewall. 
 * To disable the use of the proxy server, set serverAddr to the empty
 * string ("").
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param serverAddr the name of the proxy server to use 
 *                   e.g. proxy.mydomain.com
 * @param serverPort the port number to use. e.g. 8080
 *
 * @see tp_GetProxy(), tp_SetServer()
 */
void       tp_SetProxy          (tunepimp_t o, const char *serverAddr, short serverPort);


/**
 * Get the proxy settings. tp_GetProxy() stores the address in a user supplied
 * buffer. Not more than maxLen characters including the trailing '\\0' byte
 * are copied into that buffer.
 *
 * If no proxy was set, serverAddr is set to the empty string ("").
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param serverAddr a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 * @param serverPort the address of a variable to receive the port
 *
 * @see tp_SetProxy()
 */
void tp_GetProxy(tunepimp_t o, char *serverAddr, int maxLen, short *serverPort);


/**
 * Query the number of audio file formats supported by tunepimp. The number
 * depends on which libraries were present when tunepimp was compiled.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @returns the number of supported audio file formats
 *
 * @see tp_GetSupportedExtensions()
 */
int tp_GetNumSupportedExtensions(tunepimp_t o);


/**
 * This function returns a list of supported audio formats. The elements
 * of the list are the usual filename extensions like ".wav", ".mp3",
 * ".ogg" etc.
 *
 * The buffer you pass to the function has to be big enough to hold the
 * list. You can use tp_GetNumSupportedExtensions() to get the number of
 * supported extensions.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param extensions a user supplied buffer for the list of filename extensions
 *
 * @see tp_GetNumSupportedExtensions()
 */
#define TP_EXTENSION_LEN 32 
void tp_GetSupportedExtensions(tunepimp_t o, char extensions[][TP_EXTENSION_LEN]);

/**
 * This function sets the analyzer thread priority level.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param priority The priority to set the analyzer to. See include/defs.h for
 *                 values for this parameter.
 *
 * @see tp_GetAnalyzerPriority()
 */
void tp_SetAnalyzerPriority(tunepimp_t o, TPThreadPriorityEnum priority);

/**
 * This function gets the analyzer thread priority level.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @returns The current analyzer thread priorty. See include/defs.h for possible
 *          return codes.
 *
 * @see tp_SetAnalyzerPriority()
 */
TPThreadPriorityEnum tp_GetAnalyzerPriority(tunepimp_t o);


/**
 * Use this function to register a callback function with tunepimp that
 * gets called each time a file is added (using tp_AddFile() or tp_AddDir()),
 * removed (using tp_Remove()) or changed.
 * A change is signalled every time the status of a track changes.
 *
 * Note that if a callback is provided the tp_GetNotification() function will
 * no longer return notification messages. To unset a callback, pass in NULL
 * to this function. Only one function may be registered at a time.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param callback a function pointer to set or NULL to unset a callback
 * @param data a private data member that will be passed back verbatim to the callback
 *
 * @see tp_SetStatusCallback(), tr_GetStatus(), tp_GetNotification(),
 *      tp_GetNotifyCallback()
 */
void tp_SetNotifyCallback(tunepimp_t o, tp_notify_callback callback, void *data);


/**
 * Get the function registered to receive notification messages. See
 * tp_SetNotifyCallback() for more information.
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @returns the previously registered callback or NULL if none was registered
 *
 * @see tp_SetNotifyCallback()
 */
tp_notify_callback tp_GetNotifyCallback(tunepimp_t o);


/**
 * Get a notification message from tunepimp's queue. All messages are
 * stored in a queue (FIFO) to make sure you get them in the right
 * order.
 *
 * Please note that this function only returns notification messages if 
 * no notification callback was set.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param type the address of a variable to receive the notification type
 * @param fileId the address of a variable to receive the fileId
 * @param status the address of a variable to receive the current status
 *
 * @returns true if there was a notification message in the queue and false
 *          otherwise
 *
 * @see tp_SetNotifyCallback(), tp_GetNotifyCallback()
 */
int tp_GetNotification(tunepimp_t o, TPCallbackEnum *type, int *fileId, TPFileStatus *status);


/**
 * Use this function to register a callback function to receive
 * textual messages describing tunepimp's current status. The messages
 * are intended for direct output to the user. Don't try to parse
 * the messages. All important information can be retrieved by other
 * means.
 *
 * Note that if a callback is provided the tp_GetStatusCallback() function
 * will no longer return Status messages. To unset a callback, pass in NULL
 * to this function. Only one function may be registered at a time.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param callback a function pointer to set or NULL to unset a callback
 * @param data a private data member that will be passed back verbatim to the callback
 *
 * @see tp_SetNotifyCallback(), tp_GetError(), tp_GetStatusCallback()
 */
void tp_SetStatusCallback(tunepimp_t o, tp_status_callback callback, void *data);


/**
 * Get a status message from tunepimp's queue. All messages are
 * stored in a queue (FIFO) to make sure you get them in the right
 * order.
 *
 * Please note that this function only returns status messages if 
 * no status callback was set.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param status a user supplied buffer of statusLen characters
 * @param statusLen the size of the buffer
 *
 * @returns true if there was a status message in the queue and false otherwise
 *
 * @see tp_SetStatusCallback(), tp_GetStatusCallback()
 */
int tp_GetStatus(tunepimp_t o, char *status, int statusLen);


/**
 * Get the function registered to receive status messages. See
 * tp_SetStatusCallback() for more information.
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @returns the previously registered callback or NULL if none was registered
 *
 * @see tp_SetStatusCallback()
 */
tp_status_callback tp_GetStatusCallback(tunepimp_t o);


/**
 * Use this function to get a printable error message for the last
 * error that occured in the tunepimp object. tp_GetError() stores the
 * error string in a user supplied buffer. Not more than maxLen characters
 * including the trailing '\\0' byte are copied into that buffer.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param error a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 */
void tp_GetError(tunepimp_t o, char *error, int maxLen);


/**
 * Enable debugging output to stdout by sending a non-zero value to this
 * function. Whenever the tunepimp library makes a server call, the 
 * data sent to the server and the data returned from the server is printed 
 * to stdout.
 *
 * Default: disabled.
 *
 * @param o the tunepimp_t object returned from tp_New
 * @param debug whether or not to enable debug (non-zero enables debug output)
 *
 * @see tp_GetDebug(), tp_GetError()
 */
void       tp_SetDebug        (tunepimp_t o, int debug);


/**
 * Check if debugging is enabled.
 *
 * @param o the tunepimp_t object returned from tp_New
 *
 * @returns true if debuggin is enabled and false otherwise
 *
 * @see tp_SetDebug()
 */
int tp_GetDebug(tunepimp_t o);


/**
 * Add a file to the list. The fileId of the added file is returned which is
 * a handle that is valid until the file is removed using tp_Remove() or
 * TunePimp writes new metadata tags and automatically removes the file.
 * Adding a file that is already in the list is a no-op. Initially, the status
 * of a file is ePending.
 *
 * For each file added, your registered notification callback is invoked.
 * Its parameters are tpFileAdded and the fileId returned by tp_Add().
 *
 * Please note that tp_AddFile() always succeeds, no matter if the file isn't
 * a recognized audio file, if it isn't readable or doesn't exist at all.
 * However, you can always query the track's status to see if there was
 * an error.
 *
 * @param o the tunepimp_t object returned from tp_New
 * @param fileName a string containing a filename
 * @param readMetadataNow read the file metadata before returning
 * @returns a fileId handle for your file
 *
 * @see tp_AddDir(), tp_SetNotifyCallback()
 */
int       tp_AddFile          (tunepimp_t o, const char *fileName, int readMetadataNow);


/**
 * This function descends recursively into the specified directory and
 * adds all files to the list that look like they contain music, judging
 * by comparing file extensions. You can get a list of supported file
 * formats using tp_GetSupportedExtensions().
 * 
 * @param o the tunepimp_t object returned from tp_New
 * @param dirPath a string containing a path
 *
 * @returns the number of files found, -1 on error
 *
 * @see tp_Add(), tp_GetSupportedExtensions()
 */
int       tp_AddDir                (tunepimp_t o, const char *dirPath);


/**
 * Remove a file entry from the list. fileId is the file's handle returned
 * by tp_Add(). The file itself isn't removed from disk.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param fileId the Id of the file you want to remove.
 *
 * @see tp_Add(), tp_AddDir()
 */
void      tp_Remove                (tunepimp_t o, int fileId);


/**
 * This function returns the number of files that tunepimp has in its list.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @returns the number of files in the list
 *
 * @see tp_Add(), tp_AddDir(), tp_Remove()
 */
int       tp_GetNumFiles           (tunepimp_t o);


/**
 * This function returns the number of track that have been recognized
 * and are ready to be saved.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @returns the number of tracks not saved
 */
int       tp_GetNumUnsavedItems    (tunepimp_t o);

/**
 * This function returns the number of tracks in each of the
 * TPFileStatus categories. For example, the count for
 * the number of unrecognized files will be stored in:
 *   counts[(int)eUnrecognized]
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param counts a pointer to an array of ints that will receive the counts
 * @param maxCounts max number of counts that can be written to the counts array.
 */
int       tp_GetTrackCounts(tunepimp_t o, int *counts, int maxCounts);

/**
 * Get the number of filesIds that a call to tp_GetFileIds() would return.
 *
 * Do not use tp_Add() or tp_AddDir() between calls to tp_GetNumFileIds()
 * and tp_GetFileIds(). They might increase the number of fileIds.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @returns the number of fileIds
 *
 * @see tp_GetFileIds()
 */
int       tp_GetNumFileIds         (tunepimp_t o);


/**
 * Returns the fileIds in tunepimp's list. At most numIds are returned.
 *
 * Use tp_GetNumFileIds to get the number of fileIds in the list. Do not
 * use tp_Add() or tp_AddDir() between calls to tp_GetNumFileIds() and
 * tp_GetFileIds().
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param numIds the number of fileIds the buffer can receive
 * @param ids a poiner to the buffer that will receive the fileIds
 *
 * @see tp_GetNumFileIds()
 */
void      tp_GetFileIds            (tunepimp_t o, int *ids, int numIds);


/**
 * Get a handle for a track object. Don't forget to release the track using
 * tp_ReleaseTrack() when you don't need it any longer. YOU MUST CALL
 * tr_Lock() BEFORE YOU MAKE ANY CHANGES TO THE TRACK. After your changes
 * are complete, call tr_Unlock. 
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param fileId a fileId
 * @returns a track handle or NULL if fileId isn't associated with a track
 *
 * @see tp_ReleaseTrack(), @see tr_Lock(), @see tr_Unlock()
 */
track_t   tp_GetTrack             (tunepimp_t o, int fileId);


/**
 * Release the specified track object.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param track the track handle
 *
 * @see tp_GetTrack(), @see tr_Lock(), @see tr_Unlock()
 */
void      tp_ReleaseTrack          (tunepimp_t o, track_t track);


/**
 * Wake up tunepimp to look for work to do.
 *
 * You have to call this function every time you change a track's
 * status using tr_SetStatus(). This call will wake up the
 * TunePimp internal threads to look for tracks that need to be
 * processed. If you do not call this function after you make a 
 * change to a track, the change will be ignored.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param track the handle of the track that changed
 *
 * @see tr_SetStatus()
 */
void      tp_Wake                  (tunepimp_t o, track_t track);


/**
 * Discard all MusicBrainz idenitifiers and identify this file again. 
 * The status is set back to ePending which causes the whole identification 
 * process to start again, including PUID generation.
 * 
 * @param o the tunepimp_t object returned from tp_New()
 * @param fileId a fileId
 *
 * @see tp_IdentifyAgain()
 */
void      tp_Misidentified         (tunepimp_t o, int fileId);

/**
 * Mark a file as misidentified. 
 * 
 * @param o the tunepimp_t object returned from tp_New()
 * @param fileId a fileId
 *
 * @see tp_Misidentified()
 */
void      tp_IdentifyAgain         (tunepimp_t o, int fileId);

/**
 * Write tags for the specified files. Only files in state eRecognized
 * will be written. If renaming was enabled using tp_SetRenameFiles(),
 * the files are also renamed as specified in the file part of the file
 * mask. Otherwise, the file name stays as it is.
 *
 * If moving was enabled using tp_SetMoveFiles(), the files are moved to
 * the destination directory (see tp_SetDestDir()) while keeping their
 * original file names. If, additionally, renaming was enabled, the
 * files are moved to a subdirectory of the destination directory depending
 * on the directory part of the file mask.
 *
 * If fileIds is set to the NULL pointer, all recognized files are
 * written. In this case the numFileIds argument is ignored.
 *
 * tp_WriteTags() doesn't return an error indicator if there were
 * problems writing the files. You have to check the track status
 * to see if writing was successful. The state is changed to eDeleted on
 * success and deleted as soon as neither tunepimp nor the client
 * have any more references to the track. The status is set to
 * eError if an error occurs. Until writing of a track is done,
 * the track stays in state eVerified.
 *
 * Please note that files that had a similarity greater or equal to
 * the AutoSaveThreshold are written automatically, right after
 * they have been recognized.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param fileIds a pointer to an array of fileIds or NULL
 * @param numFileIds the number of fileIds in the array
 *
 * @returns zero if a fileId was invalid or not all files were recognized
 *
 * @see tp_SetAutoSaveThreshold(), tp_SetMoveFiles(), tp_SetRenameFiles,
 *      tp_SetAllowedFileChars(), tp_SetWriteID3v1(), tr_GetState(),
 *      tp_SetFileMask(), tp_SetVariousFileMask(), tp_SetDestDir(),
 *      tp_SetNonAlbumFileMask(), tp_SetWriteID3v2_3(), tp_SetID3Encoding()
 */
int      tp_WriteTags             (tunepimp_t o, int *fileIds, int numFileIds);


/**
 * If enabled, files are renamed as specified in the file mask or the
 * various artists file mask. Only the file name is changed, this
 * setting doesn't imply moving the file to a new directory.
 *
 * Default: enabled.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param rename set a non-zero value to enable renaming
 *
 * @see tp_GetRenameFiles(), tp_SetMoveFiles(), tp_WriteTags(),
 *      tp_SetFileMask(), tp_SetVariousFileMask(),
 *      tp_SetNonAlbumFileMask()
 */
void      tp_SetRenameFiles          (tunepimp_t o, int rename);


/**
 * Query the tunepimp object if file renaming is enabled. See
 * tp_SetRenameFiles() for an explanation.
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @returns true if file renaming was enabled and false otherwise
 *
 * @see tp_SetRenameFiles()
 */
int tp_GetRenameFiles(tunepimp_t o);


/**
 * If enabled, files are moved to the destination directory as specified
 * in the file mask or the various artists file mask. Files are only moved
 * to a new directory, but the file name isn't changed.
 *
 * Default: enabled.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param move set a non-zero value to enable moving
 *
 * @see tp_GetMoveFiles(), tp_SetRenameFiles(), tp_WriteTags(),
 *      tp_SetFileMask(), tp_SetVariousFileMask(), tp_SetDestDir(),
 *      tp_SetNonAlbumFileMask()
 */
void      tp_SetMoveFiles            (tunepimp_t o, int move);


/**
 * Check if file moving is enabled. See tp_SetMoveFiles() for more information.
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @returns true if file moving was enabled and false otherwise
 *
 * @see tp_SetMoveFiles()
 */
int tp_GetMoveFiles(tunepimp_t o);


/**
 * Use this function to enable writing of legacy ID3v1 tags to
 * MP3 files. ID3v1 tags are supported by almost every existing MP3 player.
 *
 * Default: enabled.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param writeID3v1 set a non-zero value to enable ID3v1 tags
 *
 * @see tp_GetWriteID3v1(), tp_WriteTags()
 */
void      tp_SetWriteID3v1           (tunepimp_t o, int writeID3v1);


/**
 * Check if writing ID3v1 tags to MP3 files is enabled.
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @returns true if ID3v1 writing is enabled and false otherwise
 *
 * @see tp_SetWriteID3v1()
 */
int tp_GetWriteID3v1(tunepimp_t o);


/**
 * Use this function to enable writing of ID3v2.3 tags to
 * MP3 files. ID3v2.4 tags are the default for tunepimp.
 *
 * Default: disabled
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param writeID3v2_3 set a non-zero value to enable ID3v2_3 tags
 *
 * @see tp_GetWriteID3v2_3(), tp_WriteTags()
 */
void      tp_SetWriteID3v2_3           (tunepimp_t o, int writeID3v2_3);


/**
 * Check if writing ID3v2_3 tags to MP3 files is enabled.
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @returns true if ID3v2_3 writing is enabled and false otherwise
 *
 * @see tp_SetWriteID3v2_3()
 */
int tp_GetWriteID3v2_3(tunepimp_t o);

/**
 * Use this function to set which encoding to write to ID3v2 tags.
 *
 * Default: utf-8 for ID3v2.4, ISO 8859-1 (latin1) for ID3v2.3
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param encoding set to one of eLatin1, eUTF8 or eUTF16
 *
 * @see tp_GetWriteID3v2_3(), tp_WriteTags()
 */
void      tp_SetID3Encoding           (tunepimp_t o, TPID3Encoding encoding);


/**
 * Check which encoding is set for writing ID3v2 tags.
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @returns one of eLatin1, eUTF8 or eUTF16
 *
 * @see tp_SetID3Encoding()
 */
TPID3Encoding tp_GetID3Encoding(tunepimp_t o);

/**
 * Use this function to enable/disable the clearning of metadata
 * tags before the MusicBrainz data is written to the tag. If the metadata
 * tags have crufty data in them and you want to clean them completely
 * before writing new data to the tag, then enable this option.
 *
 * Default: false
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param clearTags set a non-zero value to enable tag clearing
 *
 * @see tp_GetClearTags(), tp_WriteTags()
 */
void      tp_SetClearTags            (tunepimp_t o, int clearTags);


/**
 * Query the tunepimp object if tag clearing is enabled. See tp_SetClearTags()
 * for more information.
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @returns true if the tag clearing is enabled and false otherwise
 *
 * @see tp_SetClearTags()
 */
int tp_GetClearTags(tunepimp_t o);


/**
 * Set the file mask. The file mask is a format string roughly similar to
 * the one used in printf(3). Whenever a filename has to be created, the
 * escape sequences embedded in the file mask are expanded with meta data
 * from the musicbrainz database.
 * 
 * The following escape sequences are supported:
 *
 *	- %artist (Name of the artist)
 *	- %abc (The first character of the artist's sortname)
 *	- %abc2 (The first two character of the artist's sortname)
 *	- %abc3 (The first three character of the artist's sortname)
 *	- %sortname (Sortname of the artist)
 *	- %track (Title of the song)
 *	- %album (Title of the album)
 *	- %num (Track number on the album)
 *	- %0num (Track number on the album, zero padded to two places)
 *	- %format (The format of the given file e.g. ogg/mp3/wav/flac/ape)
 *	- %type (The release type: single, album, remix, etc)
 *	- %status (The release status: official, bootleg, promo)
 *	- %year (The first release year)
 *	- %month (The first release month)
 *	- %day (The first release day)
 *	- %country (The first release country)
 *
 *
 * Please note that you have to use tp_SetVariousFileMask() to set the
 * file mask for tracks from various artists releases.
 *
 * The default file mask is "%artist/%album/%artist-%album-%0num-%track".
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param fileMask a format string
 *
 * @see tp_GetFileMask(), tp_SetVariousFileMask(), tp_SetDestDir(),
 *      tp_SetNonAlbumFileMask()
 */
void      tp_SetFileMask             (tunepimp_t o, const char *fileMask);


/**
 * Use this function to get a string containing the file mask.
 * tp_GetFileMask() stores the string in a user supplied buffer. Not more than
 * maxLen characters including the trailing '\\0' byte are copied into that
 * buffer.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param fileMask a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 *
 * @see tp_SetFileMask()
 */
void tp_GetFileMask (tunepimp_t o, char *fileMask, int maxLen);


/**
 *
 * Set the file mask for various artists releases. See tp_SetFileMask()
 * for a discussion of file masks.
 *
 * For single artist releases, tp_SetFileMask() has to be used.
 *
 * The default is "Various Artists/%album/%album-%0num-%artist-%track".
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param variousFileMask a format string
 *
 * @see tp_SetFileMask(), tp_SetDestDir(), tp_SetNonAlbumFileMask()
 *
 */
void      tp_SetVariousFileMask     (tunepimp_t o, const char *variousFileMask);


/**
 * Use this function to get a string containing the various artists file mask.
 * tp_GetVariousFileMask() stores the string in a user supplied buffer. Not
 * more than maxLen characters including the trailing '\\0' byte are copied
 * into that buffer.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param variousFileMask a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 *
 * @see tp_SetVariousFileMask()
 */
void tp_GetVariousFileMask (tunepimp_t o, char *variousFileMask, int maxLen);


/**
 *
 * Set the file mask for non-album releases. See tp_SetFileMask()
 * for a discussion of file masks.
 *
 * For regular album releases, tp_SetFileMask() or tp_SetVariousFileMask()
 * has to be used.
 *
 * The default file mask is "%artist/%album/%artist-%track".
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param nonAlbumFileMask a format string
 *
 * @see tp_SetFileMask(), tp_SetDestDir(), tp_SetVariousMask()
 *
 */
void      tp_SetNonAlbumFileMask     (tunepimp_t o, const char *nonAlbumFileMask);


/**
 * Use this function to get a string containing the various artists file mask.
 * tp_GetVariousFileMask() stores the string in a user supplied buffer. Not
 * more than maxLen characters including the trailing '\\0' byte are copied
 * into that buffer.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param nonAlbumFileMask a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 *
 * @see tp_SetNonAlbumFileMask()
 */
void tp_GetNonAlbumFileMask (tunepimp_t o, char *nonAlbumFileMask, int maxLen);


/**
 * Use this function to set a white list of characters that are permitted in
 * a filename.
 *
 * If you set allowedFileCharacters to the empty string, all characters
 * permitted by the underlying file system are regarded as allowed. All
 * other characters are removed from filenames written by tunepimp.
 * Please note, however, that the directory separator ("/" on Unix) is
 * always permitted.
 *
 * The default is the empty string ("").
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param allowedFileCharacters the list of allowed characters
 *
 * @see tp_GetAllowedFileCharacters(), tp_SetFileMask(), tp_SetVariousFileMask(),
 *      tp_SetNonAlbumFileMask()
 */
void tp_SetAllowedFileCharacters(tunepimp_t o, const char *allowedFileCharacters);


/**
 * Use this function to get a string containing the characters allowed
 * in a file name. This function stores the string in a user supplied buffer.
 * Not more than maxLen characters including the trailing '\\0' byte are copied
 * into that buffer.
 *
 * If all characters are allowed, the empty string ("") is returned.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param allowedFileCharacters a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 *
 * @see tp_SetAllowedFileCharacters()
 */
void tp_GetAllowedFileCharacters(tunepimp_t o, char *allowedFileCharacters, int maxLen);


/**
 * This function sets a base directory that is prepended to all files
 * written by tunepimp if the move feature is enabled. The base directory
 * may be absolute or relative. No trailing directory separator ("/" or "\")
 * is required.
 *
 * Default: "MyMusic" in the current working directory.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param destDir a directory name
 *
 * @see tp_GetDestDir(), tp_SetFileMask(), tp_SetVariousFileMask(),
 *      tp_SetFileMove(), tp_SetNonAlbumMask()
 */
void      tp_SetDestDir              (tunepimp_t o, const char *destDir);


/**
 * Use this function to get a string containing the destination directory.
 * tp_GetDestDir() stores the string in a user supplied buffer. Not more than
 * maxLen characters including the trailing '\\0' byte are copied into that
 * buffer.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param destDir a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 *
 * @see tp_SetDestDir()
 *
 */
void tp_GetDestDir(tunepimp_t o, char *destDir, int maxLen);


/**
 * When TunePimp moves a file out of a directory to a new directory,
 * and the old directory is now empty, the old directory is removed.
 * This process is repeated for the old directory's parent, until
 * it reaches the TopSrcDir, where it stops removing directories.
 * Set the TopDrcDir to root of the directory tree where Tunepimp
 * is writing ID3 files to.
 *
 * Example:
 *
 *    TopSrcDir in this case is set to: /mnt/mp3
 *
 *        /mnt/mp3/dirty_mp3s/Beatles/Yesterday.mp3
 *
 *    The Yesterday song is the only file left in the dirty_mp3s
 *    folder. When tunepimp moves this file to its new, clean
 *    location, it will remove the Beatles directory, then the
 *    dirty_mp3s directory, but it will not remove the /mnt/mp3
 *    directory, since that is the TopSrcDir.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param topSrcDir the top src directory to use
 *
 * @see tp_GetTopSrcDir()
 */
void      tp_SetTopSrcDir            (tunepimp_t o, const char *topSrcDir);


/**
 * Use this function to get the top source directory. See tp_SetTopSrcDir()
 * for more information.
 *
 * tp_GetTopSrcDir() stores the string in a user supplied buffer. Not more
 * than maxLen characters including the trailing '\\0' byte are copied into
 * that buffer.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param topSrcDir a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 *
 * @see tp_SetTopSrcDir()
 */
void tp_GetTopSrcDir(tunepimp_t o, char *topSrcDir, int maxLen);


/**
 * Use this function to set the auto save threshold.
 *
 * When the similarity value (see tp_SetPUIDCollision()) is greater or
 * equal the auto save threshold, a recognized file (in state
 * eRecognized) is marked as verified (eVerified). The effect is
 * the same as calling tp_WriteTags() on a recognized file.
 *
 * The writing is done immediately, without the possibility of user
 * intervention.
 *
 * Valid values for the threshold are between 0 and 100, including 0 and 100.
 * Set it to a negative value to disable the auto save feature.
 *
 * Default: 90.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param autoSaveThreshold the auto save threshold
 *
 * @see tp_SetPUIDCollisionThreshold(), tp_WriteTags(), tp_GetAutoSaveThreshold()
 */
void      tp_SetAutoSaveThreshold    (tunepimp_t o, int autoSaveThreshold);


/**
 * Get the autosave threshold if autosave is enabled or a negative value if the feature
 * is disabled. See tp_SetAutoSaveThreshold() for an explanation of the
 * autosave feature.
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @returns the autosave threshold or a negative number of disabled
 *
 * @see tp_SetAutoSaveThreshold()
 */
int tp_GetAutoSaveThreshold(tunepimp_t o);

/**
 * Use this function to set the maximum filename length
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param maxFileNameLen the maximum filename length
 *
 * @see tp_GetMaxFileNameLen
 */
void tp_SetMaxFileNameLen(tunepimp_t o, int maxFileNameLen);


/**
 * Use this function to get the current maximum filename length
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @returns the current maximum filename length
 *
 * @see tp_SetMaxFileNameLen()
 */
int tp_GetMaxFileNameLen(tunepimp_t o);

/**
 * Use this function to control if the tunepimp library automatically
 * deletes files after they've been saved or if they should be moved
 * to the eSaved status.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param autoRemoveSavedFiles automatically remove the files (true/false)
 *
 * @see tp_GetAutoRemovedSavedFiles
 */
void tp_SetAutoRemovedSavedFiles(tunepimp_t o, int autoRemoveSavedFiles);


/**
 * Use this function to determine if the tunepimp library automatically
 * deletes files after they've been saved or if it moves them  
 * to the eSaved status.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @returns if tunepimp is auto removing files
 *
 * @see tp_SetAutoRemovedSavedFiles()
 */
int tp_GetAutoRemovedSavedFiles(tunepimp_t o);


/**
 * Get a list of recognized files (eRecognized) that have a similarity value
 * of less than threshold. If such files were found, the function allocates
 * an array of ints and returns it using the fileIds argument.
 * The number of entries in the array can be found in the numIds argument.
 *
 * Don't forget to free the allocated memory using
 * tp_DeleteRecognizedFileList().
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param threshold a threshold (between 0 and 100)
 * @param fileIds the address of an int pointer
 * @param numIds the address of a variable to receive the number of IDs returned
 *
 * @returns true if there were matching files and false otherwise
 *
 * @see tp_DeleteRecognizedFileList()
 */
int tp_GetRecognizedFileList(tunepimp_t o, int threshold, int **fileIds, int *numIds);


/**
 * Release the memory allocated by tp_GetRecognizedFileList(). You can use
 * this function even if there were no fileIds returned.
 *
 * @param o the tunepimp_t object returned from tp_New()
 * @param fileIds the array returned by tp_GetRecognizedFileList()
 *
 * @see tp_GetRecognizedFileList()
 */
void tp_DeleteRecognizedFileList(tunepimp_t o, int *fileIds);

int tp_GetWinSafeFileNames(tunepimp_t o);
void tp_SetWinSafeFileNames(tunepimp_t o, int winSafeFileNames);

#ifdef WIN32
/**
 * WINDOWS ONLY: This function must be called to initialize the WinSock
 * TCP/IP stack in windows. If your application does not utilize any
 * WinSock functions, you must call this function before you can call
 * tp_Query(). Before your application shuts down, you must call tp_WSAStop().
 * If you already call WSAInit from your own application,
 * you do not need to call this function.
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @see tp_WSAStop.
 */
void      tp_WSAInit           (tunepimp_t o);


/**
 * WINDOWS ONLY: Call this function when your application shuts down. Only
 * call this function if you called tp_WSAInit().
 *
 * @param o the tunepimp_t object returned from tp_New()
 *
 * @see tp_WSAInit
 */
void      tp_WSAStop           (tunepimp_t o);
#endif 


/* --------------------------------------------------------------------------
 * Track Interface
 * --------------------------------------------------------------------------*/

/**
 * Returns the status of a track.
 *
 * It is also possible to get notifed as soon as the status of a track changes
 * using the notfy callback.
 *
 * @param t a track object obtained via tp_GetTrack()
 * @returns the status of the track
 *
 * @see tp_SetNotifyCallback(), tp_GetTrack()
 */
TPFileStatus tr_GetStatus      (track_t t);


/**
 * Set a track's status. Setting the status is necessary if a track is in
 * state ePUIDCollision, eUserSelection or eUnrecognized. Don't forget
 * to lock the track before using this function and unlocking it
 * afterwards.
 *
 * @param t a track object obtained via tp_GetTrack()
 * @param status the new status of the track
 * 
 * @see tr_Lock(), tr_Unlock()
 */
void       tr_SetStatus        (track_t t, const TPFileStatus status);


/**
 * Get the filename of the specified track. The function stores the
 * filename in a user supplied buffer. Not more than maxLen characters
 * including the trailing '\\0' byte are copied into that buffer.
 *
 * @param t a track object obtained via tp_GetTrack()
 * @param fileName a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 */
void       tr_GetFileName      (track_t t, char *fileName, int maxLen);


/**
 * Get the PUID of the specified track in an ASCII representation. The
 * PUID is stored in a user supplied buffer. Not more than maxLen characters
 * including the trailing '\\0' byte are copied into that buffer.
 *
 * A PUID is MB_ID_LEN=36 characters long, so you can set maxLen to 37.
 *
 * @param t a track object obtained via tp_GetTrack()
 * @param puid a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 */
void       tr_GetPUID           (track_t t, char *puid, int maxLen);


/**
 * Get the track's meta data that was already present in the file. The
 * meta data is saved in a valid metadata_t object passed as an argument.
 * No I/O takes place since the data will have been read during the 
 * PUID analisys stage. Files that are still in the ePending stage 
 * may not have correct local metadata.
 *
 * @param t a track object obtained via tp_GetTrack()
 * @param mdata a meta data object created by md_New()
 *
 * @see tr_SetLocalMetadata(), tr_GetServerData(), tp_GetTrack(), md_New()
 */
void       tr_GetLocalMetadata (track_t t, metadata_t *mdata);


/**
 * Set the track's local meta data to the specified values. No I/O takes
 * place.
 *
 * To avoid race conditions, you have to tr_Lock() the track before
 * using tr_SetLocalMetadata() and tr_Unlock() afterwards.
 *
 * @param t a track object obtained via tp_GetTrack()
 * @param mdata a valid metadata_t object
 *
 * @see tr_GetLocalMetadata(), tr_SetServerData(), tp_GetTrack(), md_New()
 */
void       tr_SetLocalMetadata (track_t t, const metadata_t *mdata);


/**
 * Retrieve the meta data we got back from the server. This data will have
 * been downloaded from the server if a track was recognized.
 *
 * The server meta data is used to construct file and directory names and
 * is written to the tags as soon as the data is verified (eVerified).
 *
 * @param t a track object obtained via tp_GetTrack()
 * @param mdata a valid metadata_t object
 *
 * @see tr_SetServerMetadata(), tr_GetLocalMetadata(), tp_GetTrack(), md_New()
 */
void       tr_GetServerMetadata(track_t t, metadata_t *mdata);


/**
 * Set the server meta data. It is used to write the tag and to construct
 * new file and directory names as soon as the data is verifed (eVerified).
 *
 * @param t a track object obtained via tp_GetTrack()
 * @param mdata a valid metadata_t object
 *
 * @see tr_GetServerMetadata(), tr_SetLocalMetadata(), tp_GetTrack(), md_New()
 */
void       tr_SetServerMetadata(track_t t, const metadata_t *mdata);


/**
 * Use this function to get a printable error message for the last
 * error that occured in the track object. tr_GetError() stores the
 * error string in a user supplied buffer. Not more than maxLen characters
 * including the trailing '\\0' byte are copied into that buffer.
 *
 * Don't confuse this function with tp_GetError().
 *
 * @param t a track object obtained via tp_GetTrack()
 * @param error a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 *
 * @see tp_GetError()
 */
void       tr_GetError         (track_t t, char *error, int maxLen);


/**
 * Get the similarity of the local and the server meta data. 
 *
 * The similarity is a percent value between 0 and 100. Before a lookup,
 * the similarity is 0. If no metadata was extracted from the file, 
 * the similarity will also be 0.
 *
 * @param t a track object obtained via tp_GetTrack()
 *
 * @returns a similarity value
 */
int        tr_GetSimilarity    (track_t t);


/**
 * Returns true if local and server meta data differ and false
 * otherwise.
 *
 * @param t a track object obtained via tp_GetTrack()
 *
 * @returns true if local and server meta data differ and false otherwise
 */
int        tr_HasChanged       (track_t t);

/**
 * Mark a track as changed, so that it will be saved even if libtp
 * doesn't think the track changed. (Useful for cases where the encoding
 * changed, which libtp doesn't detect.
 *
 * @param t a track object obtained via tp_GetTrack()
 */
void       tr_SetChanged       (track_t t);

/**
 * Lock a track object to make sure tunepimp doesn't change it while you are
 * working on it. Tunepimp is multithreaded so it is needed to avoid
 * race conditions. Don't forget to release the lock using tr_Unlock()
 * when you're done.
 *
 * @param t a track object obtained via tp_GetTrack()
 *
 * @see tr_Unlock()
 */
void       tr_Lock             (track_t t);


/**
 * Unlock a track object previously locked using tr_Lock(). You are
 * not allowed to unlock tracks that were locked by tunepimp itself.
 *
 * @param t a track object obtained via tp_GetTrack()
 *
 * @see tr_Lock()
 */
void       tr_Unlock           (track_t t);


/* --------------------------------------------------------------------------
 * Metadata Interface
 * --------------------------------------------------------------------------*/


/**
 * Create a new metadata_t object.
 *
 * Don't forget to release it using md_Delete() when you don't need it any
 * longer.
 *
 * @returns a new metadata_t object
 *
 * @see md_Clear()
 */
metadata_t   *md_New                   (void);


/**
 * Delete a metadata_t object.
 *
 * @param mdata a valid metadata_t object
 *
 * @see md_Clear()
 */
void          md_Delete                (metadata_t *mdata);


/**
 * Clears a metadata_t object.
 *
 * All values of the object are set to NULL values. After that the object
 * is in the same state as directly after md_New().
 *
 * @param mdata a valid metadata_t object
 *
 * @see md_New(), md_Delete()
 */
void          md_Clear                 (metadata_t *mdata);

/**
 * Compare two metadata_t objects and return a similarity value between 
 * 0.0 and 1.0, where zero is totally dissimilar and 1.0 is exactly the same.
 *
 * @param mdataA a valid metadata_t object
 * @param mdataB a valid metadata_t object
 *
 */
int          md_Compare                (const metadata_t *mdataA, const metadata_t *mdataB);

/**
 * Converts a string to TPAlbumStatus. The string's value has to be one of
 * "official", "promotion" or "bootleg". Case doesn't matter.
 *
 * @param albumStatus the string to convert
 * @returns an album status or eAlbumStatus_Error on error
 *
 * @see md_ConvertToAlbumType()
 */
TPAlbumStatus md_ConvertToAlbumStatus  (const char *albumStatus);


/**
 * Converts a string to TPAlbumType. The string's value has to be one of
 * "album", "single", "compilation", "soundtrack", "spokenword", "audiobook",
 * "live" or "other". Case doesn't matter.
 *
 * @param albumType the string to convert
 * @returns an album type or eAlbumType_Error on error
 *
 * @see md_ConvertToAlbumStatus()
 */
TPAlbumType   md_ConvertToAlbumType    (const char *albumType);


/**
 * Convert the status of an album to its textual representation.
 * The function stores the status string in a user supplied buffer. Not more
 * than maxLen characters including the trailing '\\0' byte are copied into
 * that buffer.
 *
 * @param status an album status
 * @param albumStatus a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 *
 * @see md_ConvertToAlbumStatus()
 */
void          md_ConvertFromAlbumStatus(TPAlbumStatus status, char *albumStatus, int maxLen);


/**
 * Convert the type of an album to its textual representation.
 * The function stores the type string in a user supplied buffer. Not more
 * than maxLen characters including the trailing '\\0' byte are copied into
 * that buffer.
 *
 * @param type an album type
 * @param albumType a user supplied buffer of maxLen characters
 * @param maxLen the size of the buffer
 *
 * @see md_ConvertToAlbumType()
 */
void          md_ConvertFromAlbumType  (TPAlbumType type, char *albumType, int maxLen);



/* --------------------------------------------------------------------------
 * String Interface
 * --------------------------------------------------------------------------*/

/**
 * Does a fuzzy string comparison and returns the similarity value 
 * between 0.0 and 1.0
 *
 * @param a the first string
 * @param b the second string
 * @returns a float value from 0.0 (completely dissimilar strings) to
 *            1.0 (the exact same strings)
 */
float md_Similarity(const char *a, const char *b);

#ifdef __cplusplus
}
#endif

#endif 
