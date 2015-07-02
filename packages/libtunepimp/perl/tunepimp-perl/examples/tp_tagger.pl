#!/usr/bin/perl -w
# vi: set ts=4 sw=4 :

use strict;

use MusicBrainz::Tunepimp::tunepimp;

use constant VARTIST_MBID   => "89ad4ac3-39f7-470e-963a-56509c546377";
use constant CVS_ID			=> '$Id: tp_tagger.pl 1367 2005-02-21 01:10:28Z robert $';
use constant CVS_REVISION	=> '$Revision: 1367 $';

use MusicBrainz::Tunepimp::tunepimp qw(
	:TPError
	:TPFileStatus
	:TPCallbackEnum
	:TPAlbumType
	:TPResultType
);

my %fileStatusText = (
	&eUnrecognized => "Unrecognized",
	&eRecognized => "Recognized",
	&ePending => "Pending",
	&eTRMLookup => "TRM Lookup",
	&eTRMCollision => "TRM Collision",
	&eFileLookup => "File Lookup",
	&eUserSelection => "User Selection",
	&eVerified => "Verified",
	&eSaved => "Saved",
	&eDeleted => "Deleted",
	&eError => "Error",
);

# XXX a way to extract this from the lib
my %known_replacement_sequences = map { $_ => 1 } (
	"%artist", "%sortname", "%abc2", "%abc3", "%abc",
	"%album", "%0num", "%num", "%track", "%format",
);
sub validate_file_mask
{
	local $_ = shift;
	while (/(%\w+)/g)
	{
		$known_replacement_sequences{$1}
			or warn "Warning: '$1' isn't a valid file mask substitution\n";
	}
}

my $term;
eval '
	use Term::ReadLine;
	$term = new Term::ReadLine "tp_tagger.pl";
	my $OUT = $term->OUT || \*STDOUT;
	select $OUT;
';
*getCommand = ($@ ? \&getCommandSimple : \&getCommandReadLine);
                                      
##
## Read a line from standard input using libreadline and put it into
## the history buffer.
##
sub getCommandReadLine
{
	my $prompt = shift() || "tag> ";
	my $default = shift;

	my $line = $term->readline($prompt, $default);

	## line can be NULL if the user typed Ctrl-D
	$term->addhistory($line) if defined $line and $line =~ /\S/;
	$line = "q" if not defined $line; # quit
	
	$line =~ s/^\s*(.*?)\s*$/$1/;
    $line;
}                                     
                                      
sub getCommandSimple
{
	my $prompt = shift() || "tag> ";
	local $| = 1;
    printf($prompt);
	my $cmdLine = <STDIN>;
	chomp $cmdLine if defined $cmdLine;
	$cmdLine = "q" if not defined $cmdLine; # quit

	$cmdLine =~ s/^\s*(.*?)\s*$/$1/;
    $cmdLine;
}

sub printList
{
	my $pimp = shift;

	my @ids = $pimp->getFileIds;

    if (@ids == 0)
	{
        printf("No files in the tagger.\n");
	}
    else
    {
        for my $id (@ids)
        {
			my $track = $pimp->getTrack($id);
            if (!$track)
            {
                printf("Can't get track %d info\n", $id);
                next;
            }

			$track->lock;
            my $fileName = $track->getFileName;
            printf("%d: %s, %3d%%: %s\n", $id, 
                                   $fileStatusText{$track->getStatus},
                                   $track->getSimilarity,
                                   $fileName);
            if ($track->getStatus == &eError)
            {
                printf("  Error: %s\n", $track->getError);
            }
            $track->unlock;
        }
    }

    printf("\n%d unsubmitted TRMs.\n\n", $pimp->getNumUnsubmitted);
}

sub printTrack
{
	my ($pimp, $id) = @_;

	my $data;

    my $track = $pimp->getTrack($id);
    if (!$track)
    {
        printf("Can't get track %d\n\n", $id);
        return;
    }

	$track->lock;
	my $fileName = $track->getFileName;
    printf("%d: %s: %s\n", $id, 
                           $fileStatusText{$track->getStatus},
                           $fileName);

	my $trm = $track->getTRM;
    printf("       TRM: %s\n", $trm);
    printf("Similarity: %d\n", $track->getSimilarity);
    printf("   Changed: %d\n\n", $track->hasChanged);

	$data = $track->getLocalMetadata;
    printf("File metadata:\n");
    printf("   Format: %s\n", $data->getFileFormat);
    printf("   Artist: %s\n", $data->getArtist);
    printf(" SortName: %s\n", $data->getSortName);
    printf("    Album: %s\n", $data->getAlbum);
    printf("    Track: %s\n", $data->getTrack);
    printf(" TrackNum: %d\n", $data->getTrackNum);
    printf(" Duration: %ld\n", $data->getDuration);
    printf(" ArtistId: %s\n", $data->getArtistId);
    printf("  AlbumId: %s\n", $data->getAlbumId);
    printf("  TrackId: %s\n", $data->getTrackId);
    printf("       VA: %d\n", $data->getVariousArtist);
    printf("       NA: %d\n\n", $data->getNonAlbum);

	$data = $track->getServerMetadata;
    printf("Server metadata:\n");
    printf("   Artist: %s\n", $data->getArtist);
    printf(" SortName: %s\n", $data->getSortName);
    printf("    Album: %s\n", $data->getAlbum);
    printf("    Track: %s\n", $data->getTrack);
    printf(" TrackNum: %d\n", $data->getTrackNum);
    printf(" Duration: %ld\n", $data->getDuration);
    printf(" ArtistId: %s\n", $data->getArtistId);
    printf("  AlbumId: %s\n", $data->getAlbumId);
    printf("  TrackId: %s\n", $data->getTrackId);
    printf("       VA: %d\n", $data->getVariousArtist);
    printf("       NA: %d\n", $data->getNonAlbum);
	printf("  Release: %04d-%02d-%02d %s\n",
		$data->getReleaseYear,
		$data->getReleaseMonth,
		$data->getReleaseDay,
		$data->getReleaseCountry || "",
	) if $data->getReleaseYear;
    if ($data->getAlbumType != eAlbumType_Error)
    {
		my $type = $data->getAlbumTypeNameFromNumber;
        printf("AlbumType: %s\n", $type);
    }

    printf("\n");
	$track->unlock;
}

sub _printArtistResult
{
	my ($track, $results) = @_;

	$track->lock;
    my $fileName = $track->getFileName;
	$track->unlock;

	print "File: $fileName\n";

	print "Select an artist:\n";
	print "Num  Rel%  Name (SortName)\n";

    for my $i (0 .. $#$results)
    {
		my $r = $results->[$i];
		my $names = $r->{name};
		$names .= " ($r->{sortName})"
			unless $r->{sortName} eq $r->{name};
		printf "%2d.  %3d%%  %s\n", $i, $r->{relevance}, $names;
    }
}

sub _printAlbumResult
{
	my ($track, $results) = @_;

	$track->lock;
    my $fileName = $track->getFileName;
	$track->unlock;

	print "File: $fileName\n";

	my $artist = $results->[0]{artist};
	print "Artist: $artist->{name}";
	print " ($artist->{sortName})"
		unless $artist->{sortName} eq $artist->{name};
	print "\n";

	print "Select an album:\n";
	print "Num  Rel%  Tracks  DiscIDs  Name\n";

    for my $i (0 .. $#$results)
    {
		my $r = $results->[$i];

        printf "%2d.  %3d%%  %6d  %7d  %s\n",
			$i,
            $r->{relevance},
			$r->{numTracks},
			$r->{numCDIndexIds},
			$r->{name},
			;
    }
}

sub _printTrackResult
{
	my ($track, $results) = @_;

	$track->lock;
    my $fileName = $track->getFileName;
	$track->unlock;

	print "File: $fileName\n";

	my $artist = $results->[0]{artist};
	print "Artist: $artist->{name}";
	print " ($artist->{sortName})"
		unless $artist->{sortName} eq $artist->{name};
	print "\n";

	print "Select a track:\n";
	print "Num  Rel%  Tracks  DiscIDs  Album                             TRMs  Name\n";

    for my $i (0 .. $#$results)
    {
		my $r = $results->[$i];

        printf "%2d.  %3d%%  %6d  %7d  %-32.32s  %4d  %s\n",
			$i,
			$r->{relevance},
			$r->{album}->{numTracks},
			$r->{album}->{numCDIndexIds},
			$r->{album}->{name},
			$r->{numTRMIds},
			$r->{name},
			;
    }
}

sub printResults
{
	my ($pimp, $id) = @_;

    my $track = $pimp->getTrack($id);
    if (!$track)
    {
        printf("Can't get track %d\n\n", $id);
        return;
    }

    $track->lock;
    my $fileName = $track->getFileName;
	my ($type, $results) = $track->getResults;
    $track->unlock;

    if (not defined $results)
    {
        print "No results for this track at this time\n";
    } elsif (not @$results) {
        print "No results for this track!\n";
	} elsif ($type == eArtistList) {
		_printArtistResult($track, $results);
	} elsif ($type == eAlbumList) {
		_printAlbumResult($track, $results);
	} elsif ($type == eTrackList) {
		_printTrackResult($track, $results);
	} else {
		print "Error!  This tagger doesn't match the Tunepimp library you're using.\n";
		print "(Unknown results type #$type)\n";
    }
}

# FIXME "toggle" - this seems to only implement "set"!
sub toggleVA
{
	my ($pimp, $id) = @_;

    my $track = $pimp->getTrack($id);
    if (!$track)
    {
        printf("Can't get track %d\n\n", $id);
        return;
    }

    $track->lock;
    if ($track->getStatus != eUserSelection && $track->getStatus != eRecognized)
    {
		$track->unlock;
        printf("Only tracks waiting for a user selection or recognized tracks "
               . "can be looked up as various artist.\n");
        return;
    }
    else
    {
        my $data = $track->getLocalMetadata;
		$data->setArtistId(VARTIST_MBID);
        $track->setLocalMetadata($data);
        $track->setStatus(eFileLookup);
    }
    $track->unlock;

    $pimp->wake($track);
}

sub setNewMetadata
{
	my ($pimp, $id) = @_;

    my $track = $pimp->getTrack($id);
    if (!$track)
    {
        printf("Can't get track %d\n\n", $id);
        return;
    }

	$track->lock;
    my $data = $track->getServerMetadata;
	$track->unlock;

	$data->setArtist(getCommand("Artist: ", $data->getArtist));
	$data->setAlbum(getCommand("Album: ", $data->getAlbum));
	$data->setTrack(getCommand("Track: ", $data->getTrack));

	$data->setTrackNum(0);
	$data->setDuration(0);
	$data->setArtistId("");
	$data->setAlbumId("");
	$data->setTrackId("");

    $track->lock;
    $track->setServerMetadata($data);
    $track->setStatus(eFileLookup);
    $track->unlock;

    $pimp->wake($track);
}

sub selectTrack
{
	my ($pimp, $id, $result) = @_;

    my $track = $pimp->getTrack($id);
    if (!$track)
    {
        printf("Can't get track %d\n\n", $id);
        return;
    }

	$pimp->selectResult($track, $result);
}

# Simple check to squash duplicate notifications
# FIXME fix the library?
my $last_notify;

sub notify
{
	my ($pimp, $data, $type, $id, $status) = @_;
	my $fileName;

    my $track = $pimp->getTrack($id);
    if ($track)
    {
		$track->lock;
        $fileName = $track->getFileName;
		$track->unlock;
    }
    else
	{
        $fileName = "<unknown>";
	}

	my $msg = "?";

    if ($type == tpFileAdded)
    {
            $msg = sprintf("File added: %s\n", $fileName);
	} elsif ($type == tpFileRemoved) {
            $msg = sprintf("File removed: %d\n", $id);
	} elsif ($type == tpFileChanged) {
            if ($track)
			{
                $msg = sprintf("%s: %s\n", $fileStatusText{$status}, $fileName);
			}
	} elsif ($type == tpWriteTagsComplete) {
            $msg = sprintf("Writing tags complete!\n");
	}

	print $msg unless $msg eq $last_notify;
	$last_notify = $msg;
}

################################################################################
# Load / Save options
################################################################################

use constant TUNEPIMP_RC_FILE => "$ENV{HOME}/.tunepimprc";

use constant PIMP_SETTINGS => qw(
allowedFileCharacters
autoFileLookup
autoSaveThreshold
clearTags
debug
destDir
fileMask
moveFiles
notifyCallback
renameFiles
statusCallback
TRMCollisionThreshold
topSrcDir
useUTF8
variousFileMask
nonAlbumFileMask
writeID3v1
proxy
server
userInfo
);

sub load_config
{
	my ($pimp, $file, %opts) = @_;
	$file = TUNEPIMP_RC_FILE unless defined $file;

	if (open(my $fh, "<", $file))
	{
		print "Loading options from $file\n";
		local $/ = undef;
		my $all = <$fh>;
		close $fh;
		eval $all;
		warn "Error: $@\n" if $@;
	} elsif ($opts{'quiet'}) {
		# nothing
	} else {
		print "Failed to open $file: $!\n";
	}
}

sub save_config
{
	my ($pimp, $file, %opts) = @_;
	$file = TUNEPIMP_RC_FILE unless defined $file;

	if (open(my $fh, ">", $file))
	{
		use Data::Dumper qw( Dumper );
		local $Data::Dumper::Indent = 0;
		local $Data::Dumper::Terse = 1;

		for my $setting (PIMP_SETTINGS)
		{
			my @v = $pimp->$setting;
			print $fh "\$pimp->$setting(" . join(",", Dumper(@v)) . ");\n";
		}

		close($fh)
		? print("Options saved to $file\n")
		: print("Failed to save options to $file: $!\n");
	} elsif ($opts{'quiet'}) {
		# nothing
	} else {
		print "Failed to write to $file: $!\n";
	}
}

################################################################################
# Commands
################################################################################

# Each verb handler gets called with these arguments:
# $pimp, $context, @params
my %verb_handlers;
use constant INFINITE => 1E6;

sub check_args
{
	my ($arglist, $minargs, $maxargs, $usage) = @_;
	my $got = @$arglist - 2;
	return @$arglist if $got >= $minargs and $got <= $maxargs;
	if ($usage)
	{
		print "Usage: $arglist->[1]{verb} $usage\n";
		return;
	}
	if ($maxargs == 0)
	{
		print "Usage: $arglist->[1]{verb}\n";
		return;
	}
	print "Usage: $arglist->[1]{verb} ($minargs - $maxargs parameters)\n";
	return;
}

# tagger control

$verb_handlers{"quit"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 0)
		or return;
	$_[1]{quit} = 1;
};

$verb_handlers{"help"} = $verb_handlers{"h"} = $verb_handlers{"?"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 0)
		or return;
	showHelp($pimp);
};

$verb_handlers{"load-config"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 1, "[FILE]")
		or return;
	load_config($_[0], $_[2]);
};

$verb_handlers{"save-config"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 1, "[FILE]")
		or return;
	save_config($_[0], $_[2]);
};

$verb_handlers{"shell"} = $verb_handlers{"sh"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, INFINITE, "[COMMAND]")
		or return;
	my $command = $context->{'last_params'} || $ENV{SHELL} || "/bin/sh";
	system $command;
};

# the tagging process

$verb_handlers{"list"} = $verb_handlers{"l"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 0)
		or return;
	printList($pimp);
};

$verb_handlers{"add-file"} = $verb_handlers{"a"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, INFINITE, "FILE")
		or return;
	$pimp->addFile($context->{'last_params'}, 0);
};

$verb_handlers{"glob"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, INFINITE, "FILE")
		or return;
	$pimp->addFiles( glob($context->{'last_params'}) );
};

$verb_handlers{"add-directory"} = $verb_handlers{"d"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, INFINITE, "DIR")
		or return;
	$pimp->addDir($context->{'last_params'});
};

$verb_handlers{"new-metadata"} = $verb_handlers{"n"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, 1, "FILE#")
		or return;
	setNewMetadata($pimp, $params[0]);
};

$verb_handlers{"misidentified"} = $verb_handlers{"m"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, 1, "FILE#")
		or return;
	$pimp->misidentified($params[0]);
};

$verb_handlers{"identify-again"} = $verb_handlers{"i"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, 1, "FILE#")
		or return;
	$pimp->identifyAgain($params[0]);
};

$verb_handlers{"print"} = $verb_handlers{"p"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, 1, "FILE#")
		or return;
	printTrack($pimp, $params[0]);
};

$verb_handlers{"results"} = $verb_handlers{"r"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, 1, "FILE#")
		or return;
	printResults($pimp, $params[0]);
};

$verb_handlers{"toggle-va"} = $verb_handlers{"v"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, 1, "FILE#")
		or return;
	toggleVA($pimp, $params[0]);
};

$verb_handlers{"write-tags"} = $verb_handlers{"w"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 1, "[FILE#]")
		or return;
	$pimp->writeTags($params[0]) if defined $params[0];
	# FIXME I don't think this works if some of the tracks aren't in an
	# appropriate state
	$pimp->writeTags($pimp->getFileIds) if not defined $params[0];
};

$verb_handlers{"remove"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, INFINITE, "[FILE# ...]")
		or return;
	$pimp->remove($_) for @params;
};

$verb_handlers{"remove-all"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 0)
		or return;
	$pimp->remove($_) for $pimp->getFileIds;
};

$verb_handlers{"choose-result"} = $verb_handlers{"c"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 2, 2, "FILE# CHOICE")
		or return;
	selectTrack($pimp, @params);
};

$verb_handlers{"submit-trms"} = $verb_handlers{"s"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 0)
		or return;
	if ($pimp->submitTRMs == tpOk)
	{
		printf("Submitted ok.\n");
	} else {
		printf("Submit error: %s\n", $pimp->getError);
	}
};

# toggles

$verb_handlers{"debug"} = $verb_handlers{"b"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 0)
		or return;
	$pimp->setDebug(not $pimp->getDebug);
	printf("Debug is now %s\n", $pimp->getDebug ? "on" : "off");
};
$verb_handlers{"set-move-files"} = $verb_handlers{"o"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 0)
		or return;
	$pimp->setMoveFiles(not $pimp->getMoveFiles);
	printf("MoveFiles is now %s\n", $pimp->getMoveFiles ? "on" : "off");
};

$verb_handlers{"set-rename-files"} = $verb_handlers{"e"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 0)
		or return;
	$pimp->setRenameFiles(not $pimp->getRenameFiles);
	printf("RenameFiles is now %s\n", $pimp->getRenameFiles ? "on" : "off");
};

$verb_handlers{"set-clear-tags"} = $verb_handlers{"x"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 0)
		or return;
	$pimp->setClearTags(not $pimp->getClearTags);
	printf("ClearTags is now %s\n", $pimp->getClearTags ? "on" : "off");
};

# filemasks

$verb_handlers{"set-filemask"} = $verb_handlers{"f"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, INFINITE, "FILEMASK")
		or return;
	my $mask = $context->{'last_params'};
	validate_file_mask($mask);
	$pimp->setFileMask($mask);
	printf("FileMask is now %s\n", $pimp->getFileMask);
};

$verb_handlers{"set-va-filemask"} = $verb_handlers{"fv"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, INFINITE, "FILEMASK")
		or return;
	my $mask = $context->{'last_params'};
	validate_file_mask($mask);
	$pimp->setVariousFileMask($mask);
	printf("VariousFileMask is now %s\n", $pimp->getVariousFileMask);
};

$verb_handlers{"set-na-filemask"} = $verb_handlers{"fn"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, INFINITE, "FILEMASK")
		or return;
	my $mask = $context->{'last_params'};
	validate_file_mask($mask);
	$pimp->setNonAlbumFileMask($mask);
	printf("NonAlbumFileMask is now %s\n", $pimp->getNonAlbumFileMask);
};

# numberic options

$verb_handlers{"set-trm-collision-threshold"} = $verb_handlers{"tc"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, 1, "THRESHOLD (0-100)")
		or return;
	$pimp->setTRMCollisionThreshold($params[0]);
	printf("TRMCollisionThreshold is now %d\n", $pimp->getTRMCollisionThreshold);
};

$verb_handlers{"set-auto-save-threshold"} = $verb_handlers{"ta"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, 1, "THRESHOLD (0-100)")
		or return;
	$pimp->setAutoSaveThreshold($params[0]);
	printf("AutoSaveThreshold is now %d\n", $pimp->getAutoSaveThreshold);
};

# other options

$verb_handlers{"set-dest-dir"} = $verb_handlers{"t"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, INFINITE, "DIR")
		or return;
	$pimp->setDestDir($context->{'last_params'});
	printf("DestDir is now %d\n", $pimp->getDestDir);
};

$verb_handlers{"set-user-info"} = $verb_handlers{"ui"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 2, 2, "USER PASSWD")
		or return;
	$pimp->setUserInfo(@params[0,1]);
	printf("UserInfo is now '%s' '%s'\n", $pimp->userInfo);
};

$verb_handlers{"set-server"} = $verb_handlers{"u"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 1, 2, "HOST [PORT]")
		or return;
	@params = split(/:/, $params[0], 2) if @params == 1;
	$params[1] = 80 if not defined $params[1];
	$pimp->setServer(@params[0,1]);
	printf("Server is now %s\n", scalar $pimp->getServer);
};

$verb_handlers{"set-proxy"} = sub {
	my ($pimp, $context, @params) = check_args(\@_, 0, 2, "HOST [PORT]")
		or return;
	if (@params==0)
	{
		@params = ("", 0);
	} elsif (@params == 1) {
		@params = split(/:/, $params[0], 2);
		$params[1] = 80 if not defined $params[1];
	}
	$pimp->setProxy(@params[0,1]);
	printf("Proxy is now %s\n", scalar($pimp->getProxy) || "<none>");
};

################################################################################
# Help
################################################################################

sub showHelp
{
	my $pimp = shift;

	printf <<EOF,

Help:
Command:  Arguments:        Function:
---------------------------------------------------------
   a      <filename>        Add file
   glob   <mask>            Add files (wildcard)
   d      <dir>             Add files in dir
   l                        List files in tagger
   p      <file #>          Print details of file
   r      <file #>          Show the matches for a file lookup
   q                        Quit
   w      [file #s]         Write tags & rename files
   remove <file #s>         Remove files from list
   remove-all               Remove all files from list
   c      <file #> <choice> Choose a search result
   s                        Submit TRMs to server
   i      <file #>          Identify file again
   m      <file #>          File was misidentified
   n      <file #>          Provide new metadata for file
   v      <file #>          Toggle Various Artist flag for file

Options:
---------------------------------------------------------
   e                        Toggle file rename (%s)
   o                        Toggle file move (%s)
   t      <output dir>      Set output dir (%s)
   u      <server name>     Use MB server (%s)
   set-proxy <server name>  Use proxy (%s)
   ui     <name> <passwd>   Set MB user name/passwd (%s, %s)
   tc     <#>               Set TRM collision threshold (%d)
   ta     <#>               Set auto save threshold (%d)
   x                        Clear tags before writing new ones (%s)
   f      <mask>            Set the filemask (%s)
   fv     <va mask>         Set the various artist filemask (%s)
   fn     <na mask>         Set the non-album filemask (%s)
   hv                       Show valid substitutions for use in filemasks
   save-config [FILE]       Save current configuration to FILE (default ~/.tunepimprc)
   load-config [FILE]       Load configuration from FILE (default ~/.tunepimprc)
   shell  [command]         Spawn a shell or run a command

EOF
		$pimp->renameFiles ? "on" : "off",
		$pimp->moveFiles ? "on" : "off",
		$pimp->destDir,
		scalar($pimp->getServer),
		scalar($pimp->getProxy),
		$pimp->userInfo,
		$pimp->TRMCollisionThreshold,
		$pimp->autoSaveThreshold,
		$pimp->clearTags ? "on" : "off",
		$pimp->fileMask,
		$pimp->variousFileMask,
		$pimp->nonAlbumFileMask,
		;
		
	print "The complete set of commands I understand is: ";
	print map { " $_" } sort keys %verb_handlers;
	print "\n\n";

	print "Valid filemask substitutions are:";
	print " $_" for sort keys %known_replacement_sequences;
	print "\n\n";
}

################################################################################
# main
################################################################################

sub main
{
	my $version = CVS_REVISION;
    my $pimp = MusicBrainz::Tunepimp::tunepimp->new("tp_tagger.pl", $version);
	print "tp_tagger.pl version " . $version . "\n";
	print "libtunepimp version " . $pimp->getVersion . "\n";
    $pimp->setUseUTF8(1);

	# Set some default values

    $pimp->setDestDir("$ENV{HOME}/music");
    $pimp->setRenameFiles(1);
    $pimp->setMoveFiles(1);
    $pimp->setTopSrcDir(".");
    $pimp->setClearTags(0);
    $pimp->setFileMask("%sortname/%album/%sortname-%album-%0num-%track");
    $pimp->setVariousFileMask("Various Artists/%album/%album-%0num-%sortname-%track");
    $pimp->setNonAlbumFileMask("%sortname/%album/%sortname--%track");
    $pimp->setAutoSaveThreshold(-1);
    $pimp->setTRMCollisionThreshold(80);
	$pimp->setUserInfo("", "");
	$pimp->setAllowedFileCharacters("");
	$pimp->setServer("www.musicbrainz.org", 80);
	$pimp->setProxy("", 0);

	# Now load the default config file
	load_config($pimp, undef, quiet => 1);

    printf("Supported file extensions:");
        printf(" %s", $_) for $pimp->getSupportedExtensions;

    printf("\n\nEnter ? or h for help\n\n");

    # Not used right now -- we'll use the polling version
    # $pimp->setNotifyCallback(\&notify);

       $pimp->addFiles(@ARGV);

	# Other information needed to control us
	my %context = (
		quit => 0,
	);

    while (not $context{quit})
    {
		$last_notify = "";
		while (my ($type, $fileId, $status) = $pimp->getNotification)
		{
            notify($pimp, undef, $type, $fileId, $status);
		}

        my $cmd = getCommand();
        $cmd =~ /\S/ or next;

		my ($verb, $last_params) = $cmd =~ /^(\S+)\s*(.*)?$/;
		my @params = split ' ', $last_params;

		my @verbs = grep /^\Q$verb\E/, keys %verb_handlers;
		@verbs = ($verb) if $verb_handlers{$verb};

		if (not @verbs)
		{
			print "Unknown command '$verb'.  Try 'help'.\n";
			next;
		}

		if (@verbs > 1)
		{
			print "Ambiguous command '$verb'.  Matching commands:";
			print " $_" for sort @verbs;
			print "\n";
			next;
		}

		$verb = $verbs[0];
		$context{last_command} = $cmd;
		$context{last_params} = $last_params;
		$context{verb} = $verb;
		$context{params} = \@params;

		my $handler = $verb_handlers{$verb}
			or die "No handler for '$verb'";
		&$handler($pimp, \%context, @params);
    }
}

exit main();

# eof tp_tagger.pl
