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

   $Id: puid.c 7959 2006-06-29 00:48:30Z luks $

----------------------------------------------------------------------------*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif
#include <musicbrainz/browser.h>
#include <tunepimp-0.5/tp_c.h>
#include "../config.h"

char *EscapeFormValue(const char *form_value)
{
    int i, form_value_length, extra_length;
    char *escaped_value, *ptr;

    form_value_length = strlen(form_value);
    for (i = 0, extra_length = 0; i < form_value_length; ++i)
    {
        switch(form_value[i])
        {
            case '"':
                extra_length += 5;
                break;
            case '&':
                extra_length += 4;
                break;
            case '<':
            case '>':
                extra_length += 3;
                break;
        }
    }

    if (extra_length == 0)
    {
        // This is necessary since the caller must free the memory.
        return strdup(form_value);
    }

    escaped_value = (char *)malloc(form_value_length + extra_length + 1);
    for (i = 0, ptr = escaped_value; i < form_value_length; ++i)
    {
        switch(form_value[i])
        {
            case '"':
                strcpy(ptr, "&quot;");
                ptr += 6;
                break;
            case '&':
                strcpy(ptr, "&amp;");
                ptr += 5;
                break;
            case '<':
                strcpy(ptr, "&lt;");
                ptr += 4;
                break;
            case '>':
                strcpy(ptr, "&gt;");
                ptr += 4;
                break;
            default:
                *(ptr++) = form_value[i];
        }
    }
    *ptr = 0;

    return escaped_value;
}

int CreateLookupPage(const char *outFile, track_t *track, metadata_t *data, const char *server)
{
    FILE *out;
    char *temp, srcFile[1024], puid[255];

    tr_GetFileName(track, srcFile, 1024);
    tr_GetPUID(track, puid, 255);

    out = fopen(outFile, "wt");
    if (!out)
        return 0;

    fprintf(out,
            "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">\n"
            "<HTML><HEAD><TITLE>MusicBrainz Lookup</TITLE></HEAD>\n"
            "<BODY onLoad=\"document.forms[0].submit()\">\n"
            "<center>\n"
            "<h3>MusicBrainz Loookup</h3><p>\n"
            "Looking up file at MusicBrainz.\n"
            "<FORM METHOD=\"POST\"\n"
            "      ACTION=\"http://%s/taglookup.html\"\n"
            "      ENCTYPE=\"application/x-www-form-urlencoded\" "
            "      class=\"formstyle\">\n", server);

    temp = EscapeFormValue(data->artist);
    fprintf(out, 
            "  <INPUT TYPE=\"hidden\" NAME=\"artist\" VALUE=\"%s\">\n",
            temp);
    free(temp);

    temp = EscapeFormValue(data->album);
    fprintf(out, 
            "  <INPUT TYPE=\"hidden\" NAME=\"album\" VALUE=\"%s\">\n",
            temp);
    free(temp);

    temp = EscapeFormValue(data->track);
    fprintf(out, 
            "  <INPUT TYPE=\"hidden\" NAME=\"track\" VALUE=\"%s\">\n",
            temp);
    free(temp);

    temp = EscapeFormValue(data->trackId);
    fprintf(out, 
            "  <INPUT TYPE=\"hidden\" NAME=\"trackid\" VALUE=\"%s\">\n",
            temp);
    free(temp);

    temp = EscapeFormValue(srcFile);
    fprintf(out, 
            "  <INPUT TYPE=\"hidden\" NAME=\"filename\" VALUE=\"%s\">\n",
            temp);
    free(temp);

    temp = EscapeFormValue(puid);
    fprintf(out, 
            "  <INPUT TYPE=\"hidden\" NAME=\"puid\" VALUE=\"%s\">\n",
            temp);
    free(temp);

    fprintf(out, 
            "  <INPUT TYPE=\"hidden\" NAME=\"duration\" VALUE=\"%lu\">\n"
            "  <INPUT TYPE=\"hidden\" NAME=\"tracknum\" VALUE=\"%d\">\n"
            "</form>\n"
            "</center>\n"
            "</body>\n"
            "</html>\n", data->duration, data->trackNum);

    fclose(out);


    return 1;
}

void LookupMetadata(track_t track, const char *fileName)
{
    metadata_t *data;
    char       *server;
    char       *outFile = "/tmp/lookup.html";
    char       *url = "file:///tmp/lookup.html";

    if (getenv("MB_SERVER"))
        server = getenv("MB_SERVER");
    else
        server = "musicbrainz.org";

    data = md_New();
    tr_GetLocalMetadata(track, data);
    CreateLookupPage(outFile, track, data, server);
    md_Delete(data);

    LaunchBrowser(url, "mozilla");
}

void PrintMetadata(track_t *track)
{
    metadata_t *data;
    char        puid[255];
   
    data = md_New();
    tr_GetPUID(track, puid, 255);
    tr_GetLocalMetadata(track, data);
    printf("  Artist: '%s'\n", data->artist);
    printf("   Album: '%s'\n", data->album);
    printf("   Track: '%s'\n", data->track);
    printf("TrackNum: '%d'\n", data->trackNum);
    printf("Duration: '%lu'\n", data->duration);
    printf("     PUID: %s\n", puid);
    md_Delete(data);
}

int main(int argc, char *argv[])
{
    int            index = 1, isLookup = 0, printID3 = 0;
    tunepimp_t     pimp;
    track_t        track;
    int            done, fileId, i;
    TPCallbackEnum type;
    TPFileStatus   status;
    char           puid[255], clientId[128];
    int            analyzed = 0;
#ifdef WIN32
    WSADATA        sGawdIHateMicrosoft;
#endif

    if (argc < 2)
    {
        int        num;
        char       ext[10][32];

        fprintf(stderr,"usage: puid [-i|-l] <musicDNS clientId> <audio file>\n");
        fprintf(stderr,"Options:\n");
        fprintf(stderr,"  -i   Print out track metadata along with puid id\n");
        fprintf(stderr,"  -l   Lookup file at MusicBrainz\n\n");
        fprintf(stderr,"To obtain a MusicDNS client id, go to http://musicdns.org\n\n");
        fprintf(stderr, "BROWSER environment variable to specify your browser of choice.\n");
        fprintf(stderr, "Check http://www.catb.org/~esr/BROWSER/index.html for details.\n\n");

        pimp = tp_NewWithArgs("puid", VERSION, TP_THREAD_NONE, NULL);

        printf("Supported file extensions: ");
        num = tp_GetNumSupportedExtensions(pimp);
        tp_GetSupportedExtensions(pimp, ext);
        for(i = 0; i < num; i++)
            printf("%s ", ext[i]);
        printf("\n");

        tp_Delete(pimp);

        return -1;
    }

#ifdef WIN32
    WSAStartup(0x0002, &sGawdIHateMicrosoft);
#endif

    for(; index < argc; index++)
    {
        if (strcmp(argv[index], "-l") == 0)
           isLookup = 1;
        else
        if (strcmp(argv[index], "-i") == 0)
           printID3 = 1;
        else
           break;
    }

    if (index >= argc)
    {
        fprintf(stderr, "error: no clientid specified.\n");
        exit(-1);
    }
    strcpy(clientId, argv[index++]);
    if (strlen(clientId) == 0)
    {
        fprintf(stderr, "Invalid MusicDNS client id specified.\n");
        return (-1);
    }
    if (index >= argc)
    {
        fprintf(stderr, "error: no lookup file specified.\n");
        exit(-1);
    }
    if (access(argv[index], 0))
    {
        fprintf(stderr, "Cannot open file %s\n", argv[index]);
        return (-1);
    }

    pimp = tp_NewWithArgs("puid", VERSION, TP_THREAD_ANALYZER | TP_THREAD_READ, NULL);
    tp_SetMusicDNSClientId(pimp, clientId);
    tp_AddFile(pimp, argv[index], 0);

    for(done = 0;!done;)
    {
        while(tp_GetNotification(pimp, &type, &fileId, &status) && !done)
        {
            if (type != tpFileChanged)
                continue;

            track = tp_GetTrack(pimp, 0);
            tr_Lock(track);
            switch(tr_GetStatus(track))
            {
                case ePUIDLookup:
                {
                    if (printID3)
                        PrintMetadata(track);
                    else
                    if (isLookup)
                        LookupMetadata(track, argv[index]);
                    else
                    {
                        tr_GetPUID(track, puid, 255);
                        printf("%s\n", puid);
                    }

                    done = 1;
                    break;
                }
                case eUnrecognized:
                    if (!analyzed)
                    {
                        puid[0] = 0;
                        tr_GetPUID(track, puid, 255);
                        if (puid[0] == 0)
                        {
                            tr_SetStatus(track, ePending);
                            tp_Wake(pimp, track);
                            analyzed = 1;
                        }
                        break;
                    }
                    printf("No PUID available for this track.\n");
                    done = 1;
                    break;
                    
                case eRecognized:
                    puid[0] = 0;
                    tr_GetPUID(track, puid, 255);
                    if (puid[0])
                        fprintf(stderr, "PUID id read from file: %s\n", puid);

                    tp_IdentifyAgain(pimp, 0);
                    break;
                case ePending:
                    break;
                case eError:
                {
                    char err[255];
                    tr_GetError(track, err, 255);
                    fprintf(stderr, "Error: %s\n", err);
                    done = 1;
                    break;
                }
                default:
                    fprintf(stderr, "Warning: Unsupported case: %d\n", tr_GetStatus(track));
                    done = 1;
                    break;
            }
            tr_Unlock(track);
            tp_ReleaseTrack(pimp, track);

#ifdef WIN32
            Sleep(50);
#else
            usleep(50000);
#endif
        }
    }

    tp_Delete(pimp);

#ifdef WIN32
    WSACleanup();
#endif

    return 0;
}
