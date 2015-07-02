/*----------------------------------------------------------------------------

   libtunepimp -- The MusicBrainz tagging library.  
                  Let a thousand taggers bloom!
   
   Copyright (C) 2006 Lukas Lalinsky
   
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

   $Id: mpc.cpp 7216 2006-04-14 23:10:49Z robert $

----------------------------------------------------------------------------*/

#include <stdio.h>
#include <assert.h>
#include <time.h>
#include "fileio.h"

#include <mpcdec/mpcdec.h> 

extern char *mpcErrorString;

typedef struct reader_data_t {
    TFILE *file;
    long size;
} reader_data;

static mpc_int32_t
read_impl(void *data, void *ptr, mpc_int32_t size)
{
    reader_data *d = (reader_data *) data;
    return tread(ptr, 1, size, d->file);
}

static mpc_bool_t
seek_impl(void *data, mpc_int32_t offset)
{
    reader_data *d = (reader_data *) data;
    return !tseek(d->file, offset, SEEK_SET);
}

static mpc_int32_t
tell_impl(void *data)
{
    reader_data *d = (reader_data *) data;
    return ttell(d->file);
}

static mpc_int32_t
get_size_impl(void *data)
{
    reader_data *d = (reader_data *) data;
    return d->size;
}

static mpc_bool_t
canseek_impl(void *data)
{
    return true;
} 

typedef struct mpc_decode_struct_t {
    TFILE *file;
    reader_data rdata;
    mpc_decoder decoder;
    mpc_reader reader;
    mpc_streaminfo info;
    MPC_SAMPLE_FORMAT buffer[MPC_DECODER_BUFFER_LENGTH];
    unsigned samples;
    unsigned offset;
} mpc_decode_struct;

extern "C" void *
mpcDecodeStart(const char *fileName, int flags, const char *encoding)
{
    mpc_decode_struct *ds;
    
    ds = new mpc_decode_struct();
    if (!ds) 
        goto error;
    
    ds->file = topen(fileName, "rb", encoding);
    if (!ds->file) 
        goto error;
    
    ds->samples = 0;
    ds->offset = 0;
    
    /* initialize our reader_data tag the reader will carry around with it */ 
    ds->rdata.file = ds->file;
    tseek(ds->file, 0, SEEK_END);
    ds->rdata.size = ttell(ds->file);
    tseek(ds->file, 0, SEEK_SET);
    
    /* set up an mpc_reader linked to our function implementations */
    ds->reader.read = read_impl;
    ds->reader.seek = seek_impl;
    ds->reader.tell = tell_impl;
    ds->reader.get_size = get_size_impl;
    ds->reader.canseek = canseek_impl;
    ds->reader.data = &ds->rdata;     
    
    /* read file's streaminfo data */
    mpc_streaminfo_init(&ds->info);
    if (mpc_streaminfo_read(&ds->info, &ds->reader) != ERROR_CODE_OK) {
        mpcErrorString = "Not a valid Musepack file.";
        goto error;
    }     
    
    /* instantiate a decoder with our file reader */
    mpc_decoder_setup(&ds->decoder, &ds->reader);
    if (!mpc_decoder_initialize(&ds->decoder, &ds->info)) {
        mpcErrorString = "Error initializing decoder.";
        goto error;
    }     
    
    return ds;
    
error:
    if (ds)
        delete ds;
    
    return NULL;
}

extern "C" int
mpcDecodeInfo(mpc_decode_struct_t *ds, unsigned long *duration, unsigned int *samplesPerSecond, unsigned int *bitsPerSample, unsigned int *channels)
{
    if (!ds)
        return 0;
        
    if (duration)
        *duration = (ds->info.pcm_samples * 1000) / ds->info.sample_freq;
    if (samplesPerSecond)
        *samplesPerSecond = ds->info.sample_freq;
    if (bitsPerSample)
        *bitsPerSample = 16;
    if (channels)
        *channels = ds->info.channels;
    return 1;
}

#ifdef MPC_FIXED_POINT
static int
shift_signed(MPC_SAMPLE_FORMAT val, int shift)
{
    if (shift > 0)
        val <<= shift;
    else if (shift < 0)
        val >>= -shift;
    return (int)val;
}
#endif 

extern "C" int
mpcDecodeRead(mpc_decode_struct_t *ds, mpc_int16_t *data, int maxBytes)
{
    if (!ds)
        return -1;
        
    unsigned status, maxSamples = maxBytes / 2 / ds->info.channels, samples, offset;
    
    if (ds->samples > 0) {
        samples = ds->samples;
        offset = ds->offset;
        ds->samples = 0;     
        ds->offset = 0;
        goto convert;
    }
    
    status = mpc_decoder_decode(&ds->decoder, ds->buffer, 0, 0);
    
    if (status == (unsigned)(-1)) { //decode error
        mpcErrorString = "Error decoding file.";
        return -1;
    }
    else if (status == 0) { //EOF
        return 0;
    }
    
    if (status > maxSamples) {
        ds->samples = status - maxSamples;
        ds->offset = maxSamples;
        samples = maxSamples;
        offset = 0;
    }
    else {
        ds->samples = 0;
        samples = status;
        offset = 0;
    }

convert:
    MPC_SAMPLE_FORMAT *buf = ds->buffer + offset;
    unsigned i = samples * ds->info.channels;
    while (i--) {
#ifdef MPC_FIXED_POINT
        int val = shift_signed(*buf++, 16 - MPC_FIXED_POINT_SCALE_SHIFT);
#else
        int val = (int)(*buf++ * 32768.0); 
#endif             
        if (val < -32768)
            val = -32768;
        else if (val > 32767)
            val = 32767;
#ifdef WORDS_BIGENDIAN
	*data++ = ((val & 0x00FF) << 8) | ((val & 0xFF00) >> 8);
#else
        *data++ = val;
#endif
    }
    
    return samples * 2 * ds->info.channels;
}

extern "C" void
mpcDecodeEnd(mpc_decode_struct_t *ds)
{
    if (ds) 
        delete ds;
}


