/* (PD) 2001 The Bitzi Corporation
 * Please see file COPYING or http://bitzi.com/publicdomain 
 * for more info.
 *
 * $Id: mp3info.h 1419 2005-07-10 21:54:05Z robert $
 */
#ifndef MP3_INFO_H
#define MP3_INFO_H

#include <string>
using namespace std;
#include "fileio.h"

class TPMP3Info
{
    public:

        TPMP3Info(void) {};
       ~TPMP3Info(void) {};

         bool analyze(const string &fileName, const string &encoding);

         int  getBitrate(void) { return m_bitrate; };
         int  getSamplerate(void) { return m_samplerate; };
         int  getStereo(void) { return m_stereo; };
         int  getDuration(void) { return m_duration; };
         int  getFrames(void) { return m_frames; };
         int  getMpegVer(void) { return m_mpegver; };
         int  getAvgBitrate(void) { return m_avgbitrate; };

    private:

         int   findStart(TFILE *fp, unsigned offset);
         bool  scanFile(TFILE *fp);

         int   framesync(const unsigned char *header);
         int   padding(const unsigned char *header);
         int   mpeg_layer(const unsigned char *header);
         int   mpeg_ver(const unsigned char *header);
         int   stereo(const unsigned char *header);
         int   samplerate(const unsigned char *header);
         int   bitrate(const unsigned char *header);

         bool  isFrame(unsigned char *ptr, int &layer, int &sampleRate, 
                       int &mpegVer, int &bitRate, int &frameSize);

         int   m_goodBytes, m_badBytes;
         int   m_bitrate, m_samplerate, m_stereo, m_duration, 
               m_frames, m_mpegver, m_avgbitrate;
};

#define MP3_HEADER_SIZE 4

#endif
