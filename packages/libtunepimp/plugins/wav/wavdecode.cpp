/*----------------------------------------------------------------------------

   libtunepimp -- The MusicBrainz tagging library.  
                  Let a thousand taggers bloom!
   
   Copyright (C) Robert Kaye 2003
   Portions (C) 2001 "John Cantrill" <thejohncantrill@hotmail.com>
   
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

   $Id: wavdecode.cpp 7954 2006-06-27 22:00:45Z luks $

----------------------------------------------------------------------------*/
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include <errno.h>
#ifdef WIN32
#include <windows.h>
#endif

#include "wavdecode.h"

#ifndef WIN32
#define WAVE_FORMAT_PCM 1
typedef unsigned int DWORD;
typedef unsigned char BYTE;
#define MAKEFOURCC(ch0,ch1,ch2,ch3) ((DWORD)(BYTE)(ch0) | ((DWORD)(BYTE)(ch1) << 8) | ((DWORD)(BYTE)(ch2) << 16) | ((DWORD)(BYTE)(ch3) << 24 ))
struct WAVEFORMAT
{
   unsigned short     wFormatTag;
   unsigned short     nChannels;
   DWORD              nSamplesPerSec;
   DWORD              nAvgBytesPerSec;
   unsigned short     nBlockAlign;
};
#endif

#ifdef WIN32
    typedef __int64   mb_int64_t;
#else				            
    typedef long long mb_int64_t;
#endif

/*-------------------------------------------------------------------------*/

const int BUFFER_LEN = 4096;

WavDecode::WavDecode(const string &fileName, const string &encoding) : DecodePlugin()
{
    unsigned char  buffer[100];
    unsigned long  ulRIFF;
    unsigned long  ulLength;
    unsigned long  ulWAVE;
    unsigned long  ulType;
    unsigned long  ulCount;
    unsigned long  ulLimit;
    bool           haveWaveHeader = false;
    unsigned long  waveSize = 0;
    WAVEFORMAT     waveFormat;
    mb_int64_t     fileLen = 0;

    this->encoding = encoding;

    file = topen(fileName.c_str(), "rb", encoding.c_str());
    if (file == NULL)
    {
       errorString = string("File not found");
       tclose(file);
       file = NULL;
       return;
    }

    tseek(file, 0, SEEK_END);
    fileLen = ttell(file);
    tseek(file, 0, SEEK_SET);

    if (tread(buffer, 1, 12, file) != 12)
    {
       errorString = string("File is too short");
       tclose(file);
       file = NULL;
       return;
    }

    ulRIFF = (unsigned long)(((unsigned long *)buffer)[0]);
    ulLength = (unsigned long)(((unsigned long *)buffer)[1]);
    ulWAVE = (unsigned long)(((unsigned long *)buffer)[2]);

    if(ulRIFF != MAKEFOURCC('R', 'I', 'F', 'F') ||
       ulWAVE != MAKEFOURCC('W', 'A', 'V', 'E'))
    {
       errorString = strdup("File is not in WAVE format");
       tclose(file);
       file = NULL;
       return;
    }

    // Run through the bytes looking for the tags
    ulCount = 0;
    ulLimit = ulLength - 4;
    while (ulCount < ulLimit && waveSize == 0)
    {
       if (tread(buffer, 1, 8, file) != 8)
       {
          errorString = strdup("File is too short");
          tclose(file);
          file = NULL;
          return;
       }

       ulType   = (unsigned long)(((unsigned long *)buffer)[0]);
       ulLength = (unsigned long)(((unsigned long *)buffer)[1]);
       switch (ulType)
       {
          // format
          case MAKEFOURCC('f', 'm', 't', ' '):
             if (ulLength < sizeof(WAVEFORMAT))
             {
                errorString = strdup("File is too short");
                tclose(file);
                file = NULL;
                return;
             }

             if (tread(&waveFormat, 1, ulLength, file) != ulLength)
             {
                errorString = strdup("File is too short");
                tclose(file);
                file = NULL;
                return;
             }

             if (waveFormat.wFormatTag != WAVE_FORMAT_PCM)
             {
                errorString = strdup("Unsupported WAV format");
                tclose(file);
                file = NULL;
                return;
             }
             haveWaveHeader = true;

             ulCount += ulLength;
             break;

          // data
          case MAKEFOURCC('d', 'a', 't', 'a'):
             waveSize = ulLength;
             break;

          default:
             tseek(file, ulLength, SEEK_CUR);
             break;

       }
    }

    if (!haveWaveHeader)
    {
       errorString = strdup("Could not find WAV header");
       tclose(file);
       file = NULL;
       return;
    }

    samplesPerSecond = waveFormat.nSamplesPerSec;
    channels = waveFormat.nChannels;
    bitsPerSample = (waveFormat.nBlockAlign / waveFormat.nChannels) * 8;

    fileLen -= (mb_int64_t)ttell(file);
    fileLen /= waveFormat.nChannels;
    fileLen /= (waveFormat.nBlockAlign / waveFormat.nChannels);

    duration = (unsigned long)((fileLen * 1000) / waveFormat.nSamplesPerSec);
}

WavDecode::~WavDecode(void)
{
    if (file)
        tclose(file);
}

int WavDecode::getInfo(unsigned long &duration,
                       unsigned int &samplesPerSecond,
                       unsigned int &bitsPerSample,
                       unsigned int &channels)
{
    if (!file)
        return 0;

    duration = this->duration;
    samplesPerSecond = this->samplesPerSecond;
    bitsPerSample = this->bitsPerSample;
    channels = this->channels;

    return 1;
}

int WavDecode::read(char *data, int maxBytes)
{
    if (!file)
        return -1;

    return tread(data, sizeof(char), maxBytes, file);
} 
