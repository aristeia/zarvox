/*
 * libid3tag - ID3 tag manipulation library
 * Copyright (C) 2000-2004 Underbit Technologies, Inc.
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
 * $Id: file.c 1403 2005-06-21 07:43:50Z robert $
 */

# ifdef HAVE_CONFIG_H
#  include "config.h"
# endif

# include "global.h"

# include <stdlib.h>
# include <string.h>

# ifdef HAVE_UNISTD_H
#  include <unistd.h>
# endif

# ifdef HAVE_ASSERT_H
#  include <assert.h>
# endif

# include "id3tag.h"
# include "file.h"
# include "tag.h"
# include "field.h"
# include "fileio.h"

#define COPY_BUFFER_SIZE 4096


struct filetag {
  struct id3_tag *tag;
  unsigned long location;
  id3_length_t length;
};

struct id3_file {
  TFILE *iofile;
  char encoding[64];
  enum id3_file_mode mode;
  char *path;

  int flags;

  struct id3_tag *primary;

  unsigned int ntags;
  struct filetag *tags;
};

enum {
  ID3_FILE_FLAG_ID3V1 = 0x0001
};

/*
 * NAME:	query_tag()
 * DESCRIPTION:	check for a tag at a file's current position
 */
static
signed long query_tag(TFILE *iofile)
{
  long save_position;
  id3_byte_t query[ID3_TAG_QUERYSIZE];
  signed long size;

  save_position = ttell(iofile);
  size = id3_tag_query(query, tread(query, 1, sizeof(query), iofile));
  tseek(iofile, save_position, SEEK_SET);

  return size;
}

/*
 * NAME:	read_tag()
 * DESCRIPTION:	read and parse a tag at a file's current position
 */
static
struct id3_tag *read_tag(TFILE *iofile, id3_length_t size)
{
  id3_byte_t *data;
  struct id3_tag *tag = 0;

  data = malloc(size);
  if (data) {
    if (tread(data, size, 1, iofile) == 1)
      tag = id3_tag_parse(data, size);

    free(data);
  }

  return tag;
}

/*
 * NAME:	update_primary()
 * DESCRIPTION:	update the primary tag with data from a new tag
 */
static
int update_primary(struct id3_tag *tag, struct id3_tag const *new)
{
  unsigned int i;
  struct id3_frame *frame;

  if (new) {
    if (!(new->extendedflags & ID3_TAG_EXTENDEDFLAG_TAGISANUPDATE))
      id3_tag_clearframes(tag);

    i = 0;
    while ((frame = id3_tag_findframe(new, 0, i++))) {
      if (id3_tag_attachframe(tag, frame) == -1)
	return -1;
    }
  }

  return 0;
}

/*
 * NAME:	tag_compare()
 * DESCRIPTION:	tag sort function for qsort()
 */
static
int tag_compare(const void *a, const void *b)
{
  struct filetag const *tag1 = a, *tag2 = b;

  if (tag1->location < tag2->location)
    return -1;
  else if (tag1->location > tag2->location)
    return +1;

  return 0;
}

/*
 * NAME:	add_filetag()
 * DESCRIPTION:	add a new file tag entry
 */
static
int add_filetag(struct id3_file *file, struct filetag const *filetag)
{
  struct filetag *tags;

  tags = realloc(file->tags, (file->ntags + 1) * sizeof(*tags));
  if (tags == 0)
    return -1;

  file->tags = tags;
  file->tags[file->ntags++] = *filetag;

  /* sort tags by location */

  if (file->ntags > 1)
    qsort(file->tags, file->ntags, sizeof(file->tags[0]), tag_compare);

  return 0;
}

/*
 * NAME:	del_filetag()
 * DESCRIPTION:	delete a file tag entry
 */
static
void del_filetag(struct id3_file *file, unsigned int index)
{
  assert(index < file->ntags);

  while (index < file->ntags - 1) {
    file->tags[index] = file->tags[index + 1];
    ++index;
  }

  --file->ntags;
}

/*
 * NAME:	add_tag()
 * DESCRIPTION:	read, parse, and add a tag to a file structure
 */
static
struct id3_tag *add_tag(struct id3_file *file, id3_length_t length)
{
  long location;
  unsigned int i;
  struct filetag filetag;
  struct id3_tag *tag;

  location = ttell(file->iofile);
  if (location == -1)
    return 0;

  /* check for duplication/overlap */
  {
    unsigned long begin1, end1, begin2, end2;

    begin1 = location;
    end1   = begin1 + length;

    for (i = 0; i < file->ntags; ++i) {
      begin2 = file->tags[i].location;
      end2   = begin2 + file->tags[i].length;

      if (begin1 == begin2 && end1 == end2)
	return file->tags[i].tag;  /* duplicate */

      if (begin1 < end2 && end1 > begin2)
	return 0;  /* overlap */
    }
  }

  tag = read_tag(file->iofile, length);

  filetag.tag      = tag;
  filetag.location = location;
  filetag.length   = length;

  if (add_filetag(file, &filetag) == -1 ||
      update_primary(file->primary, tag) == -1) {
    if (tag)
      id3_tag_delete(tag);
    return 0;
  }

  if (tag)
    id3_tag_addref(tag);

  return tag;
}

/*
 * NAME:	search_tags()
 * DESCRIPTION:	search for tags in a file
 */
static
int search_tags(struct id3_file *file)
{
  long save_position;
  signed long size;

  /*
   * save the current seek position
   */
  save_position = ttell(file->iofile);

  /* look for an ID3v1 tag */

  if (tseek(file->iofile, -128, SEEK_END) == 0) {
    size = query_tag(file->iofile);
    if (size > 0) {
      struct id3_tag const *tag;

      tag = add_tag(file, size);

      /* if this is indeed an ID3v1 tag, mark the file so */

      if (tag && (ID3_TAG_VERSION_MAJOR(id3_tag_version(tag)) == 1))
	file->flags |= ID3_FILE_FLAG_ID3V1;
    }
  }

  /* look for a tag at the beginning of the file */

  tseek(file->iofile, 0, SEEK_SET);

  size = query_tag(file->iofile);
  if (size > 0) {
    struct id3_tag const *tag;
    struct id3_frame const *frame;

    tag = add_tag(file, size);

    /* locate tags indicated by SEEK frames */

    while (tag && (frame = id3_tag_findframe(tag, "SEEK", 0))) {
      long seek;

      seek = id3_field_getint(id3_frame_field(frame, 0));
      if (seek < 0 || tseek(file->iofile, seek, SEEK_CUR) == -1)
	break;

      size = query_tag(file->iofile);
      tag  = (size > 0) ? add_tag(file, size) : 0;
    }
  }

  /* look for a tag at the end of the file (before any ID3v1 tag) */

  if (tseek(file->iofile, ((file->flags & ID3_FILE_FLAG_ID3V1) ? -128 : 0) +
	    -10, SEEK_END) == 0) {
    size = query_tag(file->iofile);
    if (size < 0 && tseek(file->iofile, size, SEEK_CUR) == 0) {
      size = query_tag(file->iofile);
      if (size > 0)
	add_tag(file, size);
    }
  }

  //tclearerr(file->iofile);

  /* restore seek position */

  tseek(file->iofile, save_position, SEEK_SET);

  /* set primary tag options and target padded length for convenience */

  if ((file->ntags > 0 && !(file->flags & ID3_FILE_FLAG_ID3V1)) ||
      (file->ntags > 1 &&  (file->flags & ID3_FILE_FLAG_ID3V1))) {
    if (file->tags[0].location == 0)
      id3_tag_setlength(file->primary, file->tags[0].length);
    else
      id3_tag_options(file->primary, ID3_TAG_OPTION_APPENDEDTAG, ~0);
  }

  return 0;
}

/*
 * NAME:	finish_file()
 * DESCRIPTION:	release memory associated with a file
 */
static
void finish_file(struct id3_file *file)
{
  unsigned int i;

  if (file->path)
    free(file->path);

  if (file->primary) {
    id3_tag_delref(file->primary);
    id3_tag_delete(file->primary);
  }

  for (i = 0; i < file->ntags; ++i) {
    struct id3_tag *tag;

    tag = file->tags[i].tag;
    if (tag) {
      id3_tag_delref(tag);
      id3_tag_delete(tag);
    }
  }

  if (file->tags)
    free(file->tags);

  free(file);
}

/*
 * NAME:	new_file()
 * DESCRIPTION:	create a new file structure and load tags
 */
static
struct id3_file *new_file(TFILE *iofile, enum id3_file_mode mode,
			  char const *path, const char *encoding)
{
  struct id3_file *file;

  file = malloc(sizeof(*file));
  if (file == 0)
    goto fail;

  file->iofile  = iofile;
  file->mode    = mode;
  strcpy(file->encoding, encoding);
  file->path    = path ? strdup(path) : 0;

  file->flags   = 0;

  file->ntags   = 0;
  file->tags    = 0;

  file->primary = id3_tag_new();
  if (file->primary == 0)
    goto fail;

  id3_tag_addref(file->primary);

  /* load tags from the file */

  if (search_tags(file) == -1)
    goto fail;

  id3_tag_options(file->primary, ID3_TAG_OPTION_ID3V1,
		  (file->flags & ID3_FILE_FLAG_ID3V1) ? ~0 : 0);

  if (0) {
  fail:
    if (file) {
      finish_file(file);
      file = 0;
    }
  }

  return file;
}

/*
 * NAME:	file->open()
 * DESCRIPTION:	open a file given its pathname
 */
struct id3_file *id3_file_open(char const *path, enum id3_file_mode mode, const char *encoding)
{
  TFILE *iofile;
  struct id3_file *file;

  assert(path);

  iofile = topen(path, (mode == ID3_FILE_MODE_READWRITE) ? "r+b" : "rb", encoding);
  if (iofile == 0)
    return 0;

  file = new_file(iofile, mode, path, encoding);
  if (file == 0)
    tclose(iofile);

  return file;
}

/*
 * NAME:	file->close()
 * DESCRIPTION:	close a file and delete its associated tags
 */
int id3_file_close(struct id3_file *file)
{
  int result = 0;

  assert(file);

  if (tclose(file->iofile) == EOF)
    result = -1;

  finish_file(file);

  return result;
}

/*
 * NAME:	file->tag()
 * DESCRIPTION:	return the primary tag structure for a file
 */
struct id3_tag *id3_file_tag(struct id3_file const *file)
{
  assert(file);

  return file->primary;
}

/*
 * NAME:	v1_write()
 * DESCRIPTION:	write ID3v1 tag modifications to a file
 */
static
int v1_write(struct id3_file *file,
	     id3_byte_t const *data, id3_length_t length)
{
  assert(!data || length == 128);

  if (data) {
    long location;

    if (tseek(file->iofile, (file->flags & ID3_FILE_FLAG_ID3V1) ? -128 : 0,
	      SEEK_END) == -1 ||
	(location = ttell(file->iofile)) == -1 ||
	twrite(data, 128, 1, file->iofile) == 0 ||
	tflush(file->iofile) == EOF)
      return -1;

    /* add file tag reference */

    if (!(file->flags & ID3_FILE_FLAG_ID3V1)) {
      struct filetag filetag;

      filetag.tag      = 0;
      filetag.location = location;
      filetag.length   = 128;

      if (add_filetag(file, &filetag) == -1)
	return -1;

      file->flags |= ID3_FILE_FLAG_ID3V1;
    }
  }
# if 0 // defined(HAVE_FTRUNCATE)
  else if (file->flags & ID3_FILE_FLAG_ID3V1) {
    long length;

    if (tseek(file->iofile, 0, SEEK_END) == -1)
      return -1;

    length = ttell(file->iofile);
    if (length == -1 ||
	(length >= 0 && length < 128))
      return -1;

    if (ftruncate(fileno(file->iofile), length - 128) == -1)
      return -1;

    /* delete file tag reference */

    del_filetag(file, file->ntags - 1);

    file->flags &= ~ID3_FILE_FLAG_ID3V1;
  }
# endif

  return 0;
}

/*
 * NAME:	v2_write()
 * DESCRIPTION:	write ID3v2 tag modifications to a file
 */
static
int v2_write(struct id3_file *file,
	     id3_byte_t const *data, id3_length_t length)
{
  TFILE  *out;
  char  *newpath = NULL, *buffer = NULL, *oldpath = NULL;
  int    numread = 0, numwritten = 0;
  struct id3_file *newfile = NULL;
  long offset = 0;
  assert(!data || length > 0);

  if (data &&
      ((file->ntags == 1 && !(file->flags & ID3_FILE_FLAG_ID3V1)) ||
       (file->ntags == 2 &&  (file->flags & ID3_FILE_FLAG_ID3V1))) &&
      file->tags[0].length == length) {
    /* easy special case: rewrite existing tag in-place */

    if (tseek(file->iofile, file->tags[0].location, SEEK_SET) == -1 ||
	twrite(data, length, 1, file->iofile) == 0 ||
	tflush(file->iofile) == EOF)
      return -1;

    goto done;
  }

  /* hard general case: rewrite entire file */
  newpath = malloc(strlen(file->path) + 32 );
  tmktempname(file->path, newpath, strlen(file->path) + 32);
  out = topen(newpath, "wb", file->encoding);
  if (out == NULL)
  {
      free(newpath);
      return -1;
  }

  /* Write the new tag out */
  if (twrite(data, length, 1, out) == 0)
  {
      tclose(out);
      tunlink(newpath, file->encoding);
      free(newpath);

      return -1;
  }

  if (file->tags && ID3_TAG_VERSION_MAJOR(file->tags[0].tag->version) > 1)
      offset = file->tags[0].length;
  if (tseek(file->iofile, offset, SEEK_SET) == -1)
  {
      tclose(out);
      tunlink(newpath, file->encoding);
      free(newpath);
      return -1;
  }
  
  buffer = malloc(COPY_BUFFER_SIZE);
  for(;;)
  {
      numread = tread(buffer, sizeof(char), COPY_BUFFER_SIZE, file->iofile);
      if (numread <= 0)
          break;

      numwritten = twrite(buffer, sizeof(char), numread, out);
      if (numwritten != numread)
      {
          tclose(out);
          tunlink(newpath, file->encoding);
          free(newpath);
          free(buffer);
          return -1;
      }
  }
  free(buffer);

  tclose(out);
  tclose(file->iofile);

  /* Now rename the file. let's be more paranoid here than id3lib */
  /* Move the old file to the same name with .old appended */
  oldpath = malloc(strlen(file->path) + 32);
  tmktempname(file->path, oldpath, strlen(file->path) + 32);
  if (trename(file->path, oldpath, file->encoding))
  {
      tunlink(newpath, file->encoding);
      tunlink(oldpath, file->encoding);
      free(newpath);
      free(oldpath);
      return -1;
  }

  /* Now rename the new file to proper file */
  if (trename(newpath, file->path, file->encoding))
  {
      /* Something failed, so let's try to put things back */
      trename(oldpath, file->path, file->encoding);
      tunlink(newpath, file->encoding);
      tunlink(oldpath, file->encoding);
      free(newpath);
      free(oldpath);
      return -1;
  }

  /* now that the rename succeeded, remove the old file */
  tunlink(oldpath, file->encoding);

  free(oldpath);
  free(newpath);

  /* Now do the housekeeping to make sure we leave things as we found them */
  newfile = id3_file_open(file->path, file->mode, file->encoding);
  if (newfile)
  {
      int i;

      /* Clean up the old data */
      if (file->path)
        free(file->path);

      if (file->primary) {
        id3_tag_delref(file->primary);
        id3_tag_delete(file->primary);
      }

      for (i = 0; i < file->ntags; ++i) {
        struct id3_tag *tag;

        tag = file->tags[i].tag;
        if (tag) {
          id3_tag_delref(tag);
          id3_tag_delete(tag);
        }
      }

      if (file->tags)
        free(file->tags);

      memcpy(file, newfile, sizeof(struct id3_file));
  }
  else
  {
      /* Hmmm. Something is wrong. Let's zero out the current info */
      memset(file, 0, sizeof(struct id3_file));
  }

 done:
  return 0;
}

/*
 * NAME:	file->update()
 * DESCRIPTION:	rewrite tag(s) to a file
 */
int id3_file_update(struct id3_file *file)
{
  int options, result = 0;
  id3_length_t v1size = 0, v2size = 0;
  id3_byte_t id3v1_data[128], *id3v1 = 0, *id3v2 = 0;

  assert(file);

  if (file->mode != ID3_FILE_MODE_READWRITE)
    return -1;

  options = id3_tag_options(file->primary, 0, 0);

  /* render ID3v1 */

  if (options & ID3_TAG_OPTION_ID3V1) {
    v1size = id3_tag_render(file->primary, 0);
    if (v1size) {
      assert(v1size == sizeof(id3v1_data));

      v1size = id3_tag_render(file->primary, id3v1_data);
      if (v1size) {
	assert(v1size == sizeof(id3v1_data));
	id3v1 = id3v1_data;
      }
    }
  }

  /* render ID3v2 */

  id3_tag_options(file->primary, ID3_TAG_OPTION_ID3V1, 0);

  v2size = id3_tag_render(file->primary, 0);
  if (v2size) {
    id3v2 = malloc(v2size);
    if (id3v2 == 0)
      goto fail;

    v2size = id3_tag_render(file->primary, id3v2);
    if (v2size == 0) {
      free(id3v2);
      id3v2 = 0;
    }
  }

  /* write tags */

  if (v2_write(file, id3v2, v2size) == -1 ||
      v1_write(file, id3v1, v1size) == -1)
    goto fail;

  tseek(file->iofile, 0, SEEK_SET);

  /* update file tags array? ... */

  if (0) {
  fail:
    result = -1;
  }

  /* clean up; restore tag options */

  if (id3v2)
    free(id3v2);

  id3_tag_options(file->primary, ~0, options);

  return result;
}
