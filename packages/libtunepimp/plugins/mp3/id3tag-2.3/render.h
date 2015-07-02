/*
 * libid3tag - ID3 tag manipulation library
 * Copyright (C) 2000-2003 Underbit Technologies, Inc.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * $Id: render.h 1373 2005-05-24 05:29:15Z robert $
 */

# ifndef LIBID3TAG_RENDER_H
# define LIBID3TAG_RENDER_H

# include "id3tag.h"

id3_2_3_length_t id3_2_3_render_immediate(id3_2_3_byte_t **, char const *, unsigned int);
id3_2_3_length_t id3_2_3_render_syncsafe(id3_2_3_byte_t **, unsigned long, unsigned int);
id3_2_3_length_t id3_2_3_render_int(id3_2_3_byte_t **, signed long, unsigned int);
id3_2_3_length_t id3_2_3_render_binary(id3_2_3_byte_t **,
			       id3_2_3_byte_t const *, id3_2_3_length_t);
id3_2_3_length_t id3_2_3_render_latin1(id3_2_3_byte_t **, id3_2_3_latin1_t const *, int);
id3_2_3_length_t id3_2_3_render_string(id3_2_3_byte_t **, id3_2_3_ucs4_t const *,
			       enum id3_2_3_field_textencoding, int);
id3_2_3_length_t id3_2_3_render_padding(id3_2_3_byte_t **, id3_2_3_byte_t, id3_2_3_length_t);

id3_2_3_length_t id3_2_3_render_paddedstring(id3_2_3_byte_t **, id3_2_3_ucs4_t const *,
				     id3_2_3_length_t);

# endif
