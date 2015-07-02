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

   $Id: flacdecode.cpp 8625 2006-11-05 22:13:17Z luks $

----------------------------------------------------------------------------*/
#include <stdlib.h>
#include <string.h>
#include "flacdecode.h"

#include <FLAC/export.h>
/* FLAC 1.1.3 has FLAC_API_VERSION_CURRENT == 8 */
#if !defined(FLAC_API_VERSION_CURRENT) || FLAC_API_VERSION_CURRENT < 8
#define LEGACY_FLAC
#else
#undef LEGACY_FLAC
#endif

void FLAC_errorcb(const FLAC__StreamDecoder * decoder,
                  FLAC__StreamDecoderErrorStatus status, void *client_data)
{
}

void FLAC_metadatacb(const FLAC__StreamDecoder * decoder,
                     const FLAC__StreamMetadata * metadata, void *client_data)
{
   if (metadata->type != FLAC__METADATA_TYPE_STREAMINFO)
      return;

   clientdata_t *cd = reinterpret_cast < clientdata_t * >(client_data);

   const FLAC__StreamMetadata_StreamInfo *si = &metadata->data.stream_info;

   cd->samplesPerSecond = si->sample_rate;
   cd->bitsPerSample = si->bits_per_sample;
   cd->channels = si->channels;
   cd->duration = (si->total_samples * 1000) / si->sample_rate;
}

FLAC__StreamDecoderWriteStatus FLAC_writecb(const FLAC__StreamDecoder * decoder,
                                            const FLAC__Frame * frame,
                                            const FLAC__int32 * const buffer[], void *client_data)
{
   
   // No idea how PUID signatures are generated for more than two 
   // channels, so not going to try
   if (frame->header.channels > 2)
      return FLAC__STREAM_DECODER_WRITE_STATUS_ABORT;

   // PUID code doesn't support anything other than 8 and 16 bit samples
   if (frame->header.bits_per_sample != 8 &&
       frame->header.bits_per_sample != 16 &&
       frame->header.bits_per_sample != 24)
      return FLAC__STREAM_DECODER_WRITE_STATUS_ABORT;

   int   samplesize = frame->header.bits_per_sample / 8;
   int   bufsize = samplesize * frame->header.channels * frame->header.blocksize;

   char *newdata = new char[bufsize];
   char *outputptr = newdata;

   for (unsigned samplenum = 0; samplenum < frame->header.blocksize; samplenum++)
        for (unsigned channum = 0; channum < frame->header.channels; channum++)
        {
           memcpy(outputptr, &buffer[channum][samplenum], samplesize);
           outputptr += samplesize;
        }

   clientdata_t *cd = reinterpret_cast < clientdata_t * >(client_data);
   if (cd->dataBytes == 0)
   {
       cd->data = newdata;
       cd->dataBytes = bufsize;
   }
   else
   {
       char *temp = new char[bufsize + cd->dataBytes];
       memcpy(temp, cd->data, cd->dataBytes);
       memcpy(temp + cd->dataBytes, newdata, bufsize);
       delete [] newdata;
       cd->data = temp;
       cd->dataBytes += bufsize;
   }

   return FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE;
}

FLAC__StreamDecoderReadStatus FLAC_readcb(const FLAC__StreamDecoder *decoder, 
                                          FLAC__byte buffer[], 
#ifdef LEGACY_FLAC
                                          unsigned *bytes, 
#else
                                          size_t *bytes, 
#endif
                                          void *client_data)
{
   clientdata_t *cd = reinterpret_cast < clientdata_t * >(client_data);

   unsigned numRead = tread(buffer, sizeof(char), *bytes, cd->in);
   if (numRead < *bytes)
   {
       *bytes = numRead;
       return FLAC__STREAM_DECODER_READ_STATUS_END_OF_STREAM;
   }

   return FLAC__STREAM_DECODER_READ_STATUS_CONTINUE;
}

FlacDecode::FlacDecode(const string & fileName, const string &encoding) : DecodePlugin()
{
   FLAC__StreamDecoderState state;

   cd.in = NULL;
   this->encoding = encoding;
   ready = false;
   decoder = FLAC__stream_decoder_new();
   
   if (!decoder)
      return;

   memset(&cd, 0, sizeof(clientdata_t));
   cd.in = topen(fileName.c_str(), "rb", encoding.c_str());
   if (!cd.in)
      return;

#ifdef LEGACY_FLAC
   if (!FLAC__stream_decoder_set_read_callback(decoder, &FLAC_readcb))
      return;

   if (!FLAC__stream_decoder_set_write_callback(decoder, &FLAC_writecb))
      return;

   if (!FLAC__stream_decoder_set_metadata_callback(decoder, &FLAC_metadatacb))
      return;

   if (!FLAC__stream_decoder_set_error_callback(decoder, &FLAC_errorcb))
      return;

   if (!FLAC__stream_decoder_set_client_data(decoder, &cd))
      return;

   state = FLAC__stream_decoder_init(decoder);
   if (state != FLAC__STREAM_DECODER_SEARCH_FOR_METADATA)
      return;
#else
   if (FLAC__stream_decoder_init_stream(decoder, &FLAC_readcb, NULL, NULL, NULL, NULL, &FLAC_writecb, &FLAC_metadatacb, &FLAC_errorcb, &cd) != FLAC__STREAM_DECODER_INIT_STATUS_OK)
      return;
#endif

   FLAC__stream_decoder_process_until_end_of_metadata(decoder);
   state = FLAC__stream_decoder_get_state(decoder);
   if (state != FLAC__STREAM_DECODER_SEARCH_FOR_FRAME_SYNC )
       return;

   duration = cd.duration;
   samplesPerSecond = cd.samplesPerSecond;
   channels = cd.channels;
   bitsPerSample = cd.bitsPerSample;
   ready = true;
}

FlacDecode::~FlacDecode(void)
{
   FLAC__stream_decoder_finish(decoder);
   FLAC__stream_decoder_delete(decoder);
   if (cd.in)
       tclose(cd.in);
}

int FlacDecode::getInfo(unsigned long &duration,
                        unsigned int &samplesPerSecond,
                        unsigned int &bitsPerSample, unsigned int &channels)
{
   if (!ready)
      return 0;

   duration = this->duration;
   samplesPerSecond = this->samplesPerSecond;
   bitsPerSample = this->bitsPerSample;
   channels = this->channels;

   return 1;
}

int FlacDecode::read(char *data, int maxBytes)
{
   FLAC__StreamDecoderState state;

   if (!ready)
       return -1;

   // If we have any leftover bytes, use those first
   if (cd.dataBytes > 0)
   {
       int toCopy = (maxBytes < cd.dataBytes) ? maxBytes : cd.dataBytes;

       memcpy(data, cd.data, toCopy);
       if (toCopy < cd.dataBytes)
       {
           memmove(cd.data, cd.data + toCopy, cd.dataBytes - toCopy);
           cd.dataBytes -= toCopy;
       }
       else
       {
           delete [] cd.data;
           cd.data = NULL;
           cd.dataBytes = 0;
       }

       return toCopy;
   }

   // No leftover bytes, so generate new ones
   while(1)
   {
       FLAC__stream_decoder_process_single(decoder);
       if (cd.data)
          break;
       
       state = FLAC__stream_decoder_get_state(decoder);
       if (state == FLAC__STREAM_DECODER_END_OF_STREAM)
           break;
       if (state != FLAC__STREAM_DECODER_SEARCH_FOR_FRAME_SYNC ||
           state != FLAC__STREAM_DECODER_READ_FRAME)
       {
          return -1;
       }
   }

   int ret;
   if (cd.dataBytes > maxBytes)
   {
       memcpy(data, cd.data, maxBytes);
       memmove(cd.data, cd.data + maxBytes, cd.dataBytes - maxBytes);
       cd.dataBytes -= maxBytes;
       ret = maxBytes;
   }
   else
   {
       ret = cd.dataBytes;
       memcpy(data, cd.data, cd.dataBytes);
       delete  [] cd.data;
       cd.data = NULL;
       cd.dataBytes = 0;
   }

   return ret;
}
