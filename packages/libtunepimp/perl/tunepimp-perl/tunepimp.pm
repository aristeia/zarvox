#!/usr/bin/perl -w
# vi: set ts=4 sw=4 :
##############################################################################
#
#   libtunepimp -- The MusicBrainz tagging library.  
#                  Let a thousand taggers bloom!
#   
#   Copyright (C) Robert Kaye 2003
#   
#   This file is part of libtunepimp.
#
#   libtunepimp is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   libtunepimp is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with libtunepimp; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#   $Id: tunepimp.pm 1367 2005-02-21 01:10:28Z robert $
#
##############################################################################

=head1 NAME

MusicBrainz::Tunepimp::tunepimp - Perl binding for the tunepimp library

=head1 SYNOPSIS

	use MusicBrainz::Tunepimp::tunepimp;
	my $tp = MusicBrainz::Tunepimp::tunepimp->new("My App", "1.0");

=head1 ABSTRACT

  MusicBrainz (musicbrainz.org) is a free, community music metadatabase.
  The MusicBrainz Tunepimp library enables applications to fingerprint,
  identify, tag, and rename audio files based on the corresponding MusicBrainz
  data.  See http://www.musicbrainz.org/tagger/index.html for more
  information.

=head1 DESCRIPTION

First, please read the Tunepimp documentation.

This module is built on the C wrapper interface to Tunepimp; all of the
functions such as C<tp_GetStatus> have been transformed into Perl methods
by removing the "tp_" (or "tr_", or "md_" etc) prefix, placing the method
into the appropriate Perl class, and changing the first character of the
method name to lower case (except for "TRM..." which remains in upper case).
Hence, if you understand the Tunepimp documentation and know about
C<tr_GetFileName>, you'll know it's now in the "track" class and is called
C<getFileName>.

Hence here I'll just describe how this Perl module differs from the C wrapper
interface.

=cut

package MusicBrainz::Tunepimp::tunepimp;

use 5.008;
use strict;
use warnings;
use Carp;

require Exporter;
use AutoLoader;


sub AUTOLOAD {
	# This AUTOLOAD is used to 'autoload' constants from the constant()
	# XS function.

	my $constname;
	our $AUTOLOAD;
	($constname = $AUTOLOAD) =~ s/.*:://;
	croak "&MusicBrainz::Tunepimp::tunepimp::constant not defined" if $constname eq 'constant';
	my ($error, $val) = constant($constname);
	if ($error) { croak $error; }
	{
		no strict 'refs';
		# Fixed between 5.005_53 and 5.005_61
#XXX	if ($] >= 5.00561) {
#XXX		*$AUTOLOAD = sub () { $val };
#XXX	}
#XXX	else {
			*$AUTOLOAD = sub { $val };
#XXX	}
	}
	goto &$AUTOLOAD;
}

my %track_to_tunepimp;

################################################################################
package MusicBrainz::Tunepimp::tunepimp;
################################################################################

BEGIN
{
	my %constants = (
		TPError => {
			tpOk				=> 0,
			tpTooManyTRMs		=> 1,
			tpNoUserInfo		=> 2,
			tpLookupError		=> 3,
			tpSubmitError		=> 4,
			tpInvalidIndex		=> 5,
			tpInvalidObject		=> 6,
			tpErrorLast			=> 7,
		},
		TPCallbackEnum => {
			tpFileAdded			=> 0,
			tpFileChanged		=> 1,
			tpFileRemoved		=> 2,
			tpWriteTagsComplete	=> 3,
			tpCallbackLast		=> 4,
		},
		TPFileStatus => {
			eMetadataRead => 0,
			eUnrecognized => 1,		# unrecognized
			eRecognized => 2,		# Recognized and previously saved
			ePending => 3,			# pending trm calculation
			eTRMLookup => 4,		# trm done, pending trm lookup
			eTRMCollision => 5,		   # trm done, pending trm lookup
			eFileLookup => 6,		# trm done, no matches, pending file lookup
			eUserSelection => 7,	# file lookup done, needs user selection
			eVerified => 8,			# User verified, about to write changes to disk 
			eSaved => 9,			# Saved (renamed, taggs written)
			eDeleted => 10,			# to be deleted, waiting for refcount == 0
			eError => 11,			# Error
			eLastStatus => 12,
		},
		TPResultType => {
			eNone				=> 0,
			eArtistList			=> 1,
			eAlbumList			=> 2,
			eTrackList			=> 3,
			eMatchedTrack		=> 4,
		},
		TPAlbumType => {
			eAlbumType_Album		=> 0,
			eAlbumType_Single		=> 1,
			eAlbumType_EP			=> 2,
			eAlbumType_Compilation	=> 3,
			eAlbumType_Soundtrack	=> 4,
			eAlbumType_Spokenword	=> 5,
			eAlbumType_Interview	=> 6,
			eAlbumType_Audiobook	=> 7,
			eAlbumType_Live			=> 8,
			eAlbumType_Remix		=> 9,
			eAlbumType_Other		=> 10,
			eAlbumType_Error		=> 11,
		},
		TPAlbumStatus => {
			eAlbumStatus_Official		=> 0,
			eAlbumStatus_Promotion		=> 1,
			eAlbumStatus_Bootleg		=> 2,
			eAlbumStatus_Error			=> 3,
		},
		TPThreadPriority => {
			eThreadPriority_Idle		=> 0,
			eThreadPriority_Lowest		=> 1,
			eThreadPriority_Low			=> 2,
			eThreadPriority_Normal		=> 3,
			eThreadPriority_High		=> 4,
			eThreadPriority_Higher		=> 5,
			eThreadPriority_TimeCritical=> 6,
		},
	);

	use vars qw( @ISA $VERSION %EXPORT_TAGS @EXPORT_OK );

	@ISA = qw( Exporter );
	$VERSION = '0.03';

	require XSLoader;
	XSLoader::load('MusicBrainz::Tunepimp::tunepimp', $VERSION);

	my %all;
	while (my ($tag, $constants) = each %constants)
	{
		require constant;
		constant->import($constants);
		$EXPORT_TAGS{$tag} = [ keys %$constants ];
		$all{$_} = 1 for keys %$constants;
	}

	@EXPORT_OK = keys %all;
	$EXPORT_TAGS{"all"} = \@EXPORT_OK;
}

# Each of these subs are each here for one or more of these reasons:
# (1) to achieve something I don't yet know how to do in XS, or /could/ do in
#	  XS but it's just much easier to do in Perl
# (2) to modify an existing method to behave in a more Perl-like fashion
# (3) to create a new Perl-like method which is a wrapper around other
#	  methods.
# Hence each method below explains its existence.

=head2 MusicBrainz::Tunepimp::tunepimp

This class corresponds to a C<tunepimp_t> object.

=over 4

=item new

This method blesses the returned object into any appropriate subclass.
In other words, you can subclass this module.

=cut

sub new
{
	my $class = shift;
	my $self = _new(@_);
	bless $self, ref($class) || $class;
	$self;
}

=item as_hashref

Additional convenience method: retrieve all the fields of this object into a hash
(good for debugging).

=cut

sub as_hashref
{
	my $self = shift;

	+{
		map {
			my $method = $_;
			my $list = $method =~ s/^LIST_//;
			my $key = lcfirst substr($method, 3);
			$key =~ s/^tRM/TRM/;
			(
				$key => (
					$list
					? [ $self->$method ]
					: scalar $self->$method
				)
			);
		}
		grep !/^NO_/,

		# All the "get" methods.  Prefix by NO_ to ignore this method.
		# Prefix by LIST_ to return an array ref of the method called
		# in list context.
		qw(
getAllowedFileCharacters
getAutoFileLookup
getAutoSaveThreshold
getMinTRMThreshold
getClearTags
getDebug
getDestDir
getError
NO_getFileIds
getFileMask
getMoveFiles
NO_getNotification
getNotifyCallback
getNumFileIds
getNumFiles
getNumSupportedExtensions
getNumUnsubmitted
getNumUnsavedItems
getProxy
getAnalyzerPriority
getMaxFileNameLen
getAutoRemovedSavedFiles
getRenameFiles
getServer
NO_getStatus
getStatusCallback
LIST_getSupportedExtensions
getTRMCollisionThreshold
getTopSrcDir
NO_getTrack
NO_getTracks
getUseUTF8
LIST_getUserInfo
getVariousFileMask
getNonAlbumFileMask
getVersion
getWriteID3v1
		)
	};
}

=item getVersion

As a Perl nicety, in scalar context, the version is returned in dotted form
(e.g. "0.2.1")

=cut

sub getVersion
{
	my $self = shift;
	my @version = $self->_getVersion;
	wantarray ? @version : join(".", @version);
}

=item getTrack

Tracks (C<track_t>) are blessed into the class given by C<$tunepimp-E<gt>track_class>.
Hence, if you want to subclass track objects, you should first subclass
C<MusicBrainz::Tunepimp::tunepimp>, and override C<track_class> to return the
name of your track class.

=cut

# Also, when instantiating a new track object, record its parent tunepimp object in
# the %track_to_tunepimp hash, so we can release it properly later.

sub getTrack
{
	my $self = shift;
	my $track = $self->_getTrack(@_)
		or return undef;
	$track_to_tunepimp{ $$track } = $self;
	bless $track, $self->track_class;
}

=item track_class

This method returns the class into which tracks (returned by
C<getTrack> and C<getTracks>) should be blessed.

=cut

sub track_class { "MusicBrainz::Tunepimp::track" }

=item getTracks

Additional convenience method: retrieve all tracks.

=cut

sub getTracks
{
	my $self = shift;
	map { $self->getTrack($_) } $self->getFileIds;
}

=item writeTags

The C function (C<tp_WriteTags>) accepts a list of integers (file IDs)
via an C<int *> and an C<int> argument; we just accept a Perl list of integers.

=cut

# Pack a list of integers and pass to _writeTags (easier to pack() here)

sub writeTags
{
	my ($self, @fileids) = @_;
	my $ids = pack "i*", @fileids;
	$self->_writeTags($ids, scalar @fileids);
}

=item addFiles

Additional convenience method: multiple calls to addFile.
e.g. C<$tp-E<gt>addFiles(glob("*.mp3"))>

=cut

sub addFiles
{
	my $self = shift;
	map { $self->addFile($_, 0) } @_;
}

=item getRecognizedFileList

This method returns the number of recognized files below the given threshold,
and a reference to the list of recognized file IDs.  The threshold is given
as an integer percentage, e.g. "30" for 30%.  For example:

	($num_below_threshold, $recognized)
		= $tp->getRecognizedFileList($threshold);
	
	printf "%d of %d recognized files are below %d%% similarity\n",
		$num_below_threshold, scalar(@$recognized),
		$threshold;

	print "The IDs of the recognized files are @$recognized\n";

=cut

sub getRecognizedFileList
{
	my $self = shift;
	my ($num_below_threshold, @recognized_ids)
		= $self->_getRecognizedFileList(@_)
			or return;

	($num_below_threshold, \@recognized_ids);
}

=item getServer, getProxy

Perl nicety: in scalar context, return the host name and port number joined
by a colon.  If they have not been set, return the empty list (or C<undef>).

=cut

sub getServer
{
	my $self = shift;
	my ($host, $port) = $self->_getServer;
	return if $host eq "" and $port == 0;
	wantarray ? ($host, $port) : ("$host:$port");
}

sub getProxy
{
	my $self = shift;
	my ($host, $port) = $self->_getProxy;
	return if $host eq "" and $port == 0;
	wantarray ? ($host, $port) : ("$host:$port");
}

=item getUserInfo

Perl nicety: in scalar context, return only the user name,
instead of only the password.

=cut

sub getUserInfo
{
	my $self = shift;
	my ($userName, $password) = $self->_getUserInfo;
	wantarray ? ($userName, $password) : $userName;
}

=item Combined get / set methods

Additional methods.
As a Perl nicety, we provide combined get / set methods for various things.
e.g.

	# This calls $tunepimp->getDestDir
	$dir = $tunepimp->destDir;

	# This calls both getDestDir and setDestDir; it
	# both sets a new value and returns the old one.
	$olddir = $tunepimp->destDir($newdir);

Any pair of get / set methods are implemented as a combined method here.
The name of the combined method is that of the get / set, with "Get" or "Set"
removed, and the first character then changed to lower case (except for "TRM...").

=cut

# These ones get/set one value at a time
for my $set (qw(
setAllowedFileCharacters
setAutoFileLookup
setAutoSaveThreshold
setClearTags
setDebug
setDestDir
setFileMask
setMoveFiles
setNotifyCallback
setRenameFiles
setStatusCallback
setTRMCollisionThreshold
setTopSrcDir
setUseUTF8
setVariousFileMask
setNonAlbumFileMask
setWriteID3v1
)) {
	(my $get = $set) =~ s/^set/get/;
	my $sub = lcfirst substr($set, 3);
	$sub =~ s/^tRM/TRM/;

	my $t = sub {
		my $self = shift;
		my $old = $self->$get;
		$self->$set(@_) if @_;
		$old;
	};

	no strict 'refs';
	*{$sub} = $t;
}

=pod

All the getters and setters handle a single value at a time,
except for "proxy", "server" and "userInfo", which all deal with
a pair of values.

=cut

# These ones get/set a pair of things
for my $set (qw(
setProxy
setServer
setUserInfo
)) {
	(my $get = $set) =~ s/^set/get/;
	my $sub = lcfirst substr($set, 3);

	my $t = sub {
		my $self = shift;
		my @old = (wantarray ? $self->$get : scalar $self->$get);
		$self->$set(@_) if @_;
		wantarray ? @old : $old[0];
	};

	no strict 'refs';
	*{$sub} = $t;
}

=back

=cut

################################################################################
package MusicBrainz::Tunepimp::track;
################################################################################

=head2 MusicBrainz::Tunepimp::track

This class corresponds to a C<track_t> object.
You should never need to use the name of this class unless you're planning to
subclass it (or one of the other Tunepimp classes).

=over 4

=cut

# When destroying a track, look up its parent tunepimp object in
# %track_to_tunepimp so we can call tp_ReleaseTrack properly.

sub DESTROY
{
	my $self = shift;
	my $tunepimp = delete $track_to_tunepimp{ $$self };
	return $tunepimp->_releaseTrack($self) if $tunepimp;
	use Carp qw( carp );
	carp "Error releasing track $self (cannot find tunepimp object)"
		if $^W;
}

=item as_hashref

Additional convenience method: retrieve all the fields of this object into a hash
(good for debugging).

=cut

sub as_hashref
{
	my $self = shift;

	+{
		error				=> $self->getError,
		fileName			=> $self->getFileName,
		numResults			=> $self->getNumResults,
		similarity			=> $self->getSimilarity,
		status				=> $self->getStatus,
		TRM					=> $self->getTRM,
		hasChanged			=> $self->hasChanged,
	};
}

=item getLocalMetadata, getServerMetadata

For convenience, if no metadata argument is supplied, make a new one and
return that.  The class used to construct a new C<metadata_t> object
is given by C<$track-E<gt>metadata_class>.

=cut

sub getLocalMetadata
{
	my ($self, $md) = @_;
	$md ||= $self->metadata_class->new;
	$self->_getLocalMetadata($md);
	$md;
}

sub getServerMetadata
{
	my ($self, $md) = @_;
	$md ||= $self->metadata_class->new;
	$self->_getServerMetadata($md);
	$md;
}

=item metadata_class

This method returns the class into which automatically created metadata objects
(returned by C<getLocalMetadata> and C<getServerMetadata>) should be blessed.

=cut

sub metadata_class { "MusicBrainz::Tunepimp::metadata" }

=item getResults

This method returns the type of results (see C<:TPResultType>) and a reference
to the list of results.  For example:

	($type, $results) = $track->getResults;

	for my $result (@$results)
	{
		...;
	}

Each element of C<$results> is a plain hash reference containing the relevant
fields.  Some of the fields may themselves be hash references, e.g. for a
C<eTrackList> result you can do C<$$result{album}{artist}{name}>.

=cut

=back

=cut

################################################################################
package MusicBrainz::Tunepimp::metadata;
################################################################################

=head2 MusicBrainz::Tunepimp::metadata

This class corresponds to a C<metadata_t> object.
You should never need to use the name of this class unless you're planning to
subclass it (or one of the other Tunepimp classes).

=over 4

=item new

This method blesses its return value into the appropriate subclass.

=cut

sub new
{
	my $class = shift;
	my $self = _new(@_);
	bless $self, ref($class) || $class;
}

=item member access

In the C interface the caller is expected to just read and write the member
fields directly.  (Side note: that means they're expected to know to deal with
C<malloc()> and C<free()> too.  This is probably a bad idea).

For the Perl interface however we'll provide separate "get" and "set" methods,
then add combined get/set methods over the top of those.

=cut

# These ones get/set one value at a time
for my $set (qw(
setArtist
setSortName
setAlbum
setTrack
setTrackNum
setVariousArtist
setNonAlbum
setArtistId
setAlbumId
setTrackId
setFileTrm
setAlbumArtistId
setDuration
setAlbumType
setFileFormat
setNumTRMIds
)) {
	(my $get = $set) =~ s/^set/get/;
	my $sub = lcfirst substr($set, 3);

	my $t = sub {
		my $self = shift;
		my $old = $self->$get;
		$self->$set(@_) if @_;
		$old;
	};

	no strict 'refs';
	*{$sub} = $t;
}

=item as_hashref

Additional convenience method: retrieve all the fields of this object into a hash
(good for debugging, and maybe in real life use).

=cut

sub as_hashref
{
	my $self = shift;

	{
		artist			=> $self->getArtist,
		sortname		=> $self->getSortName,
		album			=> $self->getAlbum,
		track			=> $self->getTrack,
		tracknum		=> $self->getTrackNum,
		variousartist	=> $self->getVariousArtist,
		nonalbum	=> $self->getNonAlbum,
		artistid		=> $self->getArtistId,
		albumid			=> $self->getAlbumId,
		trackid			=> $self->getTrackId,
		filetrm			=> $self->getFileTrm,
		albumartistid	=> $self->getAlbumArtistId,
		duration		=> $self->getDuration,
		albumtype		=> $self->getAlbumType,
		fileFormat		=> $self->getFileFormat,
		releaseDate		=> [ $self->getReleaseYear, $self->getReleaseMonth, $self->getReleaseDay ],
		releaseCountry	=> $self->getReleaseCountry,
		numtrmids		=> $self->getNumTrmIds,
	};
}

=item getAlbumTypeNameFromNumber, getAlbumStatusNameFromNumber

Minor convenience: this can be called either as a class or an object
method, with an optional numeric argument.  The number defaults to that
retrieved from C<$self> if we were called as an object method.

In other words, these all work:

	# Uses $number
	$name = MusicBrainz::Tunepimp::metadata->getAlbumTypeNameFromNumber($number);

	# Uses $metadata->getAlbumType
	$name = $metadata->getAlbumTypeNameFromNumber;

	# Uses $number
	$name = $metadata->getAlbumTypeNameFromNumber($number);

The same applies to C<getAlbumStatusNameFromNumber> / C<getAlbumStatus>.
	
=cut

sub getAlbumTypeNameFromNumber
{
	my ($self, $num) = @_;
	$num = $self->getAlbumType
		if not defined $num
		and ref($self)
		and $self->isa(__PACKAGE__)
		and $self->can("getAlbumType");
	_getAlbumTypeNameFromNumber($num);
}

sub getAlbumStatusNameFromNumber
{
	my ($self, $num) = @_;
	$num = $self->getAlbumStatus
		if not defined $num
		and ref($self)
		and $self->isa(__PACKAGE__)
		and $self->can("getAlbumStatus");
	_getAlbumStatusNameFromNumber($num);
}

sub getAlbumTypeNumberFromName
{
	my ($self, $name) = @_;
	# WARNING!	For some reason the first 4 characters are ignored
	_getAlbumTypeNumberFromName($name);
}

sub getAlbumStatusNumberFromName
{
	my ($self, $name) = @_;
	# WARNING!	For some reason the first 6 characters are ignored
	_getAlbumStatusNumberFromName($name);
}

=back

=cut

################################################################################
# Restore original package (some parts of the Makefile complain otherwise)
################################################################################
package MusicBrainz::Tunepimp::tunepimp;

=head2 EXPORT TAGS

The only things which may be exported are the C<enum> values from
F<tunepimp/defs.h>.

=over 4

=item :TPError

tpOk, tpTooManyTRMs, tpNoUserInfo etc

These correspond to the value returned by C<$tunepimp-E<gt>getError>
or C<$track-E<gt>getError>.

=item :TPCallbackEnum

tpFileAdded, tpFileChanged, tpFileRemoved.

These are the values returned by
the "status" callback (see getStatus, setStatusCallback, getStatusCallback).

=item :TPFileStatus

eUnrecognized, eRecognized, ePending etc

These correspond to the value returned by C<$track-E<gt>getStatus>.

=item :TPResultType

eNone, eArtistList, eAlbumList etc.

These correspond to the "type" value returned by C<$track-E<gt>getResults>.

=item :TPAlbumType

=item :TPAlbumStatus

These correspond to the values returned by C<$metadata-E<gt>getAlbumType>
and C<$metadata-E<gt>getAlbumStatus>.

=back

Use the export tag ":all" to export everything.

Nothing is exported by default.

=cut

=head1 SEE ALSO

MusicBrainz in general: http://www.musicbrainz.org/

The MusicBrainz Tagger: http://www.musicbrainz.org/tagger/index.html

MusicBrainz mailing lists: http://www.musicbrainz.org/list.html

Other Perl code (available from CPAN):
C<MusicBrainz::Client>,
C<MusicBrainz::Client::Simple>

=head1 BUGS

At the time of writing, there is no Tunepimp documentation yet
- just the source code.

The following methods are out of bounds:
C<setStatusCallback>, C<getStatusCallback>, C<setNotifyCallback>,
C<getNotifyCallback>.  Don't use them.  They don't work.  They probably
never will.  Instead, please use only the "polling" version to retrieve
callback information, like so:

	while (my ($type, $fileid) = $tunepimp->getNotification)
	{
		...;
	}

	while (defined (my $status = $tunepimp->getStatus))
	{
		...;
	}

=head1 AUTHOR

Dave Evans, L<http://djce.org.uk/>

=head1 COPYRIGHT AND LICENSE

Copyright 2003 by Dave Evans

This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself. 

=cut

1;
__END__

# eof tunepimp.pm
